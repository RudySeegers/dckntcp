from django.contrib import admin

# Register your models here.
from .models import EarlyAdopterAddressException, BlacklistedAddress, Setting, CronLock, DutchDelegateStatus

admin.site.register(EarlyAdopterAddressException)
admin.site.register(BlacklistedAddress)
admin.site.register(Setting)
admin.site.register(CronLock)
admin.site.register(DutchDelegateStatus)
