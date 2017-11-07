from django import forms
from . models import UserProfile


class UserForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('main_ark_wallet',
                  )
        labels = {'main_ark_wallet': 'Main Ark wallet'}

