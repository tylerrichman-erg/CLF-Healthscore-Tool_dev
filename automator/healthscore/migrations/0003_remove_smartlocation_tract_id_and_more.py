# Generated by Django 4.1.5 on 2023-02-03 12:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('healthscore', '0002_smartlocation'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='smartlocation',
            name='tract_id',
        ),
        migrations.AddField(
            model_name='smartlocation',
            name='block_group_id',
            field=models.CharField(default=None, max_length=12, unique=True),
        ),
    ]
