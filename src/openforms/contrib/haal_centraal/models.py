"""
Configuration for Haal Centraal APIs
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.constants import APITypes

from .constants import BRPVersions


class HaalCentraalConfigManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.select_related(
            "brp_personen_service",
            "brp_personen_service__client_certificate",
            "brp_personen_service__server_certificate",
        )


class HaalCentraalConfig(SingletonModel):
    """
    Global configuration and defaults.
    """

    brp_personen_service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("BRP Personen Bevragen API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.orc},
        related_name="+",
        null=True,
    )
    brp_personen_version = models.CharField(
        _("BRP Personen Bevragen API version"),
        max_length=30,
        choices=BRPVersions.choices,
        default=BRPVersions.v13,  # TODO: should be change the default to v2?
        help_text=_("The API version provided by the selected service."),
    )

    objects = HaalCentraalConfigManager()

    class Meta:
        verbose_name = _("Haal Centraal configuration")
