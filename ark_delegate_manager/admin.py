from django.contrib import admin

# Register your models here.
from .models import EarlyAdopterAddressException, BlacklistedAddress, Setting, PaymentLock

admin.site.register(EarlyAdopterAddressException)
admin.site.register(BlacklistedAddress)
admin.site.register(Setting)
admin.site.register(PaymentLock)

