from django import forms
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from digid_eherkenning.oidc.admin import (
    admin_modelform_factory,
    fieldsets_factory,
)
from mozilla_django_oidc_db.forms import OpenIDConnectConfigForm
from solo.admin import SingletonModelAdmin

from openforms.forms.models import Form

from .models import AvailableScope, YiviOpenIDConnectConfig
from .plugin import get_config_to_plugin


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

        # deteermine which plugin ID we need to query for
        plugin = get_config_to_plugin()[self._meta.model]
        forms_with_backend = Form.objects.live().filter(
            authentication_backends__contains=[plugin.identifier]
        )
        if forms_with_backend.exists():
            raise forms.ValidationError(
                _(
                    "{plugin_identifier} is selected as authentication backend "
                    "for one or more forms, please remove this backend from these "
                    "forms before disabling this authentication backend."
                ).format(plugin_identifier=plugin.verbose_name)
            )
        return enabled


class AvailableScopeInline(admin.TabularInline):
    model = AvailableScope
    extra = 1


@admin.register(YiviOpenIDConnectConfig)
class DigiDConfigAdmin(SingletonModelAdmin):
    form = admin_modelform_factory(YiviOpenIDConnectConfig, form=OIDCConfigForm)
    fieldsets = fieldsets_factory(
        claim_mapping_fields=[
            "bsn_claim",
            "identifier_type_claim",
            "legal_subject_claim",
            "branch_number_claim",
            "acting_subject_claim",
            "loa_claim",
            "default_loa",
            "loa_value_mapping",
        ]
    )
    inlines = [AvailableScopeInline]
