from django.contrib import admin

# Register your models here.
import relay_manager.models

admin.site.register(relay_manager.models.RelayNodes)
