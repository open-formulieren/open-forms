from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import ZGWApiGroupConfig


@admin.register(ZGWApiGroupConfig)
class ZGWApiGroupConfigAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "identifier",
        "zrc_service",
        "drc_service",
        "ztc_service",
        "use_generated_zaaknummer",
    )
    list_select_related = ("zrc_service", "drc_service", "ztc_service")
    search_fields = (
        "name",
        "identifier",
    )
    raw_id_fields = ("zrc_service", "drc_service", "ztc_service")
    prepopulated_fields = {"identifier": ["name"]}
    ordering = ("name",)

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "identifier",
                    "use_generated_zaaknummer",
                )
            },
        ),
        (
            _("Services"),
            {
                "fields": (
                    "zrc_service",
                    "drc_service",
                    "ztc_service",
                ),
            },
        ),
        (
            _("Catalogue"),
            {
                "description": _(
                    "Specify the catalogue in the selected catalogi API service where "
                    "the case and document types are defined."
                ),
                "fields": ("catalogue_domain", "catalogue_rsin"),
            },
        ),
        (
            _("Default values"),
            {
                "fields": (
                    "organisatie_rsin",
                    "zaak_vertrouwelijkheidaanduiding",
                    "doc_vertrouwelijkheidaanduiding",
                    "auteur",
                ),
            },
        ),
        (
            _("Objects API integration"),
            {
                "fields": ("content_json",),
                "classes": ("collapse",),
            },
        ),
    )
