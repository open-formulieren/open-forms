from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from solo.admin import SingletonModelAdmin

from .models import HaalCentraalConfig


@admin.register(HaalCentraalConfig)
class HaalCentraalConfigAdmin(SingletonModelAdmin):
    fieldsets = (
        (
            _("BRP Personen Bevragen"),
            {"fields": ("brp_personen_service", "brp_personen_version")},
        ),
    )
    autocomplete_fields = ("brp_personen_service",)
