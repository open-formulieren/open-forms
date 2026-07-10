from collections.abc import Callable
from dataclasses import dataclass, field

from django.db import models
from django.utils.translation import gettext_lazy as _

from openforms.typing import JSONObject


class FormConfigurationOptions(models.TextChoices):
    registration_backends = "registrationBackends", _("Registration backends")
    prefill = "prefill", _("Prefill")
    payment_backend = "paymentBackend", _("Payment backend")
    auth_backends = "authBackends", _("Authentication backends")


EXPORT_FORM_CONFIGURATION_CHOICES: list[tuple[str, str]] = [
    choice
    for choice in FormConfigurationOptions.choices
    if choice[0]
    in {
        FormConfigurationOptions.registration_backends,
        FormConfigurationOptions.prefill,
        FormConfigurationOptions.payment_backend,
    }
]


class AdditionalFormConfigurationOptions(models.TextChoices):
    product = "product", _("Product")
    wms_tile_layers = "wmsTileLayers", _("WMS-tile layers")
    wmts_tile_layers = "wmtsTileLayers", _("WMTS-tile layers")
    yivi_attribute_groups = "yiviAttributeGroups", _("Yivi attribute groups")
    theme = "theme", _("Theme")
    category = "category", _("Category")


class ReusableFormDefinitionsOptions(models.TextChoices):
    reuse_existing = "reuseExisting", _("Reuse existing form definitions")
    create_new = "createNew", _("Create all new form definitions")


class LinksToUnknownDomainsOptions(models.TextChoices):
    ignore = "ignore", _("Keep links to unknown domains as-is")
    remove = "remove", _("Remove the links to unknown domains")
    accept = "accept", _("Accept all unknown domains")


@dataclass(slots=True)
class FormExportOptions:
    remove_sensitive_content: bool = True
    form_configuration: list[EXPORT_FORM_CONFIGURATION_CHOICES] = field(
        default_factory=lambda: [
            FormConfigurationOptions.registration_backends,
            FormConfigurationOptions.prefill,
            FormConfigurationOptions.payment_backend,
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
        ]
    )
    reusable_form_definitions: ReusableFormDefinitionsOptions = field(
        default=ReusableFormDefinitionsOptions.create_new,
    )
    links_to_unknown_domains: LinksToUnknownDomainsOptions = field(
        default=LinksToUnknownDomainsOptions.ignore,
    )
    additional_form_configuration: list[AdditionalFormConfigurationOptions] = field(
        default_factory=list
    )


@dataclass(frozen=True)
class AdditionalFormConfigurationCleanup:
    option: AdditionalFormConfigurationOptions
    cleanup: Callable[[JSONObject], None]


@dataclass(frozen=True)
class FormConfigurationCleanup:
    option: FormConfigurationOptions
    cleanup: Callable[[JSONObject], None]
