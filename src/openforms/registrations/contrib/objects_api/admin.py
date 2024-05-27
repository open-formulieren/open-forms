from django.contrib import admin

from solo.admin import SingletonModelAdmin

from .models import ObjectsAPIConfig, ObjectsAPIGroupConfig


@admin.register(ObjectsAPIConfig)
class ObjectsAPIConfigAdmin(SingletonModelAdmin):
    pass


@admin.register(ObjectsAPIGroupConfig)
class ObjectsAPIGroupConfigAdmin(admin.ModelAdmin):
    list_display = (
        "name",
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
    search_fields = ("name",)
    raw_id_fields = (
        "objects_service",
        "objecttypes_service",
        "drc_service",
        "catalogi_service",
    )
    ordering = ("name",)
