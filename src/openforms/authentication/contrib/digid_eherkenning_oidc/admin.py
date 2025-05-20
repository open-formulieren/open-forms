from django.contrib import admin

from digid_eherkenning.oidc.admin import (
    DigiDConfigAdmin as _DigiDConfigAdmin,
    DigiDMachtigenConfigAdmin as _DigiDMachtigenConfigAdmin,
    EHerkenningBewindvoeringConfigAdmin as _EHerkenningBewindvoeringConfigAdmin,
    EHerkenningConfigAdmin as _EHerkenningConfigAdmin,
    admin_modelform_factory,
    fieldsets_factory,
)
from digid_eherkenning.oidc.models import (
    DigiDConfig,
    DigiDMachtigenConfig,
    EHerkenningBewindvoeringConfig,
    EHerkenningConfig,
)
from solo.admin import SingletonModelAdmin

from openforms.contrib.auth_oidc.admin import OIDCConfigForm

from .models import (
    OFDigiDConfig,
    OFDigiDMachtigenConfig,
    OFEHerkenningBewindvoeringConfig,
    OFEHerkenningConfig,
    OFEIDASConfig,
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


@admin.register(OFEIDASConfig)
class EIDASConfigAdmin(SingletonModelAdmin):
    """
    Configuration for eIDAS authentication via OpenID connect.
    """

    form = admin_modelform_factory(OFEIDASConfig, form=OIDCConfigForm)
    fieldsets = fieldsets_factory(
        claim_mapping_fields=[
            "person_identifier_claim",
            "person_identifier_type_claim",
            "first_name_claim",
            "family_name_claim",
            "date_of_birth_claim",
            "company_identifier_claim",
            "company_name_claim",
            "mandate_service_id_claim",
            "loa_claim",
            "default_loa",
            "loa_value_mapping",
        ]
    )
