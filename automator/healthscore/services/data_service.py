import logging
from django.db import transaction
from healthscore.data.ACSDataLoader import ACSDataLoader
from healthscore.data.CDCDataLoader import CDCDataLoader
from healthscore.data.EJScreenDataLoader import EJScreenDataLoader
from healthscore.models import Metric, State, Dataset, DataSource
from django.core.exceptions import ObjectDoesNotExist


class DataService:
    """
    This class brokers requests for data by first attempting to find them in the database, and then
    fetching them from an API if possible and subsequently storing them in the database.

    Note that it makes use of transactions to avoid adding partial/incomplete datasets to the db.
    """
    def __init__(self, user):
        self.user = user
        self.log = logging.getLogger('requested')

    @staticmethod
    def vintages():
        return {
            'ACS': '2021',
            'CDC': '2021',
            'BRFSS': '2021',
            'EJScreen': '2019',
            'LifeExpectancy': '2018',
            'Latch': 'Nov 23, 2018',
            'SmartLocation': 'Jan, 2021',
            'EducationMA': 'Jan 09, 2020',
            'EducationMA Subgroup': 'Oct 15, 2019',
            'EducationCT': 'unknown',
            'EducationCT Subgroup': 'unknown',
            'EducationRI': 'unknown',
            'SchoolDistrict': '2022',
            'NMTC': 'Sep 01, 2023',
            'NHTS': 'May 31, 2017',
            'OpportunityZone': 'July 31, 2023',
            'ChildMortality': '2024',
            'PersonalHealthCare': '2022',
            'NSCH': '2022',
            'ERVisits': '2022',
            'MaternityCare': '2020',
            'MentalHealthCare': '2022',
            'NREL': '2020-2021',
            'HUD': '2023'
        }

    @transaction.atomic
    def load_acs(self, vintage: str, state_short_code: str, county: str, tracts: list):
        """
        :param vintage: i.e. '2019'
        :param state: i.e. 'MA'
        :param county: i.e. '009'
        :param tracts: i.e. ['215102', '215101', '216100']
        :return: Metric objects corresponding to the requested data
        """
        all_records = []

        # Find the state
        try:
            state = State.objects.get(short_code=state_short_code)
        except ObjectDoesNotExist:
            self.log.error("Couldn't find state with abbreviation " + state_short_code, extra={'user': self.user.username})
            return all_records

        acs_loader = ACSDataLoader(vintage, self.user)

        for d in acs_loader.datasources.keys():

            self.log.info(f"Loading ACS data for datasource={d}...", extra={'user': self.user.username})

            # Find the datasource (i.e. 'ACS Detail')
            try:
                datasource = DataSource.objects.get(name=d)
            except ObjectDoesNotExist:
                self.log.error("Couldn't find data source " + d, extra={'user': self.user.username})
                return all_records

            # Load (creating first if necessary) the dataset for this source/vintage combination.
            try:
                dataset = Dataset.objects.get(data_source__name=d, vintage=vintage)
            except ObjectDoesNotExist:
                self.log.info(f'Dataset for {datasource.name} / {vintage} does not exist. Creating...',
                              extra={'user': self.user.username})
                dataset = Dataset.objects.create(data_source=datasource, vintage=vintage,
                                                 descriptor="ACS 5 year estimates. Data is from the entire 5 year span, and the vintage represents the final year in the span.")

            # Load the metrics so that we can perform a reverse lookup on the census code if we end up needing
            # to fetch any of the geoids from the API.
            # (i.e. 'B01003_001' -> 'Total Population')
            metrics = acs_loader.metrics[d]

            # Fetch and persist state-level data if any metrics not already present
            metric_exists = {k: Metric.objects.filter(
                dataset__data_source__name=d, dataset__vintage=vintage,
                geoid=state.fips_code, code=v).exists() for k, v in metrics.items()}

            if not all(metric_exists.values()):

                self.log.info(f"State-level ACS data metric(s) for datasource={d} missing. Fetching...",
                              extra={'user': self.user.username})

                # Fetch them all, but only insert the ones that are missing...
                try:
                    fetched_df = acs_loader.fetch_state_data(d, state.fips_code)

                    # Only iterate the columns that represent values (i.e. that end in 'E')
                    # The corresponding margin of error will added to the same record.
                    value_columns = fetched_df.loc[:, fetched_df.columns.str.endswith('E')]

                    records = []

                    row_iter = fetched_df.iterrows()
                    for index, row in row_iter:
                        for value_col in value_columns:

                            code = value_col[:-1]
                            metric_name = list(metrics.keys())[list(metrics.values()).index(code)]

                            if metric_exists[metric_name]:
                                continue

                            moe_col = code + 'M'

                            est = fetched_df[value_col][index]
                            moe = fetched_df[moe_col][index]

                            if est < 0:
                                est = None
                                moe = None
                            elif moe < 0:
                                moe = None


                            records.append(
                                Metric(
                                    state_id=state.id,
                                    dataset_id=dataset.id,
                                    geoid=state.fips_code,
                                    name=metric_name,
                                    code=code,
                                    value=est,
                                    moe=moe
                                )
                            )
                    Metric.objects.bulk_create(records)
                except BaseException:
                    print("Error fetching state-level ACS missing metrics for datasource: " + d)

            # Fetch and persist tract-level data if not already present
            for tract in tracts:

                geoid = state.fips_code + county + tract

                metric_exists = {k: Metric.objects.filter(
                    dataset__data_source__name=d, dataset__vintage=vintage,
                    geoid=geoid, code=v).exists() for k, v in metrics.items()}

                if not all(metric_exists.values()):

                    try:
                        fetched_df = acs_loader.fetch_tract_data(d, state.fips_code, county, tract)

                        if not fetched_df.empty:
                            # Only iterate the columns that represent values (i.e. that end in 'E')
                            # The corresponding margin of error will be added to the same record.
                            value_columns = fetched_df.loc[:, fetched_df.columns.str.endswith('E')]

                            records = []

                            row_iter = fetched_df.iterrows()
                            for index, row in row_iter:
                                for value_col in value_columns:

                                    code = value_col[:-1]
                                    metric_name = list(metrics.keys())[list(metrics.values()).index(code)]

                                    if metric_exists[metric_name]:
                                        continue

                                    moe_col = code + 'M'

                                    est = fetched_df[value_col][index]
                                    moe = fetched_df[moe_col][index]

                                    if est < 0:
                                        est = None
                                        moe = None
                                    elif moe < 0:
                                        moe = None

                                    records.append(
                                        Metric(
                                            state_id=state.id,
                                            dataset_id=dataset.id,
                                            geoid=state.fips_code + county + tract,
                                            name=metric_name,
                                            code=code,
                                            value=est,
                                            moe=moe
                                        )
                                    )
                            Metric.objects.bulk_create(records)
                    except BaseException:
                        print("Error fetching ACS missing metrics for tract: " + tract)

        # Return the Metric records for both state and tracts
        geoids = [state.fips_code + county + t for t in tracts]
        all_geoids = [state.fips_code] + geoids
        return Metric.objects.filter(
            dataset__data_source__name__in=acs_loader.datasources.keys(), dataset__vintage=vintage,
            geoid__in=all_geoids
        )

    @transaction.atomic
    def load_cdc(self, vintage: str, state: str, county: str, tracts: list):
        """
        :param vintage: i.e. '2019'
        :param state: i.e. 'MA'
        :param county: i.e. '009'
        :param tracts: i.e. ['215102', '215101', '216100']
        :return: Metric objects corresponding to the requested data
        """
        all_records = []

        # Find the state
        try:
            state = State.objects.get(short_code=state)
        except ObjectDoesNotExist:
            self.log.error("Couldn't find state with abbreviation " + state)
            return all_records

        cdc_loader = CDCDataLoader(vintage, self.user)

        for d in cdc_loader.datasources.keys():

            # Find the datasource (i.e. 'CDC Places')
            try:
                datasource = DataSource.objects.get(name=d)
            except ObjectDoesNotExist:
                self.log.error("Couldn't find data source " + d)
                return all_records

            # Load (creating first if necessary) the dataset for this source/vintage combination.
            try:
                dataset = Dataset.objects.get(data_source__name=d, vintage=vintage)
            except ObjectDoesNotExist:
                self.log.info(f'Dataset for {datasource.name} / {vintage} does not exist. Creating...')
                dataset = Dataset.objects.create(data_source=datasource, vintage=vintage,
                                                 descriptor="CDC Places data for the year specified by the vintage.")

            # Load the metrics so that we can perform a reverse lookup on the census code if we end up needing
            # to fetch any of the geoids from the API.
            # (i.e. 'B01003_001' -> 'Total Population')
            metrics = cdc_loader.metrics[d]

            # No state-level data for this API...
            # Fetch and persist tract-level data if not already present
            for tract in tracts:

                geoid = state.fips_code + county + tract

                metric_exists = {k: Metric.objects.filter(
                    dataset__data_source__name=d, dataset__vintage=vintage,
                    geoid=geoid, code=v).exists() for k, v in metrics.items()}

                if not all(metric_exists.values()):

                    try:
                        fetched_df = cdc_loader.fetch_tract_data(d, state.fips_code, county, tract)

                        # Only iterate the columns that represent values (i.e. that end in 'E')
                        # The corresponding margin of error will added to the same record.
                        value_columns = fetched_df.loc[:, fetched_df.columns.str.endswith('E')]

                        records = []

                        population_added = False
                        row_iter = fetched_df.iterrows()
                        for index, row in row_iter:
                            for value_col in value_columns:

                                code = value_col[:-1]
                                metric_name = list(metrics.keys())[list(metrics.values()).index(code)]

                                if metric_exists[metric_name]:
                                    continue

                                moe_col = code + 'M'

                                est = fetched_df[value_col][index]
                                moe = fetched_df[moe_col][index]
                                total_pop = fetched_df['total_pop'][index]

                                if est < 0:
                                    est = None
                                    moe = None
                                elif moe < 0:
                                    moe = None

                                records.append(
                                    Metric(
                                        state_id=state.id,
                                        dataset_id=dataset.id,
                                        geoid=state.fips_code + county + tract,
                                        name=metric_name,
                                        code=code,
                                        value=est,
                                        moe=moe
                                    )
                                )

                                if not population_added:
                                    records.append(
                                        Metric(
                                            state_id=state.id,
                                            dataset_id=dataset.id,
                                            geoid=state.fips_code + county + tract,
                                            name='PLACES Population',
                                            code='TOT_POP',
                                            value=total_pop,
                                            moe=0
                                        )
                                    )
                                    population_added = True
                        Metric.objects.bulk_create(records)
                    except BaseException:
                        print("Error fetching CDC missing metrics for tract: " + tract)

        # Return the Metric records for tracts
        geoids = [state.fips_code + county + t for t in tracts]
        all_geoids = [state.fips_code] + geoids
        return Metric.objects.filter(
            dataset__data_source__name__in=cdc_loader.datasources.keys(), dataset__vintage=vintage,
            geoid__in=all_geoids
        )


        """
    Load all EJ Screen data for a given vintage.

        Example call: load_ejscreen_tracts('2019', ['2515102', '215101', '216100'])
    """

    @transaction.atomic
    def load_ejscreen(self, vintage: str, state: str, county: str, tracts: list):
        """
        :param vintage: i.e. '2019'
        :param state: i.e. 'MA'
        :param county: i.e. '009'
        :param tracts: i.e. ['215102', '215101', '216100']
        :return: Metric objects corresponding to the requested data
        """
        all_records = []

        # Find the state
        try:
            state = State.objects.get(short_code=state)
        except ObjectDoesNotExist:
            self.log.error("Couldn't find state with abbreviation " + state)
            return all_records

        ej_loader = EJScreenDataLoader(vintage, self.user)

        for d in ej_loader.datasources.keys():

            # Find the datasource (i.e. 'EJ Screen')
            try:
                datasource = DataSource.objects.get(name=d)
            except ObjectDoesNotExist:
                self.log.error("Couldn't find data source " + d)
                return all_records

            # Load (creating first if necessary) the dataset for this source/vintage combination.
            try:
                dataset = Dataset.objects.get(data_source__name=d, vintage=vintage)
            except ObjectDoesNotExist:
                self.log.info(f'Dataset for {datasource.name} / {vintage} does not exist. Creating...')
                dataset = Dataset.objects.create(data_source=datasource, vintage=vintage,
                                                 descriptor="EJ Screen environmental data vintages vary. Check datasource reference URL for more information.")

            # Load the metrics so that we can perform a reverse lookup on the census code if we end up needing
            # to fetch any of the geoids from the API.
            # (i.e. 'B01003_001' -> 'Total Population')
            metrics = ej_loader.metrics[d]

            state_data = {}

            # State-level data will be returned along with tract level data...
            # Fetch and persist tract-level data if not already present
            for tract in tracts:

                geoid = state.fips_code + county + tract

                metric_exists = {k: Metric.objects.filter(
                    dataset__data_source__name=d, dataset__vintage=vintage,
                    geoid=geoid, code__contains=v).exists() for k, v in metrics.items()}

                if not all(metric_exists.values()):

                    try:
                        fetched_df = ej_loader.fetch_tract_data(d, state.fips_code, county, tract)

                        # Only iterate the columns that represent values (i.e. that end in 'E')
                        # The corresponding margin of error will added to the same record.
                        value_columns = fetched_df.loc[:, fetched_df.columns.str.startswith('RAW_E')]

                        records = []

                        row_iter = fetched_df.iterrows()
                        for index, row in row_iter:
                            for value_col in value_columns:

                                code = value_col[6:]
                                metric_name = list(metrics.keys())[list(metrics.values()).index(code)]

                                if metric_exists[metric_name]:
                                    continue

                                # Save the state value for later
                                state_avg_col = 'S_E_' + code
                                state_avg = fetched_df[state_avg_col][index]
                                state_data[state_avg_col] = state_avg

                                est = fetched_df[value_col][index]
                                records.append(
                                    Metric(
                                        state_id=state.id,
                                        dataset_id=dataset.id,
                                        geoid=state.fips_code + county + tract,
                                        name=metric_name,
                                        code=value_col,
                                        value=est,
                                        moe=None
                                    )
                                )

                                percentile_col = 'S_P_' + code
                                percentile = fetched_df[percentile_col][index]
                                records.append(
                                    Metric(
                                        state_id=state.id,
                                        dataset_id=dataset.id,
                                        geoid=state.fips_code + county + tract,
                                        name='Percentile ' + metric_name,
                                        code=percentile_col,
                                        value=percentile,
                                        moe=None
                                    )
                                )
                        Metric.objects.bulk_create(records)
                    except BaseException:
                        print("Error fetching EJScreen missing metrics for tract: " + tract)
                        return all_records

            # Persist state-level data if not already present (note this data was fetched
            # along with the tract-level data...)
            metric_exists = {k: Metric.objects.filter(
                dataset__data_source__name=d, dataset__vintage=vintage,
                geoid=state.fips_code, code__contains=v).exists() for k, v in metrics.items()}
            if not all(metric_exists.values()):

                records = []

                for key in state_data:

                    code = key[4:]
                    metric_name = list(metrics.keys())[list(metrics.values()).index(code)]

                    if metric_exists[metric_name]:
                        continue

                    value = state_data[key]

                    records.append(
                        Metric(
                            state_id=state.id,
                            dataset_id=dataset.id,
                            geoid=state.fips_code,
                            name=metric_name,
                            code=key,
                            value=value,
                            moe=None
                        )
                    )
                Metric.objects.bulk_create(records)

        # Return the Metric records for both state and tracts
        geoids = [state.fips_code + county + t for t in tracts]
        all_geoids = [state.fips_code] + geoids
        return Metric.objects.filter(
            dataset__data_source__name__in=ej_loader.datasources.keys(), dataset__vintage=vintage,
            geoid__in=all_geoids
        )
