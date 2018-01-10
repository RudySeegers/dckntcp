from django.db import models
from django.core.validators import RegexValidator
from django.contrib.postgres.fields import JSONField


class Setting(models.Model):
    id = models.CharField(default='main', primary_key=True, max_length=10)
    vendorfield = models.CharField(max_length=64, default='Thank you for voting.')
    news_link = models.CharField(max_length=300, blank=True, null=True)

    def __str__(self):
        return self.id


class VotePool(models.Model):
    address = RegexValidator(r'A[0-9a-zA-Z]{33}$', 'Only valid address formats are allowed.')
    ark_address = models.CharField(max_length=34, blank=True, default='', validators=[address], unique=True)
    payout_amount = models.FloatField(default=0)
    blacklisted = models.BooleanField(default=False)
    status = models.CharField(max_length=200, default="Non-Dutchdelegate Voter")
    share = models.IntegerField(default=0.95)

    def __str__(self):
        return self.ark_address


class DutchDelegateStatus(models.Model):
    id = models.CharField(default='main', primary_key=True, max_length=10)
    rank = models.IntegerField(default=1)
    ark_votes = models.FloatField(default=0)
    voters = models.IntegerField(default=0)
    productivity = models.FloatField(default=100)
    reward = models.BigIntegerField(default=0)


class CustomAddressExceptions(models.Model):
    address = RegexValidator(r'A[0-9a-zA-Z]{33}$', 'Only valid address formats are allowed.')
    old_ark_address = models.CharField(max_length=34, blank=True, default='', validators=[address])
    new_ark_address = models.OneToOneField(max_length=34, blank=True, default='', validators=[address], unique=True,
                                           to=VotePool, on_delete=models.CASCADE)

    email = models.EmailField(null=True, blank=True)
    info = models.CharField(max_length=10000, blank=True, default='')
    share_RANGE_IS_0_TO_1 = models.IntegerField(default=0.96)
    status_name = models.CharField(max_length=100, default='Early Adopter')

    def __str__(self):
        return self.new_ark_address


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
    share_percentages = JSONField(default={999999999999999999: 'N.A.'})

    def __str__(self):
        return self.username


class Node(models.Model):
    id = models.CharField(default='main', primary_key=True, max_length=10)
    blockchain_height = models.IntegerField(default=0)


class CronLock(models.Model):
    job_name = models.CharField(blank=True, max_length=100, unique=True)
    lock = models.BooleanField(default=False)

    def __str__(self):
        return self.job_name


class PayoutTable(models.Model):
    address = RegexValidator(r'A[0-9a-zA-Z]{33}$', 'Only valid address formats are allowed.')
    address = models.CharField(max_length=34, blank=True, validators=[address], unique=True)
    amount = models.BigIntegerField(default=0)
    last_payout_blockchain_side = models.IntegerField(default=0)
    vote_timestamp = models.IntegerField(default=0)
    status = models.BooleanField(default=False)
    last_payout_server_side = models.IntegerField(default=0)
