from digid_eherkenning.oidc.models.base import BaseConfig
from mozilla_django_oidc_db.views import OIDCInit

from openforms.contrib.auth_oidc.views import OIDCAuthenticationCallbackView

from .models import (
    OFDigiDConfig,
    OFDigiDMachtigenConfig,
    OFEHerkenningBewindvoeringConfig,
    OFEHerkenningConfig,
    OFEIDASCompanyConfig,
    OFEIDASConfig,
)


def init_view(config_class: type[BaseConfig]):
    def view(request, options, *args, **kwargs):
        oidc_init = OIDCInit.as_view(
            config_class=config_class,
            options=options,
            allow_next_from_query=False,
        )
        return oidc_init(request, *args, **kwargs)

    return view


digid_init = init_view(config_class=OFDigiDConfig)
digid_machtigen_init = init_view(config_class=OFDigiDMachtigenConfig)
eherkenning_init = init_view(config_class=OFEHerkenningConfig)
eherkenning_bewindvoering_init = init_view(
    config_class=OFEHerkenningBewindvoeringConfig
)
eidas_init = init_view(config_class=OFEIDASConfig)
eidas_company_init = init_view(config_class=OFEIDASCompanyConfig)

callback_view = OIDCAuthenticationCallbackView.as_view()
