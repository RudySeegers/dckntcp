from django.db import models
from django.core.validators import RegexValidator


class CronTest(models.Model):
    test_result = models.FloatField(default=0)


class VotePool(models.Model):
    address = RegexValidator(r'A[0-9a-zA-Z]{33}$', 'Only valid address formats are allowed.')

    ark_address = models.CharField(max_length=34, blank=True, default='', validators=[address], unique=True)
    payout_amount = models.FloatField(default=0)


class DutchDelegateStatus(models.Model):
    id = models.CharField(default='main', primary_key=True, max_length=10)
    rank = models.IntegerField(default=1)
    ark_votes = models.FloatField(default=0)
    voters = models.IntegerField(default=0)
    productivity = models.FloatField(default=100)
