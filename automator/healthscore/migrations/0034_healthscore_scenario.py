# Generated by Django 4.1.7 on 2023-10-25 12:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('healthscore', '0033_remove_brfss_vintage_remove_educationct_vintage_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='healthscore',
            name='scenario',
            field=models.CharField(default='HNEF II', max_length=32),
        ),
    ]
