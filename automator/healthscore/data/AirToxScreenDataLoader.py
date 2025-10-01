
"""
This class is responsible for constructing calls to, and fetching data from api.census.gov.
"""
import json
from json import JSONDecodeError

import numpy as np
import pandas as pd
import requests
import logging


class AirToxScreenDataLoader:

    def __init__(self, year, user):

        self.user = user
        self.log = logging.getLogger('requested')
        self.year = year
        self.datasources = {
            'AirToxScreen': ''
        }

        self.metrics = {
            'AirToxScreen': {
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

        tract_id = endpoint[-11:]

        df = pd.read_excel('/home/healthscore/clf-healthscore/external_data/US_AIRTOXSCREEN_2024_cleaned.xlsx', engine='openpyxl')
        df = df.loc[df['ID'] == int(tract_id)]

        col_list = list()

        for m in self.metrics[datasource].values():
            raw_col = 'RAW_E_' + m
            percentile_col = 'S_P_' + m
            state_avg_col = 'S_E_' + m

            col_list.append(raw_col)
            col_list.append(percentile_col)
            col_list.append(state_avg_col)
    
        df = df[col_list]

        final_df = df

        return final_df
