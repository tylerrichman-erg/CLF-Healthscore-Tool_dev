# Generated by Django 4.1.7 on 2023-09-22 13:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('healthscore', '0031_remove_dataset_descriptor_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='datasource',
            name='descriptor',
        ),
        migrations.AddField(
            model_name='dataset',
            name='descriptor',
            field=models.CharField(max_length=128, null=True),
        ),
    ]
