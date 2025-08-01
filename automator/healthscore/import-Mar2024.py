import sys, os, django
import numpy as np
import pandas as pd

sys.path.append("/home/healthscore/clf-healthscore/automator")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "automator.settings")
django.setup()

from healthscore.models import DataSource, Dataset, SmartLocation


# SmartLocation data for all states
data_source = DataSource.objects.filter(name__exact='SmartLocation').first()
dataset = Dataset.objects.create(data_source=data_source, vintage='Jan, 2021',
                                 descriptor='A mixture of data sources. We use one transit frequency variable.')
df = pd.read_csv('../../external_data/EPA_SmartLocationDatabase_V3_Jan_2021_Final.csv', dtype=str)
df = df.replace(np.nan, None)
row_iter = df.iterrows()


def zero_pad(value, desired_length):
    new_value = value

    while len(new_value) < desired_length:
        new_value = '0' + new_value

    return new_value


records = [

    SmartLocation(
        D4c=row["D4C"],
        block_group_id=zero_pad(row['STATEFP'], 2) + zero_pad(row['COUNTYFP'], 3) + zero_pad(row['TRACTCE'], 6) + row['BLKGRPCE'],
        dataset=dataset
    )
    for index, row in row_iter
]

SmartLocation.objects.bulk_create(records)
