# Generated by Django 4.1.7 on 2023-08-24 10:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('healthscore', '0025_opportunityzone_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='opportunityzone',
            name='vintage',
            field=models.CharField(default='2023', max_length=32),
        ),
    ]
