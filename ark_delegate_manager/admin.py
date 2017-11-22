from django.contrib import admin

# Register your models here.
from .models import EarlyAdopterExceptions, Blacklist, Settings

admin.site.register(EarlyAdopterExceptions)
admin.site.register(Blacklist)
admin.site.register(Settings)

