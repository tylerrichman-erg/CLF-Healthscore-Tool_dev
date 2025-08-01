# Generated by Django 4.1.5 on 2023-02-03 13:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('healthscore', '0003_remove_smartlocation_tract_id_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='State',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('short_code', models.CharField(max_length=2)),
                ('fips_code', models.CharField(max_length=2)),
                ('name', models.CharField(max_length=32)),
            ],
        ),
        migrations.CreateModel(
            name='BRFSS',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('metric', models.CharField(max_length=64)),
                ('value', models.FloatField(default=None, null=True)),
                ('moe', models.FloatField(default=None, null=True)),
                ('state', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='healthscore.state')),
            ],
        ),
    ]
