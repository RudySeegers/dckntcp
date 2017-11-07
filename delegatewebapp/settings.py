import os
from decouple import config, Csv
import dj_database_url

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

#Used for token generation to verify wallet ownership
VERIFICATION_KEY = config('VERIFICATION_KEY')

#used for payouts
PASSPHRASE = config('PASSPHRASE')

#delegate_params
DELEGATE_PARAMS = {
    'ADDRESS': config('DELEGATE_ADDRESS'),
    'PUBKEY': config('DELEGATE_PUBKEY'),
    'SECRET': PASSPHRASE
}

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

#Arknode connection params
ARKNODE_PARAMS = {
    'HOST': config('ARKNODE_HOST'),
    'DATABASE': config('ARKNODE_DB'),
    'USER': config('ARKNODE_USER'),
    'PASSWORD': config('ARKNODE_PASSWORD'),
}


ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())


DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL')
    )
}
# Application definition

INSTALLED_APPS = [
    # django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # third-party apps
    'crispy_forms',
    'django_extensions',
    'widget_tweaks',
    'django_cron'
    # my apps
    'home',
    'console',
    'api',
    'ark_delegate_manager',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'delegatewebapp.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'home/templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
CRISPY_TEMPLATE_PACK = 'bootstrap4'
WSGI_APPLICATION = 'delegatewebapp.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases


ACCOUNT_ACTIVATION_DAYS = 7

# LOGIN_REDIRECT_URL = '/home'

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Amsterdam'

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = '/static/'

ROOT_PATH = os.path.dirname(__file__)

STATICFILES_DIRS = [os.path.join(ROOT_PATH, 'static')]
STATIC_ROOT = "/var/www/dutchdelegate.nl/static/"

LOGIN_REDIRECT_URL = '/home'

EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'dutchdelegate@gmail.com'
EMAIL_HOST_PASSWORD = '*9aw3k^r&V6Gc#gryXSQwY&g@Yw@xr!yvySFbDrfExAGpE*K77'
EMAIL_PORT = 587

RAVEN_CONFIG = {
    'dsn': 'https://28bb33619731412192e45a738c4a98ca:ee7da28b1fc34b95a8a91365558ffb4a@sentry.io/235432',
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'root': {
        'level': 'WARNING',
        'handlers': ['sentry'],
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s '
                      '%(process)d %(thread)d %(message)s'
        },
    },
    'handlers': {
        'sentry': {
            'level': 'ERROR', # To capture more than ERROR, change to WARNING, INFO, etc.
            'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
            'tags': {'custom-tag': 'x'},
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'django.db.backends': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': False,
        },
        'raven': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'sentry.errors': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
    'ark_delegate_manager': {
            'level': 'ERROR',
            'handlers': ['sentry'],
            'propagate': False
        },
    },
}

CRON_CLASSES = [
    "ark_delegate_manager.cron.UpdateVotePool",
    "ark_delegate_manager.cron.RunPayments",
    "ark_delegate_manager.cron.VerifyReceivingArkAddresses",
    "ark_delegate_manager.cron.UpdateDutchDelegateStatus",

]