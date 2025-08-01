
"""
This class is responsible for constructing calls to, and fetching data from api.census.gov.
"""
import logging
from json import JSONDecodeError

import numpy as np
import pandas as pd
import requests


class ACSDataLoader:

    def __init__(self, year, user):

        self.user = user
        self.log = logging.getLogger('requested')
        self.year = year
        self.api_key = 'f9f363d3f234e17efe942546146445b2a9395a1d'
        self.datasources = {
            'ACS Detail': f'https://api.census.gov/data/{year}/acs/acs5?key={self.api_key}&get=metrics',
            'ACS Subject': f'https://api.census.gov/data/{year}/acs/acs5/subject?key={self.api_key}&get=metrics',
            'ACS Profile': f'https://api.census.gov/data/{year}/acs/acs5/profile?key={self.api_key}&get=metrics'
        }

        self.metrics = {
            'ACS Detail': {
                'Median Household Income': 'B19013_001',
                # 'Female Householder': 'B11012_010',

                # Population of Color
                'Total with Race Data': 'B02001_001',
                'Total White Alone': 'B02001_002',

                # Cost Burdened Renters
                'Total with Rent Data': 'B25070_001',
                'Rent 30.0-34.9%': 'B25070_007',
                'Rent 35.0-39.9%': 'B25070_008',
                'Rent 40.0-49.9%': 'B25070_009',
                'Rent >50.0%': 'B25070_010',

                # Population
                'Total Population': 'B01003_001'
            },
            'ACS Subject': {

                # Median Household Income
                'Total with Income Data': 'S1901_C01_001',
                '<10000': 'S1901_C01_002',
                '10000-14999': 'S1901_C01_003',
                '15000-24999': 'S1901_C01_004',
                '25000-34999': 'S1901_C01_005',
                '35000-49999': 'S1901_C01_006',
                '50000-74999': 'S1901_C01_007',
                '75000-99999': 'S1901_C01_008',
                '100000-149999': 'S1901_C01_009',
                '150000-199999': 'S1901_C01_010',
                '>200000': 'S1901_C01_011',

                # Poverty Rate
                # 'Poverty Rate': 'S1701_C03_001',
                'Total with Poverty Data': 'S1701_C01_001',
                'Below Poverty Level': 'S1701_C02_001',
                'Poverty Rate (%)': 'S1701_C03_001',

                # Education Attainment
                # '% >25 with Associates': 'S1501_C02_011',
                # '% >25 with Bachelors or higher': 'S1501_C02_015',
                'Total with Education Data >25': 'S1501_C01_006',
                '> 25 with Associates' : 'S1501_C01_011',
                '> 25 with Bachelors or higher' : 'S1501_C01_015',

                # Limited English Households
                'Limited English-speaking Households (%)': 'S1602_C04_001',
                'Total with Language Data': 'S1602_C01_001',
                'Limited English-speaking': 'S1602_C03_001',

                # Low-Income <5
                'Low-Income <5': 'S1701_C02_003',
                'Total <5': 'S1701_C01_003',
                'Population of Low-Income Children <5 (%)': 'S1701_C03_003',

                # Low-Income >65
                'Low-Income >65': 'S1701_C02_010',
                'Total >65': 'S1701_C01_010',
                'Population of Low-Income Seniors >65 (%)': 'S1701_C03_010',

                # Transit Use
                'Workers >16': 'S0801_C01_001',
                '% Public Transit': 'S0801_C01_009',
                '% Walked': 'S0801_C01_010',
                '% Bicycle': 'S0801_C01_011',

                # Percent with a disability
                'Population With Disability (%)': 'S1810_C03_001'
            },
            'ACS Profile': {

                'Female Householder (%)': 'DP02_0011P',

                # Unemployment Rate
                'Unemployment Rate (%)': 'DP03_0009P',
                'In Labor Force': 'DP03_0002',
                'Total Unemployed': 'DP03_0005',

                # Car Ownership
                'Occupied Housing Units': 'DP04_0057',
                'No vehicles': 'DP04_0058',
                '1 vehicle': 'DP04_0059',
                '2 vehicles': 'DP04_0060',
                '>3 vehicles': 'DP04_0061'
            }
        }

    def fetch_state_data(self, datasource: str, state_fips_code: str):

        # Use the datasource name to construct the appropriate endpoint, and then delegate to fetch_data()
        endpoint = self.datasources[datasource] + f'&for=state:{state_fips_code}'

        self.log.info(f"State-level ACS API call to {endpoint}", extra={'user': self.user.username})

        print("Fetching state ACS data at this endpoint: " + endpoint)

        return self.fetch_data(datasource, endpoint)

    def fetch_tract_data(self, datasource: str, state_fips_code: str, county: str, tract: str):

        # Use the dataset name to construct the appropriate endpoint, and then delegate to fetch_data()
        endpoint = self.datasources[datasource] + f'&for=tract:{tract}&in=state:{state_fips_code}+county:{county}'

        self.log.info(f"Tract-level ACS API call to {endpoint}", extra={'user': self.user.username})
        return self.fetch_data(datasource, endpoint)

    def fetch_data(self, datasource: str, endpoint: str):

        # Fetch the data for the given endpoint. If the number of metrics exceeds 25,
        # split them into multiple calls because api.census.gov allows at most 50 metrics in a single call,
        # and we are requesting 2 values for each metric (value, moe).

        # 1. Substitute defined metrics in the form of a comma separated list
        # 2. If there are too many metrics, split into multiple calls
        # 3. Make call(s), sanitize response, and return.
        calls = []

        i = 0
        metrics = ''
        for key in self.metrics[datasource].keys():
            metrics = metrics + f"""{self.metrics[datasource][key]}E,{self.metrics[datasource][key]}M,"""
            i = i + 1

            if i == 25:
                # Note we are chopping off the last character, which is a comma!
                calls.append(endpoint.replace('metrics', metrics[:-1]))
                i = 0
                metrics = ''

        if len(metrics) > 0:
            calls.append(endpoint.replace('metrics', metrics[:-1]))

        # Now, issue each call as constructed and deliver the response
        final_df = pd.DataFrame()
        for call in calls:

            data = requests.get(call)

            print("ACS call: " + call)

            try:
                df = pd.DataFrame.from_dict(data.json())

                # Shift the first row of data up into the column header...
                df.rename(columns=df.iloc[0], inplace=True)
                df.drop(df.index[0], inplace=True)
                df = df.astype(np.float32)

                final_df = df if final_df.empty else pd.merge(final_df, df, on='state')
            except BaseException:
                print("Error processing response from ACS API for call: " + call)

        final_df.reset_index(inplace=True, drop=True)
        return final_df
