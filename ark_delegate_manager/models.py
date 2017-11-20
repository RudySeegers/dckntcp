from django.db import models
from django.core.validators import RegexValidator

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
    reward = models.IntegerField(default=0)
    vendorfield = models.CharField(max_length=64, default='Thank you for voting.')


class EarlyAdopterExceptions(models.Model):
    address = RegexValidator(r'A[0-9a-zA-Z]{33}$', 'Only valid address formats are allowed.')
    ark_address = models.CharField(max_length=34, blank=True, default='', validators=[address], unique=True)


class ArkDelegates(models.Model):
    address = RegexValidator(r'A[0-9a-zA-Z]{33}$', 'Only valid address formats are allowed.')

    pubkey = models.CharField(primary_key=True, max_length=100)
    username = models.CharField(max_length=100)
    address = models.CharField(max_length=34, blank=True, default='', validators=[address], unique=True)
    voters = models.IntegerField(default=0)
    productivity = models.FloatField(default=0)
    ark_votes = models.FloatField(default=0)
    producedblocks = models.IntegerField(default=0)
    missedblocks = models.IntegerField(default=0)
    rank = models.IntegerField(default=0)


class Node(models.Model):
    id = models.CharField(default='main', primary_key=True, max_length=10)
    blockchain_height = models.IntegerField(default=0)
