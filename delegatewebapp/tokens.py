from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import six
import hashlib
from django.conf import settings


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (six.text_type(user.pk) + six.text_type(timestamp)) + six.text_type(user.is_active)


account_activation_token = AccountActivationTokenGenerator()


def gen_ark_token(user):
    rawtoken = settings.VERIFICATION_KEY + str(user) + 'ark'
    return hashlib.sha256(rawtoken.encode()).hexdigest()


def gen_kapu_token(user):
    rawtoken = settings.VERIFICATION_KEY + str(user) + 'kapu'
    return hashlib.sha256(rawtoken.encode()).hexdigest()


