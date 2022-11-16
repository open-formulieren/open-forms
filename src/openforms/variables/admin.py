from django.contrib import admin

from .models import ServiceFetchConfiguration


@admin.register(ServiceFetchConfiguration)
class ServiceFetchConfigurationAdmin(admin.ModelAdmin):
    pass
