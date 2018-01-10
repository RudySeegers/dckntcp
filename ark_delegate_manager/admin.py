from django.contrib import admin

# Register your models here.
from .models import Setting, CronLock, DutchDelegateStatus, CustomAddressExceptions

admin.site.register(Setting)
admin.site.register(CronLock)
admin.site.register(DutchDelegateStatus)
admin.site.register(CustomAddressExceptions)