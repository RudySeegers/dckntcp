from django import forms
from console.models import UserProfile
from django.core.validators import RegexValidator
from django.utils.translation import ugettext_lazy as _


class SettingsForm(forms.ModelForm):
    EMAIL_CHOICES = (
        (1, "Don't inform me by email about payouts and current news."),
        (2, 'Feel free to send me emails  .'))
    address = RegexValidator(r'A[0-9a-zA-Z]{33}$', 'Only valid address formats are allowed.')
    main_ark_wallet = forms.CharField(validators=[address])

    class Meta:
        model = UserProfile
        fields = ['preferred_day', 'inform_by_email', 'main_ark_wallet',
                  'main_ark_tag', 'payout_frequency']

        labels = {
            'main_ark_wallet': _('Ark address'),
            'main_ark_tag': _('Address label'),

        }

