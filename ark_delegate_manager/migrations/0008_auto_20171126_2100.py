# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-11-26 20:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ark_delegate_manager', '0007_auto_20171126_1756'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dutchdelegatestatus',
            name='reward',
            field=models.BigIntegerField(default=0),
        ),
    ]