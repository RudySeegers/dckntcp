from django.db import models
from django.core.validators import RegexValidator
from django.contrib.postgres.fields import JSONField


class PayoutReports(models.Model):
    address = RegexValidator(r'A[0-9a-zA-Z]{33}$', 'Only valid address formats are allowed.')
    address = models.CharField(max_length=34, blank=True, default='', validators=[address])
    payout_report = JSONField()
    balance_report = JSONField()
    roi_report = JSONField()