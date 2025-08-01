
"""
This class is responsible for constructing calls to, and fetching data from api.census.gov.
"""
import json
from json import JSONDecodeError

import numpy as np
import pandas as pd
import requests
import logging


class EJScreenDataLoader:

    def __init__(self, year, user):

        self.user = user
        self.log = logging.getLogger('requested')
        self.year = year
        self.datasources = {
            'EJ Screen': f'https://ejscreen.epa.gov/mapper/ejscreenRESTbroker.aspx?geometry=&distance=&unit=9035&areatype=tract&f=pjson'
        }

        self.metrics = {
            'EJ Screen': {
                'PM 2.5 (ug/m3)': 'PM25',
                'NATA Diesel PM (ug/m3)': 'DIESEL',
                'NATA Air Toxics Cancer Risk (risk per MM)': 'CANCER',
                'NATA Respiratory Hazard Index': 'RESP'
            }
        }

    def fetch_tract_data(self, datasource:str, state_fips_code:str, county:str, tract:str):

        # Use the dataset name to construct the appropriate endpoint, and then delegate to fetch_data()
        full_code = state_fips_code + county + tract
        endpoint = self.datasources[datasource] + f'&areaid={full_code}&namestr={full_code}'

        self.log.info(f"Tract-level EJScreen API call to {endpoint}", extra={'user': self.user.username})
        return self.fetch_data(datasource, endpoint)

    def fetch_data(self, datasource:str, endpoint:str):

        # Now, issue each call as constructed and deliver the response
        final_df = pd.DataFrame()

        print("API call: " + endpoint)

        data = requests.get(endpoint)

        # This is a hack of the response, which seems to be coming back with a strange error message!
        # data.text = data.text.replace('ERROR: Thread was being aborted.', '')
        try:
            df = data.json()
        except JSONDecodeError as e:
            return final_df

        for m in self.metrics[datasource].values():

            raw_col = 'RAW_E_' + m
            percentile_col = 'S_P_' + m
            state_avg_col = 'S_E_' + m

            try:
                raw = df[raw_col]
                percentile = df[percentile_col]
                state_avg = df[state_avg_col]

                this_df = pd.DataFrame({raw_col: raw, percentile_col: percentile, state_avg_col: state_avg}, index=[0])
                final_df = this_df if final_df.empty else final_df.join(this_df)
            except KeyError:
                print("EJScreen missing metric: " + raw_col)

        final_df.reset_index(inplace=True, drop=True)
        return final_df
