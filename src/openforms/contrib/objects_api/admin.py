from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import ObjectsAPIGroupConfig


@admin.register(ObjectsAPIGroupConfig)
class ObjectsAPIGroupConfigAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "identifier",
        "objects_service",
        "objecttypes_service",
        "drc_service",
        "catalogi_service",
    )
    list_select_related = (
        "objects_service",
        "objecttypes_service",
        "drc_service",
        "catalogi_service",
    )
    search_fields = (
        "name",
        "identifier",
    )
    raw_id_fields = (
        "objects_service",
        "objecttypes_service",
        "drc_service",
        "catalogi_service",
    )
    prepopulated_fields = {"identifier": ["name"]}
    ordering = (
        "id",
        "name",
    )
    fieldsets = [
        (None, {"fields": ["name", "identifier"]}),
        (
            _("Services"),
            {
                "fields": [
                    "objects_service",
                    "objecttypes_service",
                    "drc_service",
                    "catalogi_service",
                ]
            },
        ),
        (
            _("Default values"),
            {
                "fields": [
                    "organisatie_rsin",
                ]
            },
        ),
    ]
