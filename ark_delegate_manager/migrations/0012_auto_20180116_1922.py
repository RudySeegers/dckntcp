# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2018-01-16 18:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ark_delegate_manager', '0011_auto_20180107_2049'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customaddressexceptions',
            name='share_RANGE_IS_0_TO_1',
            field=models.FloatField(default=0.96),
        ),
    ]
