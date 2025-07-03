from django import forms
from django.utils.translation import gettext_lazy as _

from mozilla_django_oidc_db.forms import OpenIDConnectConfigForm

from openforms.forms.models import Form

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
            auth_backends__backend__exact=plugin.identifier,
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
