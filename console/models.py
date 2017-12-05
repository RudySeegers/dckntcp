from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from console.choices import PAYOUT_CHOICES
from django.core.validators import RegexValidator
from annoying.fields import AutoOneToOneField
import console.custom_model_fields as custom


class UserProfile(models.Model):
    SENDER_CHOICES = (
        (1, 'Send payout second address.'),
        (2, 'Send payout to voting address.')
    )
    EMAIL_CHOICES = (
        (1, "Don't inform me by email about payouts and current news."),
        (2, 'Feel free to send me emails.')
    )
    address = RegexValidator(r'A[0-9a-zA-Z]{33}$', 'Only valid address formats are allowed.')

    user = AutoOneToOneField(User, related_name='user', primary_key=True)
    main_ark_wallet = models.CharField(max_length=34, blank=True, default='', validators=[address])
    main_ark_tag = models.CharField(max_length=34, blank=True, null=True)
    ark_send_to_second_address = models.IntegerField(choices=SENDER_CHOICES, default=2)

    receiving_ark_address = models.CharField(max_length=34, blank=True, null=True, validators=[address])
    receiving_ark_address_tag = models.CharField(max_length=34, blank=True, null=True)

    receiving_ark_address_verified = models.BooleanField(default=False)

    payout_frequency = models.IntegerField(choices=PAYOUT_CHOICES, default=2)
    preferred_day = custom.DayOfTheWeekField(default='8')

    """inform by email is decided by the user in the settings tab."""
    inform_by_email = models.IntegerField(default=1, choices=EMAIL_CHOICES)

    """ send_email_about_payout is set to True during a payout run if a payout is transmitted"""
    send_email_about_payout = models.BooleanField(default=False)

    def __str__(self):
        return self.main_ark_wallet


def create_profile(sender, **kwargs):
    user = kwargs["instance"]
    if kwargs["created"]:
        user_profile = UserProfile(user=user)
        user_profile.save()
        post_save.connect(create_profile, sender=User)


