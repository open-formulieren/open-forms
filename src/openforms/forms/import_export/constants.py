from django.db import models
from django.utils.translation import gettext_lazy as _


class FormConfigurationOptions(models.TextChoices):
    registration_backends = "registrationBackends", _("Registration backends")
    prefill = "prefill", _("Prefill")
    payment_backend = "paymentBackend", _("Payment backend")
    auth_backends = "authBackends", _("Authentication backends")


class AdditionalFormConfigurationOptions(models.TextChoices):
    product = "product", _("Product")
    wms_tile_layers = "wmsTileLayers", _("WMS-tile layers")
    wmts_tile_layers = "wmtsTileLayers", _("Background tile layers")
    yivi_attribute_groups = "yiviAttributeGroups", _("Yivi attribute groups")
