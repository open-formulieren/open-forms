from dataclasses import dataclass, field

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
    wmts_tile_layers = "wmtsTileLayers", _("WMTS-tile layers")
    yivi_attribute_groups = "yiviAttributeGroups", _("Yivi attribute groups")
    theme = "theme", _("Theme")
    category = "category", _("Category")


@dataclass(slots=True)
class FormExportOptions:
    remove_sensitive_content: bool = True
    form_configuration: list[FormConfigurationOptions] = field(
        default_factory=lambda: [
            FormConfigurationOptions.registration_backends,
            FormConfigurationOptions.prefill,
            FormConfigurationOptions.payment_backend,
            FormConfigurationOptions.auth_backends,
        ]
    )
    additional_form_configuration: list[AdditionalFormConfigurationOptions] = field(
        default_factory=list
    )
