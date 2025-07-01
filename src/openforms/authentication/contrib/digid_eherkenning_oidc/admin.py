from django.contrib import admin

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

from openforms.contrib.auth_oidc.admin import OIDCConfigForm

from .models import (
    OFDigiDConfig,
    OFDigiDMachtigenConfig,
    OFEHerkenningBewindvoeringConfig,
    OFEHerkenningConfig,
)

# unregister the default app admins so we can add in our own behaviour
admin.site.unregister(DigiDMachtigenConfig)
admin.site.unregister(EHerkenningBewindvoeringConfig)
admin.site.unregister(EHerkenningConfig)
admin.site.unregister(DigiDConfig)


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
