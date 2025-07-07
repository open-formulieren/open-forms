from typing import Sequence

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from digid_eherkenning.oidc.admin import (
    ATTRIBUTES_MAPPING_TITLE,
    COMMON_FIELDSETS,
    admin_modelform_factory,
)
from solo.admin import SingletonModelAdmin

from openforms.contrib.auth_oidc.admin import OIDCConfigForm

from .models import AttributeGroup, YiviOpenIDConnectConfig


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
class YiviOpenIDConnectConfigAdmin(SingletonModelAdmin):
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
