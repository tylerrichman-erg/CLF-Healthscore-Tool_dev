import sys, os, django
import numpy as np
import pandas as pd

sys.path.append("/home/healthscore/clf-healthscore/automator")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "automator.settings")
django.setup()

from healthscore.models import DataSource, Dataset, ChildMortality, ERVisits

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

# Create dataset
childmortality = DataSource.objects.filter(name__exact='County Health Rankings').first()
ds = Dataset.objects.create(data_source=childmortality, vintage='2024',
                            descriptor='2024 child mortality data by county and state.')

# Note: the csv file we are importing here was constructed from the original, much larger analytics file
# that is downloadable from the referenced web page
df = pd.read_csv('../../external_data/child_mortality_2024.csv', dtype={'State FIPS Code': 'str',
                                                                   'County FIPS Code': 'str',
                                                                   '5-digit FIPS Code': 'str'})
df = df.replace(np.nan, None)
row_iter = df.iterrows()
#
records = [
    ChildMortality(
        state_fips=None if row['State FIPS Code'] == '0' else
            row['State FIPS Code'] if len(row['State FIPS Code']) == 2 else '0' + row['State FIPS Code'],
        county_fips=None if row['County FIPS Code'] == '0' else
            row['5-digit FIPS Code'] if len(row['5-digit FIPS Code']) == 5 else '0' + row['5-digit FIPS Code'],
        value=row['raw_value'],
        moe=None if row['CI_high'] is None or row['CI_low'] is None else (row['CI_high'] - row['CI_low']) / 2,
        dataset=ds
    )
    for index, row in row_iter
]

ChildMortality.objects.bulk_create(records)

# Create dataset
kff = DataSource.objects.filter(name__exact='KFF').first()
ds = Dataset.objects.create(data_source=kff, vintage='2022',
                            descriptor='State and national level emergency room visits, broken down by hospital owner type.')

df = pd.read_csv('../../external_data/kff_2022.csv', dtype=str)
df = df.replace(np.nan, None)
row_iter = df.iterrows()

records = [
    # "Location","State/Local Government","Non-Profit","For-Profit","Total"
    ERVisits(
        state_fips=None if row['Location'] == 'United States' else state_codes[us_state_to_abbrev[row['Location']]],
        state_local_value=None if row['State/Local Government'] is None else int(row['State/Local Government']),
        non_profit_value=None if row['Non-Profit'] is None else int(row['Non-Profit']),
        for_profit_value=None if row['For-Profit'] is None else int(row['For-Profit']),
        dataset=ds
    )
    for index, row in row_iter
]

ERVisits.objects.bulk_create(records)
