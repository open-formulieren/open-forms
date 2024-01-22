from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from solo.admin import SingletonModelAdmin

from .models import BRPPersonenRequestOptions, HaalCentraalConfig


@admin.register(HaalCentraalConfig)
class HaalCentraalConfigAdmin(SingletonModelAdmin):
    fieldsets = (
        (
            _("BRP Personen Bevragen"),
            {
                "fields": (
                    "brp_personen_service",
                    "brp_personen_version",
                    "default_brp_personen_purpose_limitation_header_value",
                    "default_brp_personen_processing_header_value",
                )
            },
        ),
    )
    autocomplete_fields = ("brp_personen_service",)


@admin.register(BRPPersonenRequestOptions)
class BRPPersonenRequestOptionsAdmin(admin.ModelAdmin):
    list_display = (
        "form",
        "brp_personen_purpose_limitation_header_value",
        "brp_personen_processing_header_value",
    )
    list_filter = ("form",)
    search_fields = (
        "brp_personen_purpose_limitation_header_value",
        "brp_personen_processing_header_value",
    )
    raw_id_fields = ("form",)
