from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TypedDict

from django.db import models
from django.utils.translation import gettext_lazy as _

from openforms.typing import JSONObject


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


class FormExportOptionsData(TypedDict, total=False):
    remove_sensitive_content: bool
    form_configuration: list[FormConfigurationOptions]
    additional_form_configuration: list[AdditionalFormConfigurationOptions]


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


@dataclass(slots=True)
class FormImportOptions:
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
    reuse_form_definitions: bool = True
    theme: str | None = None
    category: str | None = None


@dataclass(frozen=True)
class AdditionalFormConfigurationCleanup:
    option: AdditionalFormConfigurationOptions
    cleanup: Callable[[JSONObject], None]


@dataclass(frozen=True)
class FormConfigurationCleanup:
    option: FormConfigurationOptions
    cleanup: Callable[[JSONObject], None]
