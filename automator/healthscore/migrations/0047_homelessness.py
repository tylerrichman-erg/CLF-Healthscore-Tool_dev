# Generated by Django 4.1.7 on 2024-02-11 15:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('healthscore', '0046_alter_householdburden_energy_burden_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Homelessness',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('state_fips', models.CharField(max_length=2, null=True)),
                ('homeless', models.IntegerField(default=0)),
                ('population', models.IntegerField(default=0)),
                ('dataset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='healthscore.dataset')),
            ],
        ),
    ]
