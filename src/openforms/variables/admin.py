from django.contrib import admin

from .models import ServiceFetchConfiguration


@admin.register(ServiceFetchConfiguration)
class ServiceFetchConfigurationAdmin(admin.ModelAdmin):
    raw_id_fields = [
        "service",
    ]
    list_display = [
        "service",
        "path",
    ]
    list_filter = [
        "service",
    ]
