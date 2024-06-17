from django import forms
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from digid_eherkenning.oidc.admin import (
    DigiDConfigAdmin as _DigiDConfigAdmin,
    DigiDMachtigenConfigAdmin as _DigiDMachtigenConfigAdmin,
    EHerkenningBewindvoeringConfigAdmin as _EHerkenningBewindvoeringConfigAdmin,
    EHerkenningConfigAdmin as _EHerkenningConfigAdmin,
    admin_modelform_factory,
)
from digid_eherkenning.oidc.models import (
    DigiDConfig,
    DigiDMachtigenConfig,
    EHerkenningBewindvoeringConfig,
    EHerkenningConfig,
)
from mozilla_django_oidc_db.forms import OpenIDConnectConfigForm

from openforms.forms.models import Form

from .models import (
    OFDigiDConfig,
    OFDigiDMachtigenConfig,
    OFEHerkenningBewindvoeringConfig,
    OFEHerkenningConfig,
)
from .plugin import get_config_to_plugin

# unregister the default app admins so we can add in our own behaviour
admin.site.unregister(DigiDMachtigenConfig)
admin.site.unregister(EHerkenningBewindvoeringConfig)
admin.site.unregister(EHerkenningConfig)
admin.site.unregister(DigiDConfig)


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


@admin.register(OFDigiDConfig)
class DigiDConfigAdmin(_DigiDConfigAdmin):
    form = admin_modelform_factory(OFDigiDConfig, form=OIDCConfigForm)


@admin.register(OFDigiDMachtigenConfig)
class DigiDMachtigenConfigAdmin(_DigiDMachtigenConfigAdmin):
    form = admin_modelform_factory(OFDigiDMachtigenConfig, form=OIDCConfigForm)


@admin.register(OFEHerkenningConfig)
class EHerkenningConfigAdmin(_EHerkenningConfigAdmin):
    form = admin_modelform_factory(OFEHerkenningConfig, form=OIDCConfigForm)


@admin.register(OFEHerkenningBewindvoeringConfig)
class EHerkenningBewindvoeringConfigAdmin(_EHerkenningBewindvoeringConfigAdmin):
    form = admin_modelform_factory(
        OFEHerkenningBewindvoeringConfig, form=OIDCConfigForm
    )
