from typing import Sequence

from django import forms
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from digid_eherkenning.oidc.admin import (
    ATTRIBUTES_MAPPING_TITLE,
    COMMON_FIELDSETS,
    admin_modelform_factory,
)
from mozilla_django_oidc_db.forms import OpenIDConnectConfigForm
from solo.admin import SingletonModelAdmin

from openforms.forms.models import Form

from .constants import PLUGIN_ID
from .models import AttributeGroup, YiviOpenIDConnectConfig
from .plugin import YiviOIDCAuthentication


class OIDCConfigForm(OpenIDConnectConfigForm):
    """
    Custom form class to block backend disabling if any form uses it.
    """

    def clean_enabled(self):
        """
        Scan the (live) forms to see if any might be using this backend.
        Disabling a backend while it is being used as a plugin on a live form would
        break this form, so we warn the users for this.
        """
        enabled = self.cleaned_data["enabled"]
        # Nothing to do if it is being or stays enabled
        if enabled:
            return enabled

        forms_with_backend = Form.objects.live().filter(
            auth_backends__backend__exact=PLUGIN_ID,
        )
        if forms_with_backend.exists():
            raise forms.ValidationError(
                _(
                    "{plugin_identifier} is selected as authentication backend "
                    "for one or more forms, please remove this backend from these "
                    "forms before disabling this authentication backend."
                ).format(plugin_identifier=YiviOIDCAuthentication.verbose_name)
            )
        return enabled


def yivi_fieldsets_factory(
    bsn_claim_mapping_fields: Sequence[str],
    kvk_claim_mapping_fields: Sequence[str],
    pseudo_claim_mapping_fields: Sequence[str],
):
    """
    A custom Yivi implementation for applying the shared fieldsets configuration with the
    model-specific overrides.
    This Yivi specific implementation replaces the ATTRIBUTES_MAPPING_TITLE with separate
    BSN, KVK and pseudo mappings. Adding more overview and structure to the Yivi
    configuration view.
    """

    # @TODO define proper json schema once the mozilla_django_oidc_db rework has landed
    _fieldsets = {}
    for key, value in COMMON_FIELDSETS.items():
        if key is ATTRIBUTES_MAPPING_TITLE:
            _fieldsets[_("Attributes to extract from bsn claims")] = {
                "fields": tuple(bsn_claim_mapping_fields)
            }
            _fieldsets[_("Attributes to extract from kvk claims")] = {
                "fields": tuple(kvk_claim_mapping_fields)
            }
            _fieldsets[_("Attributes to extract from pseudo (anonymous) claims")] = {
                "fields": tuple(pseudo_claim_mapping_fields)
            }
        else:
            # Any other fieldset is just copied
            _fieldsets[key] = value

    return tuple((label, config) for label, config in _fieldsets.items())


@admin.register(YiviOpenIDConnectConfig)
class DigiDConfigAdmin(SingletonModelAdmin):
    form = admin_modelform_factory(YiviOpenIDConnectConfig, form=OIDCConfigForm)
    fieldsets = yivi_fieldsets_factory(
        bsn_claim_mapping_fields=[
            "bsn_claim",
            "bsn_loa_claim",
            "bsn_default_loa",
            "bsn_loa_value_mapping",
        ],
        kvk_claim_mapping_fields=[
            "kvk_claim",
            "kvk_loa_claim",
            "kvk_default_loa",
            "kvk_loa_value_mapping",
        ],
        pseudo_claim_mapping_fields=[
            "pseudo_claim",
        ],
    )


@admin.register(AttributeGroup)
class AttributeGroupAdmin(admin.ModelAdmin):
    fields = [
        "name",
        "description",
        "attributes",
    ]
    list_display = [
        "name",
        "description",
        "attributes",
    ]
