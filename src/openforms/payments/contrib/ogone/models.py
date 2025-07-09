from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from .constants import HashAlgorithm, OgoneEndpoints


class OgoneMerchant(models.Model):
    label = models.CharField(
        _("Label"),
        max_length=255,
        help_text=_("Human readable label"),
    )

    pspid = models.CharField(
        _("PSPID"),
        max_length=255,
        help_text=_("Ogone PSPID"),
    )
    sha_in_passphrase = models.CharField(
        _("SHA-IN passphrase"),
        max_length=255,
        help_text=_("This must match with the Ogone backend"),
    )
    sha_out_passphrase = models.CharField(
        _("SHA-OUT passphrase"),
        max_length=255,
        help_text=_("This must match with the Ogone backend"),
    )
    hash_algorithm = models.CharField(
        _("Hash algorithm"),
        choices=HashAlgorithm.choices,
        max_length=8,
        help_text=_("This must match with the Ogone backend"),
    )

    endpoint_preset = models.URLField(
        _("Preset endpoint"),
        choices=OgoneEndpoints.choices,
        default=OgoneEndpoints.test,
        help_text=_("Select a common preset endpoint"),
    )
    endpoint_custom = models.URLField(
        _("Custom endpoint"),
        blank=True,
        help_text=_("Optionally override the preset endpoint"),
    )

    def __str__(self):
        return self.label

    def clean(self):
        super().clean()
        if not self.endpoint_custom and not self.endpoint_preset:
            raise ValidationError(
                _("Specify either '{preset}' or '{custom}'").format(
                    preset=_("Preset endpoint"), custom=_("Custom endpoint")
                )
            )

    @property
    def endpoint(self):
        return self.endpoint_custom or self.endpoint_preset
