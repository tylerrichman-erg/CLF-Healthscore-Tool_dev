import sys, os, django
import numpy as np
import pandas as pd

sys.path.append("/Users/chris/DeepGreen/workspaces/tamarack/clf-healthscore/automator")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "automator.settings")
django.setup()

from healthscore.models import DataSource, Dataset, ChildMortality, NHTS, PersonalHealthCare, Metric, State, ChildHealth


# Map of state names and abbrev to FIPS code
state_codes = {
    'WA': '53', 'DE': '10', 'DC': '11', 'WI': '55', 'WV': '54', 'HI': '15',
    'FL': '12', 'WY': '56', 'PR': '72', 'NJ': '34', 'NM': '35', 'TX': '48',
    'LA': '22', 'NC': '37', 'ND': '38', 'NE': '31', 'TN': '47', 'NY': '36',
    'PA': '42', 'AK': '02', 'NV': '32', 'NH': '33', 'VA': '51', 'CO': '08',
    'CA': '06', 'AL': '01', 'AR': '05', 'VT': '50', 'IL': '17', 'GA': '13',
    'IN': '18', 'IA': '19', 'MA': '25', 'AZ': '04', 'ID': '16', 'CT': '09',
    'ME': '23', 'MD': '24', 'OK': '40', 'OH': '39', 'UT': '49', 'MO': '29',
    'MN': '27', 'MI': '26', 'RI': '44', 'KS': '20', 'MT': '30', 'MS': '28',
    'SC': '45', 'KY': '21', 'OR': '41', 'SD': '46'
}
us_state_to_abbrev = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
    "District of Columbia": "DC",
    "American Samoa": "AS",
    "Guam": "GU",
    "Northern Mariana Islands": "MP",
    "Puerto Rico": "PR",
    "United States Minor Outlying Islands": "UM",
    "U.S. Virgin Islands": "VI"}

# Create data source for personal health care
records = [
    DataSource(name="NSCH", reference_url='https://www.childhealthdata.org/browse/')
]
DataSource.objects.bulk_create(records)

# Create dataset
nsch = DataSource.objects.filter(name__exact='NSCH').first()
ds = Dataset.objects.create(data_source=nsch, vintage='2022',
                            descriptor='National Survey of Children\'s Health, data is 2016 - present.')


df = pd.read_csv('../../external_data/nsch.csv', dtype={'state_fips': 'str'})
df = df.replace(np.nan, None)
row_iter = df.iterrows()

records = [
    ChildHealth(
        state_fips=row['state_fips'],
        obesity_value=row['obese'],
        obesity_moe=(row['obese_ci_high'] - row['obese_ci_low']) / 2,
        asthma_value=row['asthma'],
        asthma_moe=(row['asthma_ci_high'] - row['asthma_ci_low']) / 2,
        dataset=ds
    )
    for index, row in row_iter
]

ChildHealth.objects.bulk_create(records)


# Back load all states median household income so that we can create quintiles for select NEF metrics.
# This means back loading the actual state entities too.

acs_detail_source = DataSource.objects.filter(name__exact='ACS Detail').first()
ds = Dataset.objects.filter(data_source=acs_detail_source, vintage='2021').first()

df = pd.read_csv('../../external_data/all-states-median-household-income-2021.csv', dtype={'state': 'str'})
df = df.replace(np.nan, None)
row_iter = df.iterrows()

for name, abbrev in us_state_to_abbrev.items():

    if abbrev in state_codes:
        fips = state_codes[abbrev]

        if len(df.loc[df['state'] == fips]) > 0:

            if State.objects.filter(fips_code=fips).exists():
                this_state = State.objects.filter(fips_code=fips).first()
            else:
                this_state = State.objects.create(name=name, short_code=abbrev, fips_code=fips)

            if not Metric.objects.filter(dataset=ds,
                                         name__exact='Median Household Income',
                                         geoid__exact=fips).exists():

                Metric.objects.create(name='Median Household Income',
                                      geoid=fips,
                                      code='B19013_001',
                                      value=df.loc[df['state'] == fips].iloc[0].income,
                                      moe=df.loc[df['state'] == fips].iloc[0].moe,
                                      state=this_state,
                                      dataset=ds)


# Create data source for personal health care
records = [
    DataSource(name="CMS", reference_url='https://www.cms.gov/data-research/statistics-trends-and-reports/national-health-expenditure-data/state-residence')
]
DataSource.objects.bulk_create(records)

# Create dataset
personalhc = DataSource.objects.filter(name__exact='CMS').first()
ds = Dataset.objects.create(data_source=personalhc, vintage='2022',
                            descriptor='2020 personal health care cost data in dollars, by state.')

df = pd.read_csv('../../external_data/cms_per_capita_health_costs.csv')
df = df.replace(np.nan, None)
row_iter = df.iterrows()

records = [
    PersonalHealthCare(
        state_fips=None if row['Group'] == 'United States' else state_codes[us_state_to_abbrev[row['State_Name']]],
        value=row['Y2020'],
        dataset=ds
    )
    for index, row in row_iter
    if (row['State_Name'] is not None or row['Group'] == 'United States') and row['Item'] == 'Personal Health Care ($)'
]

PersonalHealthCare.objects.bulk_create(records)

# Create data source for child mortality data
# records = [
#     DataSource(name="County Health Rankings", reference_url='https://www.countyhealthrankings.org/explore-health-rankings/rankings-data-documentation')
# ]
# DataSource.objects.bulk_create(records)
#
# # Create dataset
# childmortality = DataSource.objects.filter(name__exact='County Health Rankings').first()
# ds = Dataset.objects.create(data_source=childmortality, vintage='2023',
#                             descriptor='2023 child mortality data by county and state.')

# Note: the csv file we are importing here was constructed from the original, much larger analytics file
# that is downloadable from the referenced web page
# df = pd.read_csv('../../external_data/child_mortality.csv', dtype={'State FIPS Code': 'str',
#                                                                    'County FIPS Code': 'str',
#                                                                    '5-digit FIPS Code': 'str'})
# df = df.replace(np.nan, None)
# row_iter = df.iterrows()
#
# records = [
#     ChildMortality(
#         state_fips=None if row['State FIPS Code'] == '0' else
#             row['State FIPS Code'] if len(row['State FIPS Code']) == 2 else '0' + row['State FIPS Code'],
#         county_fips=None if row['County FIPS Code'] == '0' else
#             row['5-digit FIPS Code'] if len(row['5-digit FIPS Code']) == 5 else '0' + row['5-digit FIPS Code'],
#         value=row['raw_value'],
#         moe=None if row['CI_high'] is None or row['CI_low'] is None else (row['CI_high'] - row['CI_low']) / 2,
#         dataset=ds
#     )
#     for index, row in row_iter
# ]
#
# ChildMortality.objects.bulk_create(records)

# df = pd.read_stata('../../external_data/nsch_2022e_topical.dta')
# df = df.replace(np.nan, None)
# row_iter = df.iterrows()
#
# records = [
#     NHTS(
#         fips_id=row['state_fips'] if len(row['state_fips']) == 2 else '0' . row['state_fips'],
#         est_vmiles_urban=row['vest_miles_urban'],
#         est_vmiles_suburban=row['vest_miles_suburban'],
#         est_vmiles_rural=row['vest_miles_rural'],
#         dataset=ds
#     )
#     for index, row in row_iter
# ]

# nhts = DataSource.objects.filter(name__exact='NHTS').first()
# ds = Dataset.objects.filter(data_source=nhts).update(descriptor='State level summary data collected in 2009. NOTE: Using mismatched 2009 data because 2017 is not available.')

