import sys, os, django
import numpy as np
import pandas as pd

sys.path.append("/home/healthscore/clf-healthscore/automator")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "automator.settings")
django.setup()

from healthscore.models import DataSource, Dataset, HouseholdBurden, Homelessness, BRFSS, State

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

# BRFSS data for all states
brfss_ds = Dataset.objects.filter(data_source__name__exact='BRFSS').first()

df = pd.read_csv('../../external_data/all_brfss_2021.csv', dtype=str)
df = df.replace(np.nan, None)
row_iter = df.iterrows()

BRFSS.objects.all().delete()

records = [
    # State,Overall Homeless,Total Population
    BRFSS(
        state=State.objects.filter(name=row['State']).first(),
        metric=row['Metric'],
        value=float(row['Value']),
        moe=(float(row['High_Confidence_Limit']) - float(row['Low_Confidence_Limit'])) / 2,
        dataset=brfss_ds
    )
    for index, row in row_iter
]

BRFSS.objects.bulk_create(records)

# Create data source for Homelessness
# records = [
#     DataSource(name="HUD", reference_url='https://www.hudexchange.info/resource/3031/pit-and-hic-data-since-2007/')
# ]
# DataSource.objects.bulk_create(records)
#
# # Create dataset
# hud = DataSource.objects.filter(name__exact='HUD').first()
# ds = Dataset.objects.create(data_source=hud, vintage='2023',
#                             descriptor='State homeless and total population counts.')
#
# df = pd.read_csv('../../external_data/homelessness-pop-2023.csv', dtype=str)
# df = df.replace(np.nan, None)
# row_iter = df.iterrows()
#
# records = [
#     # State,Overall Homeless,Total Population
#     Homelessness(
#         state_fips=state_codes[us_state_to_abbrev[row['State']]],
#         homeless=int(row['Overall Homeless']),
#         population=int(row['Total Population']),
#         dataset=ds
#     )
#     for index, row in row_iter
# ]
#
# Homelessness.objects.bulk_create(records)


# Create data source for Household Burden
# records = [
#     DataSource(name="NREL", reference_url='https://maps.nrel.gov/slope/data-viewer?filters=%5B%5D&layer=eej.household-energy-burden&year=2020&res=county')
# ]
# DataSource.objects.bulk_create(records)
#
# # Create dataset
# mha = DataSource.objects.filter(name__exact='NREL').first()
# ds = Dataset.objects.create(data_source=mha, vintage='2020-2021',
#                             descriptor='Tract-level transportation and energy household burden, coming from two separate reports via NREL.')
#
# df = pd.read_csv('../../external_data/nrel_energy_burden_tracts.csv', dtype=str)
# df = df.replace(np.nan, None)
# row_iter = df.iterrows()
#
# records = [
#     # Geography ID,Transportation Burden Pct Income,Energy Burden Pct Income
#     HouseholdBurden(
#         geoid=row['Geography ID'][1:],
#         transportation_value=None if row['Transportation Burden Pct Income'] is None else float(row['Transportation Burden Pct Income']),
#         energy_value=None if row['Energy Burden Pct Income'] is None else float(row['Energy Burden Pct Income']),
#         transportation_burden=None if row['Transportation Burden Pct Income'] is None else ('Low' if float(row['Transportation Burden Pct Income']) < 0.036 else
#         ('Medium' if float(row['Transportation Burden Pct Income']) <= 0.042 else 'High')),
#         energy_burden=None if row['Energy Burden Pct Income'] is None else ('Low' if float(row['Energy Burden Pct Income']) < 0.038 else
#         ('Medium' if float(row['Energy Burden Pct Income']) <= 0.06 else 'High')),
#         dataset=ds
#     )
#     for index, row in row_iter
# ]
#
# HouseholdBurden.objects.bulk_create(records)

