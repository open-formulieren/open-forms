import warnings

from django.conf import settings
from django.utils.functional import classproperty
from django.utils.translation import gettext_lazy as _

from digid_eherkenning.oidc.models import (
    DigiDConfig,
    DigiDMachtigenConfig,
    EHerkenningBewindvoeringConfig,
    EHerkenningConfig,
)


def get_callback_view(self):
    from .views import callback_view

    return callback_view


class OFDigiDConfig(DigiDConfig):
    class Meta:
        proxy = True
        verbose_name = _("DigiD (OIDC)")
        verbose_name_plural = _("DigiD (OIDC)")

    get_callback_view = get_callback_view
    of_oidcdb_required_claims = ["bsn_claim"]

    @classproperty
    def oidc_authentication_callback_url(cls) -> str:  # type: ignore
        if settings.USE_LEGACY_DIGID_EH_OIDC_ENDPOINTS:
            warnings.warn(
                "Legacy DigiD-eHerkenning callback endpoints will be removed in 4.0",
                DeprecationWarning,
            )
            return "digid_oidc:callback"
        return "oidc_authentication_callback"


class OFDigiDMachtigenConfig(DigiDMachtigenConfig):
    class Meta:
        proxy = True
        verbose_name = _("DigiD Machtigen (OIDC)")
        verbose_name_plural = _("DigiD Machtigen (OIDC)")

    get_callback_view = get_callback_view
    of_oidcdb_required_claims = ["representee_bsn_claim", "authorizee_bsn_claim"]

    @classproperty
    def oidc_authentication_callback_url(cls) -> str:  # type: ignore
        if settings.USE_LEGACY_DIGID_EH_OIDC_ENDPOINTS:
            warnings.warn(
                "Legacy DigiD-eHerkenning callback endpoints will be removed in 4.0",
                DeprecationWarning,
            )
            return "digid_machtigen_oidc:callback"
        return "oidc_authentication_callback"


class OFEHerkenningConfig(EHerkenningConfig):
    class Meta:
        proxy = True
        verbose_name = _("eHerkenning (OIDC)")
        verbose_name_plural = _("eHerkenning (OIDC)")

    get_callback_view = get_callback_view
    of_oidcdb_required_claims = ["legal_subject_claim"]

    @classproperty
    def oidc_authentication_callback_url(cls) -> str:  # type: ignore
        if settings.USE_LEGACY_DIGID_EH_OIDC_ENDPOINTS:
            warnings.warn(
                "Legacy DigiD-eHerkenning callback endpoints will be removed in 4.0",
                DeprecationWarning,
            )
            return "eherkenning_oidc:callback"
        return "oidc_authentication_callback"


class OFEHerkenningBewindvoeringConfig(EHerkenningBewindvoeringConfig):
    class Meta:
        proxy = True
        verbose_name = _("eHerkenning bewindvoering (OIDC)")
        verbose_name_plural = _("eHerkenning bewindvoering (OIDC)")

    get_callback_view = get_callback_view
    of_oidcdb_required_claims = ["legal_subject_claim", "representee_claim"]

    @classproperty
    def oidc_authentication_callback_url(cls) -> str:  # type: ignore
        if settings.USE_LEGACY_DIGID_EH_OIDC_ENDPOINTS:
            warnings.warn(
                "Legacy DigiD-eHerkenning callback endpoints will be removed in 4.0",
                DeprecationWarning,
            )
            return "eherkenning_bewindvoering_oidc:callback"
        return "oidc_authentication_callback"
