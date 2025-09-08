from django.contrib import admin

from import_export.admin import ImportExportModelAdmin

from .models import AttributeGroup
from .resources import AttributeGroupResource


@admin.register(AttributeGroup)
class AttributeGroupAdmin(ImportExportModelAdmin):
    fields = (
        "name",
        "uuid",
        "description",
        "attributes",
    )
    readonly_fields = ("uuid",)
    list_display = (
        "name",
        "uuid",
        "description",
        "attributes",
    )
    search_fields = ("uuid", "name")

    # Import and export options:
    resource_classes = (AttributeGroupResource,)
