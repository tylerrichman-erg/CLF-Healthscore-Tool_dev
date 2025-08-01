import numpy as np
import pandas as pd
import sys, os, django

#sys.path.append("/Users/trichman/Tyler/Tools/Development/CLF Health Score Tool/Github/CLF-Healthscore-Tool_dev/automator")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "automator.settings")
django.setup()

from healthscore.models import Latch, LifeExpectancy, State, Community, MetricValence, SmartLocation, BRFSS,\
    EducationMA, EducationCT, EducationRI, EducationMASubgroup, EducationCTSubgroup, DataSource, Dataset,\
    SchoolDistrict, NMTC, OpportunityZone, NHTS

# Create data source data
# records = [
#     DataSource(name="LATCH", reference_url='https://www.bts.gov/latch/latch-data'),
#     DataSource(name="USALEEP", reference_url='https://www.cdc.gov/nchs/nvss/usaleep/usaleep.html'),
#     DataSource(name="SmartLocation", reference_url='https://www.epa.gov/sites/default/files/2021-06/documents/epa_sld_3.0_technicaldocumentationuserguide_may2021.pdf'),
#     DataSource(name="BRFSS", reference_url='https://data.cdc.gov/Behavioral-Risk-Factors/Behavioral-Risk-Factor-Surveillance-System-BRFSS-P/dttw-5yxu'),
#     DataSource(name="NMTC", reference_url='https://www.novoco.com/resource-centers/new-markets-tax-credits/data-tools/data-tables'),
#     DataSource(name="Education MA", reference_url='https://www.doe.mass.edu/accountability/lists-tools/default.html'),
#     DataSource(name="Education CT", reference_url='https://public-edsight.ct.gov/?language=en_US'),
#     DataSource(name="Education RI", reference_url=''),
#     DataSource(name="Education MA Subgroup", reference_url='https://www.doe.mass.edu/accountability/lists-tools/default.html'),
#     DataSource(name="Education CT Subgroup", reference_url='https://public-edsight.ct.gov/performance/performance-index?language=en_US'),
#     DataSource(name="School District", reference_url='https://nces.ed.gov/programs/edge/Geographic/RelationshipFiles'),
#     DataSource(name="OpportunityZone", reference_url='https://hudgis-hud.opendata.arcgis.com/datasets/ef143299845841f8abb95969c01f88b5/explore'),
#     DataSource(name="NHTS", reference_url='https://www.bts.gov/statistical-products/surveys/vehicle-miles-traveled-and-vehicle-trips-state')
# ]
# DataSource.objects.bulk_create(records)

# Create community data
# records = [
#     Community(name="Advantaged"),
#     Community(name="Disadvantaged")
# ]
# Community.objects.bulk_create(records)

# Create state data
# records = [
#     State(name="Massachusetts", fips_code="25", short_code="MA"),
#     State(name="Connecticut", fips_code="09", short_code="CT"),
#     State(name="Rhode Island", fips_code="44", short_code="RI")
# ]
# State.objects.bulk_create(records)

# Import metric valence data
# df = pd.read_csv('../../external_data/metric_valence.csv')
# df = df.replace(np.nan, None)
# row_iter = df.iterrows()
#
# records = [
#     MetricValence(
#         community_id = row['community_id'],
#         metric = row['metric'],
#         valence = row['valence']
#     )
#     for index, row in row_iter
# ]
# MetricValence.objects.bulk_create(records)

# Import Latch data
# df = pd.read_csv('../../external_data/latch.csv')
# df = df.replace(np.nan, None)
# row_iter = df.iterrows()
#
# records = [
#     Latch(
#         tract_id = row['geocode'] if len(row['geocode']) == 11 else '0' . row['geocode'],
#         urban_group = row['urban_group'],
#         est_vmiles = row['est_vmiles'],
#         hh_cnt = row['hh_cnt']
#     )
#     for index, row in row_iter
# ]
# Latch.objects.bulk_create(records)


# Import Life Expectancy data
# df = pd.read_csv('../../external_data/life_expectancy.csv', dtype={'Tract ID': 'str'})
# df = df.replace(np.nan, None)
# row_iter = df.iterrows()
#
# records = [
#     LifeExpectancy(
#         geoid=row['Tract ID'],
#         value=row['e(0)'],
#         standard_error=row['se(e(0))']
#     )
#     for index, row in row_iter
# ]
#
# LifeExpectancy.objects.bulk_create(records)

# df = pd.read_csv('../../external_data/life_expectancy_state.csv', dtype={'State ID': 'str'})
# df = df.replace(np.nan, None)
# row_iter = df.iterrows()
#
# records = [
#     LifeExpectancy(
#         geoid=row['State ID'],
#         value=row['e(0)'],
#         standard_error=row['se(e(0))']
#     )
#     for index, row in row_iter
# ]
#
# LifeExpectancy.objects.bulk_create(records)

# Import EPA Smart Location transit frequency data
# Note: we are stripping the last character from the GEOID10 field, because it comes in the
# file as a block group code instead of a tract.
# df = pd.read_csv('../../external_data/epa_smart_location.csv', dtype={'GEOID10': 'str'})
# df = df.replace(np.nan, None)
# row_iter = df.iterrows()
#
# records = [
#     SmartLocation(
#         block_group_id = row['GEOID10'],
#         D4c = row['D4c']
#     )
#     for index, row in row_iter
# ]
#
# SmartLocation.objects.bulk_create(records)

