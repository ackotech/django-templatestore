# Generated by Django 3.0.7 on 2024-09-14 11:04

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('templatestore', '0012_templateserviceprovider'),
    ]

    operations = [
        migrations.AddField(
            model_name='templateserviceprovider',
            name='metadata',
            field=django.contrib.postgres.fields.jsonb.JSONField(default={}),
        ),
    ]
