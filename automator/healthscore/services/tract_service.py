from censusgeocode import CensusGeocode
import geopandas as gpd
import logging
import requests as requests
import pandas as pd
import numpy as np
from math import ceil
from pygris import blocks, tracts
from pygris.data import get_census
from healthscore.services.data_service import DataService
from healthscore.models import SchoolDistrict, LifeExpectancy, NMTC, OpportunityZone
from django.core.exceptions import ObjectDoesNotExist

class TractService:
    """
    This class has methods that support the tract selection process. Notably, there are methods
    that perform Google geocoding and census block/tract population analysis.
    """
    def __init__(self, user):
        self.api_key = 'AIzaSyBO1ULFdur5Z274bzrn-mN-5K1NO2AP3o0'  # API key fo account CLF.infotech@gmail.com
        self.base_url = 'https://maps.googleapis.com/maps/api/geocode/json'
        self.user = user
        self.log = logging.getLogger('requested')

    def google_geocode(self, address_or_zipcode: str):
        lat, lng = None, None
        endpoint = f"{self.base_url}?address={address_or_zipcode}&key={self.api_key}"

        self.log.info(f'Geocoding address {address_or_zipcode}...', extra={'user': self.user.username})

        r = requests.get(endpoint)
        if r.status_code not in range(200, 299):
            self.log.info(f'Geocoding failed for address {address_or_zipcode} with status code ' + str({r.status_code}),
                          extra={'user': self.user.username})
            return None, None
        try:
            results = r.json()['results'][0]
            lat = results['geometry']['location']['lat']
            lng = results['geometry']['location']['lng']
            self.log.info(f'Lat,lon = {lat}, {lng}', extra={'user': self.user.username})
        except:
            pass
        return lat, lng

    def select_tracts(self, address: str, buffer_size: int, pop_pct_threshold: float):
        """
        :param address: i.e. '123 Main St. Kalamazoo MI 49901'
        :param buffer_size: radius of desired buffer in meters
        :param pop_pct_threshold:  [0 > value <= 1] that describes % of tract population within buffer that will cause
            this algortihm to select the tract
        :return: a list of information corresponding to the geocoded address, selected tracts, and an IFrame HTML
            snippet for the interactive map:

            (iframe, state_fips, county, primary, block_group, unique_tracts)
        """
        # Set some variables that will be used to retrieve census data

        # NOTE: the data that gets used for census block/tract population analysis below is not actually ACS data,
        # but rather PL 94-171 Redistricting data. Nevertheless, we will proceed with the same vintage as is being used
        # for ACS to provide consistency between the two. In this case, pygris wants the year as an int, hence the cast.
        vintages = DataService.vintages()
        year = int(vintages['ACS'])
        pop_var = 'P1_001N'
        geoid_var = 'GEOID20'
        tract_var = 'TRACTCE20'
        block_group_var = 'BLKGRP'

        # Geocode the incoming address to get a lat,lon pair
        lat_lon = self.google_geocode(address)

        lon = lat_lon[1]
        lat = lat_lon[0]

        if lat is None or lon is None:
            # Geocoding failed to find coordinates for the given address
            self.log.info(f'Lat or lon is None, bailing out...', extra={'user': self.user.username})
            return None, None, None, None, None, []

        utm_zone = ceil((lon + 180) / 6)

        # Get some census information about this location (state, county, tract, block, group)
        try:
            cg = CensusGeocode(benchmark='Public_AR_Current', vintage='Census2020_Current')
            result = cg.coordinates(x=lon, y=lat)
        except ValueError as e:
            self.log.error(e)
            return None

        block = result['Census Blocks'][0]['GEOID']
        primary = block[:-4][5:]

        state_short_code = result['States'][0]['STUSAB']
        state_name = result['States'][0]['BASENAME']
        state_fips = result['States'][0]['GEOID']
        block_group = result['Census Blocks'][0][block_group_var]

        # NOTE! This value is tricky for the state of Connecticut, which is currently in a transition
        # away from county FIPS codes to "planning regions" with different values. See
        # https://www.federalregister.gov/documents/2022/06/06/2022-12063/change-to-county-equivalents-in-the-state-of-connecticut
        # Therefore we have an alternate value that can be tried if needed.
        county_fips = block[2:5]
        county_code_alt = result['Counties'][0]['GEOID'][2:5]
        county_name = result['Counties'][0]['BASENAME']

        # Use pygris to get the PL 94-171 redistricting data, which includes total population.
        # Note that vintage is hard-coded to 2020, because that's the most recent that's available.
        blocks_pop_gpd = get_census(dataset="dec/pl",
                                    variables=pop_var, year=2020,
                                    params={"for": "block:*", "in": "state:"+state_fips + "&county:"+county_fips},
                                    guess_dtypes=True, return_geoid=True)

        # Use pygris to get the shape file for all blocks in this state and county
        blocks_gpd = blocks(state=state_fips, county=county_fips, cache=False, year=year, subset_by={address: 4000})
        tracts_gpd = tracts(state=state_fips, county=county_fips, cache=False, year=year)

        # Project to UTM
        ma_blocks = blocks_gpd.to_crs(f"+proj=utm +zone={utm_zone} ellps=WGS84")

        # Merge shapes with census data
        merged_gpd = ma_blocks.merge(blocks_pop_gpd, how="inner", left_on=geoid_var, right_on="GEOID")

        # Use this if we want polygons for the blocks
        # polygons_gpd = gpd.GeoDataFrame.copy(merged_gpd)

        # Convert the blocks to a point which represents their centroid
        merged_gpd['geometry'] = merged_gpd.centroid

        # Construct a circle with a half mile radius (805 meters) and the address at the center
        location = pd.DataFrame([
            {'id': address,
             'longitude': lon,
             'latitude': lat
            }
        ])
        development_gpd = gpd.GeoDataFrame(location, geometry=gpd.points_from_xy(location.longitude, location.latitude),
                                           crs='+proj=longlat + ellps=WGS84 +datum=WGS84')

        buffer_gpd = gpd.GeoDataFrame.copy(development_gpd)
        buffer_gpd.geometry = buffer_gpd.geometry.to_crs(f"+proj=utm +zone={utm_zone} ellps=WGS84")
        buffer_gpd.geometry = buffer_gpd.geometry.buffer(buffer_size)

        # Calculate the tract population for each row
        merged_gpd['TRACT_POP'] = merged_gpd.groupby(tract_var)[pop_var].transform('sum')

        # Merge life expectancy data (tract-level) with blocks
        nearby_tracts = tracts_gpd['GEOID'].values
        expectancies = LifeExpectancy.objects.filter(dataset__vintage=vintages['LifeExpectancy'], geoid__in=nearby_tracts).values()
        state_expectancy = LifeExpectancy.objects.filter(dataset__vintage=vintages['LifeExpectancy'], geoid=state_fips).first()
        from_db_gpd = gpd.GeoDataFrame.from_dict(expectancies)

        if len(from_db_gpd.index) > 0:
            merged_gpd['TRACT_ID'] = merged_gpd['GEOID20'].str[:-4]
            merged_gpd = pd.merge(merged_gpd, from_db_gpd, left_on='TRACT_ID', right_on='geoid', how='left')
            merged_gpd['value'] = merged_gpd['value'].fillna('N/A')
        else:
            # No Life expectancy data
            merged_gpd['value'] = 'N/A'

        merged_gpd['state_le'] = state_expectancy.value

        # Merge NMTC data (tract-level) with blocks
        nmtc = NMTC.objects.filter(dataset__vintage=vintages['NMTC'], tract_id__in=nearby_tracts).values()
        from_db_gpd = gpd.GeoDataFrame.from_dict(nmtc)

        if len(from_db_gpd.index) > 0:
            merged_gpd['TRACT_ID'] = merged_gpd['GEOID20'].str[:-4]
            merged_gpd = pd.merge(merged_gpd, from_db_gpd, left_on='TRACT_ID', right_on='tract_id', how='left')
            merged_gpd['eligible'] = merged_gpd['eligible'].map(lambda x: 'Yes' if x else 'No')
        else:
            # No NMTC data
            merged_gpd['eligible'] = 'N/A'

        # Merge Opportunity Zone data (tract-level) with blocks
        opportunity_zone =\
            OpportunityZone.objects.filter(dataset__vintage=vintages['OpportunityZone'], geoid__in=nearby_tracts).values()
        from_db_gpd = gpd.GeoDataFrame.from_dict(opportunity_zone)

        if len(from_db_gpd.index) > 0:
            merged_gpd['TRACT_ID'] = merged_gpd['GEOID20'].str[:-4]
            merged_gpd = pd.merge(merged_gpd, from_db_gpd, left_on='TRACT_ID', right_on='geoid', how='left', suffixes=('_opportunity', '_merged'))
            merged_gpd['opportunity'] = merged_gpd['geoid_merged'].map(lambda x: 'No' if pd.isnull(x) else 'Yes')
        else:
            # No Opportunity Zones
            merged_gpd['opportunity'] = 'No'

        # Find the rows (and hence blocks) that spatially intersect the buffer we created.
        intersection = gpd.sjoin(buffer_gpd, merged_gpd, how='left')

        # Calculate the population of the intersecting blocks by tract ("overlap pop")
        intersection['OVERLAP_POP'] = intersection.groupby(tract_var)[pop_var].transform('sum')

        # Filter out records where overlap pop < 50% of tract pop.
        intersection = intersection[intersection['OVERLAP_POP'] / intersection['TRACT_POP'] >= pop_pct_threshold]
        intersection.reset_index(inplace=True)
        unique_tracts = intersection[tract_var].unique()

        if primary not in unique_tracts:
            unique_tracts = np.append(unique_tracts, [primary])

        unique_tracts.sort()

        # Add the buffer first to establish a good starting zoom level
        m = buffer_gpd.explore(tiles="https://mt.google.com/vt/lyrs=m,transit,bike&x={x}&y={y}&z={z}", attr="Google Maps",
                               style_kwds={'color': 'orange', 'opacity': 0.7, 'fillColor': 'orange', 'fillOpacity': 0.2},
                               tooltip=False, highlight=False)

        m = development_gpd.explore(m=m, tooltip=False, highlight=False, color='red', marker_type='marker')
        m = tracts_gpd.explore(m=m, tooltip=False,
                               style_kwds={'color': 'blue', 'opacity': 0.3, 'weight': 1, 'fillOpacity': 0.0},
                               highlight_kwds={'color': 'red', 'opacity': 0.7, 'weight': 2, 'fillOpacity': 0.0})
        m = merged_gpd.explore(m=m, tooltip=['TRACTCE20', 'TRACT_POP', 'value', 'state_le', 'eligible', 'opportunity', 'P1_001N'],
                               popup=['TRACTCE20', 'TRACT_POP', 'value', 'state_le', 'eligible', 'opportunity', 'P1_001N'],
                               tooltip_kwds={'aliases': ['Tract', 'Tract pop', 'Life Expectancy', 'State Life Expectancy',
                                                         'New Market Tax Credit Eligible', 'Opportunity Zone', 'Block pop']},
                               popup_kwds={'aliases': ['Tract', 'Tract pop', 'Life Expectancy', 'State Life Expectancy',
                                                       'New Market Tax Credit Eligible', 'Opportunity Zone', 'Block pop']})
        iframe = m._repr_html_()

        return iframe, state_fips, state_name, state_short_code, county_fips, county_code_alt, county_name, primary,\
            block_group, unique_tracts.tolist()

    def get_school_district(self, state_fips: str, county_fips: str, primary: str, vintage: str):
        """
        Return a school district name that corresponds to the given census tract id.

        :param state_fips: i.e. '25'
        :param county_fips: i.e. '009'
        :param primary: i.e. '215102'
        :param vintage: i.e. '2022'
        :return: i.e. 'Hamilton-Wenham'
        """
        try:
            sd = SchoolDistrict.objects.filter(dataset__vintage=vintage, tract_id=state_fips+county_fips+primary).first()
            return '' if sd is None else sd.district_name

        except ObjectDoesNotExist as e:
            return ''

    def miles_to_meters(self, value_in_miles: float):
        conversion_factor = 0.00062137119
        converted = value_in_miles / conversion_factor
        return round(converted)
