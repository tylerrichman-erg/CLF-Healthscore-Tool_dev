
"""
This class is responsible for constructing calls to, and fetching data from chronicdata.cdc.gov.
"""
import logging
import pandas as pd
import numpy as np
from sodapy import Socrata


class CDCDataLoader:

    def __init__(self, year, user):

        self.user = user
        self.log = logging.getLogger('requested')
        self.year = year
        self.datasources = {
            'CDC Places': 'chronicdata.cdc.gov'
        }

        self.metrics = {
            'CDC Places': {
                'Cancer (excluding skin cancer) among adults >= 18': 'CANCER',
                'Current asthma among adults >= 18': 'CASTHMA',
                'COPD among adults >= 18': 'COPD',
                'Coronary heart disease among adults >= 18': 'CHD',
                'Diabetes among adults >= 18': 'DIABETES',
                'Stroke among adults >= 18': 'STROKE',
                'Mental health not good for >= 14 days among adults >= 18': 'MHLTH',
            }
        }

    def fetch_tract_data(self, datasource: str, state_fips_code: str, county: str, tract: str):

        full_code = state_fips_code + county + tract
        return self.fetch_data(datasource, full_code)

    def fetch_data(self, datasource: str, full_code: str):

        # Use the dataset name to construct the appropriate endpoint, and then create a Socrata
        # client to make requests against the CDC API, which has a SODA-based impl.
        endpoint = self.datasources[datasource]
        client = Socrata(endpoint, None)

        final_df = pd.DataFrame()
        for m in self.metrics[datasource].values():

            self.log.info(f"CDC API call with locationid={full_code}, measureid={m}",
                          extra={'user': self.user.username})

            # https://dev.socrata.com/foundry/data.cdc.gov/cwsq-ngmh
            # "PLACES: Local Data for Better Health, Census Tract Data 2023 release"
            results = client.get("cwsq-ngmh", year=self.year, locationid=full_code, measureid=m, limit=2000)

            try:
                df = pd.DataFrame.from_records(results)

                if not df.empty:
                    pop_est = float(df['totalpopulation'])

                    est_col = m + 'E'
                    moe_col = m + 'M'
                    est = float(df['data_value'])
                    moe = (abs((est - float(df['low_confidence_limit']))) +
                          abs((est - float(df['high_confidence_limit'])))) / 2

                    this_df = pd.DataFrame({est_col: est, moe_col: moe}, index=[0])

                    if final_df.empty:
                        final_df = this_df
                        final_df.loc[0, 'total_pop'] = pop_est
                    else:
                        final_df = final_df.join(this_df)
            except BaseException:
                print("Error processing response from CDC API for metric " + m)

        final_df.reset_index(inplace=True, drop=True)
        return final_df

