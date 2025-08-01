import numpy as np
import pandas as pd
import sys, os, django

sys.path.append("/Users/chris/DeepGreen/workspaces/tamarack/clf-healthscore/automator")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "automator.settings")
django.setup()

from healthscore.models import Latch, LifeExpectancy, State, Community, MetricValence, SmartLocation, BRFSS,\
    EducationMA, EducationCT, EducationRI, EducationMASubgroup, EducationCTSubgroup, DataSource, Dataset,\
    SchoolDistrict, NMTC, OpportunityZone, NHTS

# Create new data sources
records = [
    DataSource(name="LATCH", reference_url='https://www.bts.gov/latch/latch-data'),
    DataSource(name="USALEEP", reference_url='https://www.cdc.gov/nchs/nvss/usaleep/usaleep.html'),
    DataSource(name="SmartLocation", reference_url='https://www.epa.gov/sites/default/files/2021-06/documents/epa_sld_3.0_technicaldocumentationuserguide_may2021.pdf'),
    DataSource(name="BRFSS", reference_url='https://data.cdc.gov/Behavioral-Risk-Factors/Behavioral-Risk-Factor-Surveillance-System-BRFSS-P/dttw-5yxu'),
    DataSource(name="NMTC", reference_url='https://www.novoco.com/resource-centers/new-markets-tax-credits/data-tools/data-tables'),
    DataSource(name="Education MA", reference_url='https://www.doe.mass.edu/accountability/lists-tools/default.html'),
    DataSource(name="Education CT", reference_url='https://public-edsight.ct.gov/?language=en_US'),
    DataSource(name="Education RI", reference_url=''),
    DataSource(name="Education MA Subgroup", reference_url='https://www.doe.mass.edu/accountability/lists-tools/default.html'),
    DataSource(name="Education CT Subgroup", reference_url='https://public-edsight.ct.gov/performance/performance-index?language=en_US'),
    DataSource(name="School District", reference_url='https://nces.ed.gov/programs/edge/Geographic/RelationshipFiles'),
    DataSource(name="OpportunityZone", reference_url='https://hudgis-hud.opendata.arcgis.com/datasets/ef143299845841f8abb95969c01f88b5/explore'),
    DataSource(name="NHTS", reference_url='https://www.bts.gov/statistical-products/surveys/vehicle-miles-traveled-and-vehicle-trips-state')
]
DataSource.objects.bulk_create(records)

acs_detail = DataSource.objects.filter(name='ACS Detail').first()
acs_detail.reference_url = 'https://api.census.gov/data/{year}/acs/acs5'
acs_detail.save()

acs_subject = DataSource.objects.filter(name='ACS Subject').first()
acs_subject.reference_url = 'https://api.census.gov/data/{year}/acs/acs5/subject'
acs_subject.save()

acs_profile = DataSource.objects.filter(name='ACS Profile').first()
acs_profile.reference_url = 'https://api.census.gov/data/{year}/acs/acs5/profile'
acs_profile.save()

cdc_places = DataSource.objects.filter(name='CDC Places').first()
cdc_places.reference_url = 'https://dev.socrata.com/foundry/data.cdc.gov/nw2y-v4gm'
cdc_places.save()

ej_screen = DataSource.objects.filter(name='EJ Screen').first()
ej_screen.reference_url = 'https://www.epa.gov/ejscreen/ejscreen-change-log'
ej_screen.save()

# Update dataset descriptors for existing data sources
acs_detail_ds = Dataset.objects.filter(data_source__name__exact='ACS Detail').first()
acs_detail_ds.descriptor = 'ACS 5 year detail estimates. Data is from the entire 5 year span, and the vintage represents the final year in the span.'
acs_detail_ds.save()

acs_subject_ds = Dataset.objects.filter(data_source__name__exact='ACS Subject').first()
acs_subject_ds.descriptor = 'ACS 5 year subject estimates. Data is from the entire 5 year span, and the vintage represents the final year in the span.'
acs_subject_ds.save()

acs_profile_ds = Dataset.objects.filter(data_source__name__exact='ACS Profile').first()
acs_profile_ds.descriptor = 'ACS 5 year profile estimates. Data is from the entire 5 year span, and the vintage represents the final year in the span.'
acs_profile_ds.save()

cdc_places_ds = Dataset.objects.filter(data_source__name__exact='CDC Places').first()
cdc_places_ds.descriptor = 'CDC Places data for the year specified by the vintage.'
cdc_places_ds.save()

ej_screen_ds = Dataset.objects.filter(data_source__name__exact='EJ Screen').first()
ej_screen_ds.descriptor = 'EJ Screen environmental data from 2019. '
ej_screen_ds.save()

# Create datasets for remaining data sources
latch = DataSource.objects.filter(name__exact='LATCH').first()
ds = Dataset.objects.create(data_source=latch, vintage='Nov 23, 2018',
                       descriptor='Data collected in 2017.')
Latch.objects.all().update(dataset=ds)

