from django.contrib import admin

# Register your models here.
from .models import EarlyAdopterExceptions, DutchDelegateStatus

admin.site.register(EarlyAdopterExceptions)
admin.site.register(DutchDelegateStatus)
