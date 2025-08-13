from django import forms
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from mozilla_django_oidc_db.admin import OIDCClientAdmin
from mozilla_django_oidc_db.models import OIDCClient

from openforms.authentication.registry import register as auth_registry
from openforms.forms.models import Form

from .plugin import OIDCAuthentication

# unregister mozilla_django_oidc_db admin so we can add in our own behaviour
admin.site.unregister(OIDCClient)


class OIDCClientForm(forms.ModelForm):
    class Meta:
        model = OIDCClient
        fields = "__all__"  # noqa: DJ007

    def clean_enabled(self) -> bool:
        """
        Scan the (live) forms to see if any might be using this backend.

        Disabling a backend while it is being used as a plugin on a live form would
        break the form, so we warn the users for this.
        """
        enabled = self.cleaned_data["enabled"]
        # Nothing to do if it is being or stays enabled
        if enabled:
            return enabled

        # Find the Auth plugin corresponding to the OIDC
        # client being modified. If it doesn't correspond to any OIDC
        # auth plugin, just return.
        for plugin in auth_registry:
            if not isinstance(plugin, OIDCAuthentication):
                continue
            if plugin.oidc_plugin_identifier == self.instance.identifier:
                matching_plugin = plugin
                break
        else:  # pragma: no cover
            return enabled

        forms_with_backend = Form.objects.live().filter(
            auth_backends__backend__exact=matching_plugin.identifier,
        )
        if forms_with_backend.exists():
            raise forms.ValidationError(
                _(
                    "{plugin_name} is selected as authentication backend "
                    "for one or more forms, please remove this backend from these "
                    "forms before disabling this authentication backend."
                ).format(plugin_name=matching_plugin.verbose_name)
            )
        return enabled


@admin.register(OIDCClient)
class OFOIDCClientAdmin(OIDCClientAdmin):
    form = OIDCClientForm
