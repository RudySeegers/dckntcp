# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-09-11 03:54
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('console', '0002_userprofile_status'),
    ]

    operations = [
        migrations.RenameField(
            model_name='userprofile',
            old_name='status',
            new_name='payout_frequency',
        ),
    ]
