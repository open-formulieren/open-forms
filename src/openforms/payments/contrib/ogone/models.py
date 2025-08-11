from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel

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

    # Worldline migration fields
    api_key = models.CharField(
        _("API Key"),
        max_length=255,
        blank=True,
        help_text=_(
            "API Key created for the specified PSPID. This value will be used"
            " when upgrading to a Open Forms version supporting the Worldline"
            " payment provider."
        ),
    )
    api_secret = models.CharField(
        _("API Secret"),
        max_length=255,
        blank=True,
        help_text=_(
            "API Secret created for the specified PSPID. This value will be used"
            " when upgrading to a Open Forms version supporting the Worldline"
            " payment provider."
        ),
    )

    def __str__(self):
        return self.label

    @property
    def endpoint(self):
        return self.endpoint_custom or self.endpoint_preset


# Worldline migration model
class OgoneWebhookConfiguration(SingletonModel):
    webhook_key_id = models.CharField(_("Webhook Key ID"), max_length=255, default="")
    webhook_key_secret = models.CharField(
        _("Webhook Key Secret"), max_length=255, default=""
    )

    def __str__(self):
        return self.webhook_key_id
