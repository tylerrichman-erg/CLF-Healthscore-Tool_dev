# Generated by Django 4.1.7 on 2023-08-24 10:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('healthscore', '0024_rename_tract_id_lifeexpectancy_geoid'),
    ]

    operations = [
        migrations.CreateModel(
            name='OpportunityZone',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('geoid', models.CharField(max_length=16, unique=True)),
            ],
        ),
        migrations.AddIndex(
            model_name='opportunityzone',
            index=models.Index(fields=['geoid'], name='healthscore_geoid_dbf78c_idx'),
        ),
    ]
