# Generated by Django 4.1.5 on 2023-02-20 13:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('healthscore', '0011_rename_year_dataset_vintage'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='metric',
            unique_together={('dataset', 'state', 'geoid', 'name')},
        ),
    ]
