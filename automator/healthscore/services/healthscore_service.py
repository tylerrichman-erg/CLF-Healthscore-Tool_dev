import logging
from datetime import datetime

from django.db import transaction
from healthscore.models import Healthscore, State, Community, CensusTract, HousingUnitType
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist


class HealthscoreService:
    """
    This class provides methods to save and retrieve healthscore objects, which represent the collection of input
    and parameter values needed to run the healthscore algorithm and produce a spreadsheet summary or other output.
    """
    def __init__(self, user):
        self.user = user
        self.log = logging.getLogger('requested')

    def get_healthscore(self, id):
        return Healthscore.objects.prefetch_related('all_tracts').get(pk=id)

    @transaction.atomic
    def create_healthscore(self, user: User, title: str, address: str, state_fips: str, state_name: str,
                           state_short_code: str, county_fips: str, county_name: str, block_group: str,
                           primary_tract: str, all_tracts: list, school_district: str, community: str,
                           housing_data: list, buffer_radius: int, population_threshold: float, scenario: str):

        # Find the state
        try:
            state, created = State.objects.get_or_create(name=state_name, fips_code=state_fips, short_code=state_short_code)
        except ObjectDoesNotExist:
            self.log.error("Couldn't find state with abbreviation " + state.short_code)
            return None

        # Find the community
        try:
            comm = Community.objects.get(name=community)
        except ObjectDoesNotExist:
            self.log.error("Couldn't find community with name " + community)
            return None

        primary, created = CensusTract.objects.get_or_create(geoid=state_fips+county_fips+primary_tract)

        # Get a list of tract objects corresponding to the given geoids
        tract_list = []
        for t in all_tracts:
            tract, created = CensusTract.objects.get_or_create(geoid=state_fips+county_fips+t)
            tract_list.append(tract)

        new_healthscore = Healthscore.objects.create(user=user, title=title, address=address, state=state,
                                                     county_code=county_fips, county_name=county_name,
                                                     block_group=block_group,
                                                     school_district=school_district, primary_tract=primary,
                                                     community=comm, buffer_radius=buffer_radius,
                                                     population_threshold=population_threshold, scenario=scenario)

        new_healthscore.all_tracts.set(tract_list)

        # If there is housing data, create that too...
        if housing_data is not None and len(housing_data) > 0 and housing_data[0]['unit_type'] != '':
            for housing in housing_data:
                if housing['unit_type'] != '' and housing['unit_count'] != '' and housing['rent'] != '':
                    HousingUnitType.objects.create(healthscore=new_healthscore, unit_type=housing['unit_type'],
                                                   unit_count=housing['unit_count'], starting_rent=housing['rent'])

        return new_healthscore

    @transaction.atomic
    def update_healthscore(self, id: int, user: User, title: str, address: str, state_fips: str, state_name: str,
                           state_short_code: str, county_fips: str, county_name: str, block_group: str,
                           primary_tract: str, all_tracts: list, school_district: str, community: str,
                           housing_data: list, buffer_radius: int, population_threshold: float, scenario: str):

        # Find the state
        try:
            state, created = State.objects.get_or_create(name=state_name, fips_code=state_fips, short_code=state_short_code)
        except ObjectDoesNotExist:
            self.log.error("Couldn't find state with abbreviation " + state.short_code)
            return None

        # Find the community
        try:
            comm = Community.objects.get(name=community)
        except ObjectDoesNotExist:
            self.log.error("Couldn't find community with name " + community)
            return None

        primary, created = CensusTract.objects.get_or_create(geoid=state_fips+county_fips+primary_tract)

        # Get a list of tract objects corresponding to the given geoids
        tract_list = []
        for t in all_tracts:
            tract, created = CensusTract.objects.get_or_create(geoid=state_fips+county_fips+t)
            tract_list.append(tract)

        # Update the existing healthscore object
        Healthscore.objects.filter(pk=id).update(title=title, address=address, state=state, date_created=datetime.now(),
                                                     county_code=county_fips, county_name=county_name,
                                                     block_group=block_group,
                                                     school_district=school_district, primary_tract=primary,
                                                     community=comm, buffer_radius=buffer_radius,
                                                     population_threshold=population_threshold, scenario=scenario)

        existing = Healthscore.objects.get(pk=id)
        existing.all_tracts.set(tract_list)

        # If there is housing data, create that too...but first, delete anything that already exists.
        HousingUnitType.objects.filter(healthscore=existing).delete()

        if housing_data is not None and len(housing_data) > 0 and housing_data[0]['unit_type'] != '':
            for housing in housing_data:
                HousingUnitType.objects.create(healthscore=existing, unit_type=housing['unit_type'],
                                               unit_count=housing['unit_count'], starting_rent=housing['rent'])

        return existing

    @transaction.atomic
    def update_healthscore_title(self, id: int, title: str):

        # Update the existing healthscore object
        Healthscore.objects.filter(pk=id).update(title=title, date_created=datetime.now())
        existing = Healthscore.objects.get(pk=id)

        return existing

    @transaction.atomic
    def delete_healthscore(self, id: int):
        Healthscore.objects.filter(id=id).delete()

    def get_my_healthscores(self):
        return list(Healthscore.objects.prefetch_related('all_tracts').filter(user=self.user).order_by('title'))