# Import BRFSS/NCHS data
# Note: the csv file we are importing here was constructed from the original state level .xlsx files.
# df = pd.read_csv('../../external_data/state_metrics.csv')
# df = df.replace(np.nan, None)
# row_iter = df.iterrows()
#
# records = [
#     BRFSS(
#         state_id = row['state_id'],
#         metric = row['metric'],
#         value = row['value'],
#         moe = row['moe'],
#         vintage=row['2018']
#     )
#     for index, row in row_iter
# ]
#
# BRFSS.objects.bulk_create(records)

# Import NMTC data
# df = pd.read_excel('../../external_data/nmtc_2011-2015_lic_110217.xlsx', sheet_name='NMTC LICs 2011-2015 ACS',
#                    dtype='str')
# df = df.replace(np.nan, None)
# row_iter = df.iterrows()
#
# records = [
#     NMTC(
#         vintage='2015',
#         tract_id=row['2010 Census Tract Number FIPS code. GEOID'],
#         eligible=row['Does Census Tract Qualify For NMTC Low-Income Community (LIC) on Poverty or Income Criteria?'] == 'Yes'
#                  or row['Does Census Tract Qualify on Poverty Criteria>=20%?'] == 'Yes'
#                  or row['Does Census Tract Qualify on Median Family Income Criteria<=80%?'] == 'Yes'
#     )
#     for index, row in row_iter
# ]
#
# NMTC.objects.bulk_create(records)

# Import education data

# df = pd.read_excel('../../external_data/grf22_lea_tract.xlsx', header=0, dtype='str')
# df = df.replace(np.nan, None)
# row_iter = df.iterrows()
#
# records = [
#     SchoolDistrict(
#         vintage='2022',
#         tract_id=row['TRACT'],
#         district_name=row['NAME_LEA22'].removesuffix('School District')
#     )
#     for index, row in row_iter
# ]
#
# SchoolDistrict.objects.bulk_create(records)


# df = edu = pd.read_excel('../../external_data/ma_accountability.xlsx',
#                          sheet_name='Table 3 - Schools', usecols='D,L', header=1)
# df = df.replace(np.nan, None)
# row_iter = df.iterrows()
#
# records = [
#     EducationMA(
#         district = row['District Name'],
#         percentile = row['2019 Accountability Percentile']
#     )
#     for index, row in row_iter
# ]
#
# EducationMA.objects.bulk_create(records)
#
# df = edu = pd.read_excel('../../external_data/ct_accountability.xlsx', header=0)
# df = df.replace(np.nan, None)
# row_iter = df.iterrows()
#
# records = [
#     EducationCT(
#         district=row['RptngDistrictName'].removesuffix(' School District'),
#         percentile=row['OutcomeRatePct']
#     )
#     for index, row in row_iter
# ]
#
# EducationCT.objects.bulk_create(records)
#
# df = edu = pd.read_excel('../../external_data/ri_accountability.xlsx', sheet_name='School Indicator Data', header=None,
#                          skiprows=2, usecols='B,G,AZ', names=['District', 'Group', 'Rating'])
# df = df.replace(np.nan, None)
# row_iter = df.iterrows()
#
# records = [
#     EducationRI(
#         district = row['District'],
#         group = row['Group'],
#         star_rating = row['Rating']
#     )
#     for index, row in row_iter
# ]
#
# EducationRI.objects.bulk_create(records)
#
# df = pd.read_excel('../../external_data/ma_subgroup.xlsx', None)
#
# # There are three sheets to scrape data from
# nonhs = df['NonHS data']
# hs = df['HS data']
# k12 = df['MSHS K-12 data']
# sheets = [nonhs, hs, k12]
#
# for i in sheets:
#
#     this_df = i.replace(np.nan, None)
#     this_df = this_df.iloc[1: , :]
#     row_iter = this_df.iterrows()
#
#     records = [
#         EducationMASubgroup(
#             district = row['District'],
#             school = row['School name'],
#             group = row['Group'],
#             percentile = row[-1]
#         )
#         for index, row in row_iter
#     ]
#
#     EducationMASubgroup.objects.bulk_create(records)
#
# df = pd.read_excel('../../external_data/ct_subgroup.xlsx', header=0)
# df = df.replace(np.nan, None)
# row_iter = df.iterrows()
#
# records = [
#     EducationCTSubgroup(
#         district=row['District Name'].removesuffix(' School District'),
#         subgroup=row['Subgroup'],
#         ela_performance_index=row['ELAPerformanceIndex'],
#         math_performance_index=row['MathPerformanceIndex'],
#         science_performance_index=row['SciencePerformanceIndex']
#     )
#     for index, row in row_iter
# ]
#
# EducationCTSubgroup.objects.bulk_create(records)

# Opportunity Zones...data is a manipulated version of download from here:
# https://hudgis-hud.opendata.arcgis.com/datasets/ef143299845841f8abb95969c01f88b5/explore
# df = pd.read_csv('../../external_data/opportunity_zones.csv', dtype={'GEOID10': 'str'})
# df = df.replace(np.nan, None)
# row_iter = df.iterrows()
#
# records = [
#     OpportunityZone(
#         geoid=row['GEOID10'],
#     )
#     for index, row in row_iter
# ]
#
# OpportunityZone.objects.bulk_create(records)

