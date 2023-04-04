from django.contrib import admin

from .models import ServiceFetchConfiguration


@admin.register(ServiceFetchConfiguration)
class ServiceFetchConfigurationAdmin(admin.ModelAdmin):
    raw_id_fields = [
        "service",
    ]
    list_display = [
        "name",
        "service",
        "method",
        "path",
    ]
    list_filter = [
        "service",
    ]
    search_fields = [
        "name",
        "service__api_root",
        "path",
    ]
