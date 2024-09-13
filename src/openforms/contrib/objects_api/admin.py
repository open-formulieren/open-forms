from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import ObjectsAPIGroupConfig


@admin.register(ObjectsAPIGroupConfig)
class ObjectsAPIGroupConfigAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "objects_service",
        "objecttypes_service",
        "drc_service",
        "catalogi_service",
        "catalogue_domain",
        "catalogue_rsin",
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
    fieldsets = [
        (None, {"fields": ["name"]}),
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
            _("Catalogue"),
            {
                "description": _(
                    "Specify the catalogue in the selected catalogi API service where "
                    "the document types are defined. If provided, document types will "
                    "also be validated against the catalogue."
                ),
                "fields": ("catalogue_domain", "catalogue_rsin"),
            },
        ),
        (
            _("Default values"),
            {
                "fields": [
                    "iot_submission_report",
                    "iot_submission_csv",
                    "iot_attachment",
                    "organisatie_rsin",
                ]
            },
        ),
        (
            _("Default values (deprecated)"),
            {
                "description": _(
                    "These configuration fields are deprecated - do not use them for "
                    "new configurations."
                ),
                "fields": [
                    "informatieobjecttype_submission_report",
                    "informatieobjecttype_submission_csv",
                    "informatieobjecttype_attachment",
                ],
                "classes": ("collapse",),
            },
        ),
    ]
