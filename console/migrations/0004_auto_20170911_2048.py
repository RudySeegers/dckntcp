# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-09-11 18:48
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('console', '0003_auto_20170911_0554'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='payout_frequency',
            field=models.CharField(choices=[(1, 'daily'), (2, 'weekly'), (3, 'monthly')], default=1, max_length=25),
        ),
    ]
