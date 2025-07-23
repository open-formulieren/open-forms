from django.db import models
from django.utils.translation import gettext_lazy as _

from .constants import WordlineEndpoints


class WorldlineMerchant(models.Model):
    label = models.CharField(
        _("Label"),
        max_length=255,
        help_text=_("Human readable label"),
    )

    pspid = models.CharField(
        _("PSPID"),
        max_length=255,
        help_text=_("Worldline PSPID"),
    )

    api_key = models.CharField(
        _("API Key"),
        max_length=255,
        help_text=_("API Key created for the specified PSPID"),
    )

    api_secret = models.CharField(
        _("API Secret"),
        max_length=255,
        help_text=_("API Secret created for the specified PSPID"),
    )

    endpoint_preset = models.URLField(
        _("Preset endpoint"),
        choices=WordlineEndpoints.choices,
        default=WordlineEndpoints.test,
        help_text=_("Select a common preset endpoint"),
    )
    endpoint_custom = models.URLField(
        _("Custom endpoint"),
        blank=True,
        help_text=_("Optionally override the preset endpoint"),
    )

    def __str__(self):
        return self.label

    @property
    def endpoint(self):
        return self.endpoint_custom or self.endpoint_preset