usaleep = DataSource.objects.filter(name__exact='USALEEP').first()
ds = Dataset.objects.create(data_source=usaleep, vintage='2018',
                       descriptor='Life expectancy data collected from 2010-2015.')
LifeExpectancy.objects.all().update(dataset=ds)

smartlocation = DataSource.objects.filter(name__exact='SmartLocation').first()
ds = Dataset.objects.create(data_source=smartlocation, vintage='Jun, 2021',
                       descriptor='A mixture of data sources. We use one variable, from the 2020 GTFS.')
SmartLocation.objects.all().update(dataset=ds)

brfss = DataSource.objects.filter(name__exact='BRFSS').first()
ds = Dataset.objects.create(data_source=brfss, vintage='2021',
                       descriptor='Continuously updated, data is from 2011-present.')
BRFSS.objects.all().update(dataset=ds)

nmtc = DataSource.objects.filter(name__exact='NMTC').first()
ds = Dataset.objects.create(data_source=nmtc, vintage='Nov 02, 2017',
                       descriptor='Data from 2011-2015 ACS.')
NMTC.objects.all().update(dataset=ds)

ma_school = DataSource.objects.filter(name__exact='Education MA').first()
ds = Dataset.objects.create(data_source=ma_school, vintage='Jan 09, 2020',
                       descriptor='School accountability data from 2019.')
EducationMA.objects.all().update(dataset=ds)

ma_school_subgroup = DataSource.objects.filter(name__exact='Education MA Subgroup').first()
ds = Dataset.objects.create(data_source=ma_school_subgroup, vintage='Oct 15, 2019',
                       descriptor='School accountability subgroup data from 2019.')
EducationMASubgroup.objects.all().update(dataset=ds)

ct_school = DataSource.objects.filter(name__exact='Education CT').first()
ds = Dataset.objects.create(data_source=ct_school, vintage='unknown',
                       descriptor='School accountability subgroup data from 2019.')
EducationCT.objects.all().update(dataset=ds)

ct_school_subgroup = DataSource.objects.filter(name__exact='Education CT Subgroup').first()
ds = Dataset.objects.create(data_source=ct_school_subgroup, vintage='unknown',
                       descriptor='Performance indices for the 2018-2019 school year.')
EducationCTSubgroup.objects.all().update(dataset=ds)

ri_school = DataSource.objects.filter(name__exact='Education RI').first()
ds = Dataset.objects.create(data_source=ri_school, vintage='unknown',
                       descriptor='School accountability data.')
EducationRI.objects.all().update(dataset=ds)

schooldistrict = DataSource.objects.filter(name__exact='School District').first()
ds = Dataset.objects.create(data_source=schooldistrict, vintage='2022',
                       descriptor='TIGER 2022 dataset, representing the 2021-2022 school year.')
SchoolDistrict.objects.all().update(dataset=ds)

opportunityzones = DataSource.objects.filter(name__exact='OpportunityZone').first()
ds = Dataset.objects.create(data_source=opportunityzones, vintage='July 31, 2023',
                       descriptor='Data date of coverage is through Dec 2019.')
OpportunityZone.objects.all().update(dataset=ds)

# Import NHTS data
nhts = DataSource.objects.filter(name__exact='NHTS').first()
ds = Dataset.objects.create(data_source=nhts, vintage='May 31, 2017',
                            descriptor='Data collected in 2009. This is LATCH data, but as a state level summary.')


# Note: the csv file we are importing here was constructed from the original state level .xlsx file.
df = pd.read_csv('../../external_data/nhts.csv')
df = df.replace(np.nan, None)
row_iter = df.iterrows()

records = [
    NHTS(
        fips_id=row['state_fips'] if len(row['state_fips']) == 2 else '0' . row['state_fips'],
        est_vmiles_urban=row['vest_miles_urban'],
        est_vmiles_suburban=row['vest_miles_suburban'],
        est_vmiles_rural=row['vest_miles_rural'],
        dataset=ds
    )
    for index, row in row_iter
]

NHTS.objects.bulk_create(records)

# Import new NMTC data
nmtc = DataSource.objects.filter(name__exact='NMTC').first()
ds = Dataset.objects.create(data_source=nmtc, vintage='Sep 01, 2023',
                       descriptor='Data from 2016-2020 ACS.')

df = pd.read_excel('../../external_data/NMTC_2016-2020_ACS_LIC_Sept1_2023.xlsx', sheet_name='2016-2020',
                   dtype='str')
df = df.replace(np.nan, None)
row_iter = df.iterrows()

records = [
    NMTC(
        dataset=ds,
        vintage='Sep 01, 2023',
        tract_id=row['2020 Census Tract Number FIPS code. GEOID'],
        eligible=row['Does Census Tract Qualify For NMTC Low-Income Community (LIC) on Poverty or Income Criteria?'] == 'Yes'
                 or row['Does Census Tract Qualify on Poverty Criteria>=20%?'] == 'Yes'
                 or row['Does Census Tract Qualify on Median Family Income Criteria<=80%?'] == 'Yes'
    )
    for index, row in row_iter
]

NMTC.objects.bulk_create(records)

