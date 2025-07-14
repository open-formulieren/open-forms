import warnings
from collections.abc import Sequence

from django.conf import settings
from django.db import models
from django.utils.functional import classproperty
from django.utils.translation import gettext_lazy as _

from digid_eherkenning.oidc.models import (
    BaseConfig,
    DigiDConfig,
    DigiDMachtigenConfig,
    EHerkenningBewindvoeringConfig,
    EHerkenningConfig,
)
from digid_eherkenning.oidc.models.base import default_loa_choices
from django_jsonform.models.fields import ArrayField
from mozilla_django_oidc_db.fields import ClaimField, ClaimFieldDefault
from mozilla_django_oidc_db.typing import ClaimPath

from openforms.authentication.contrib.digid_eherkenning_oidc.choices import (
    EIDASAssuranceLevels,
)


def get_callback_view(self):
    from .views import callback_view

    return callback_view


def get_default_scopes_eidas():
    """
    Returns the default scopes to request for OpenID Connect logins for eIDAS.
    """
    return ["openid", "profile"]


def get_default_scopes_eidas_company():
    """
    Returns the default scopes to request for OpenID Connect logins for eIDAS with
    company.
    """
    return ["openid", "profile", "legal"]


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
                stacklevel=2,
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
                stacklevel=2,
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
                stacklevel=2,
            )
            return "eherkenning_oidc:callback"
        return "oidc_authentication_callback"


@default_loa_choices(EIDASAssuranceLevels)
class OFEIDASConfig(BaseConfig):
    legal_subject_identifier_claim = ClaimField(
        verbose_name=_("legal subject identifier claim"),
        default=ClaimFieldDefault("urn:etoegang:1.12:EntityConcernedID:PseudoID"),
        help_text=_(
            "Name of the claim holding the identifier of the authenticated user."
        ),
    )
    legal_subject_identifier_type_claim = ClaimField(
        verbose_name=_("legal subject identifier type claim"),
        default=ClaimFieldDefault("namequalifier"),
        help_text=_(
            "Claim that specifies how the person identifier claim must be interpreted. "
            "The expected claim value is one of: 'bsn', 'pseudo' or 'national_id'."
        ),
    )
    legal_subject_first_name_claim = ClaimField(
        verbose_name=_("legal subject first name claim"),
        default=ClaimFieldDefault("urn:etoegang:1.9:attribute:FirstName"),
        help_text=_("Claim that holds the legal name of the authenticated user."),
    )
    legal_subject_family_name_claim = ClaimField(
        verbose_name=_("legal subject family name claim"),
        default=ClaimFieldDefault("urn:etoegang:1.9:attribute:FamilyName"),
        help_text=_(
            "Claim that holds the legal family name of the authenticated user."
        ),
    )
    legal_subject_date_of_birth_claim = ClaimField(
        verbose_name=_("legal subject date of birth claim"),
        default=ClaimFieldDefault("urn:etoegang:1.9:attribute:DateOfBirth"),
        help_text=_("Claim that holds the legal birthdate of the authenticated user."),
    )

    oidc_rp_scopes_list = ArrayField(
        verbose_name=_("OpenID Connect scopes"),
        base_field=models.CharField(_("OpenID Connect scope"), max_length=50),
        default=get_default_scopes_eidas,
        blank=True,
        help_text=_(
            "OpenID Connect scopes that are requested during login. "
            "These scopes are hardcoded and must be supported by the identity provider."
        ),
    )

    get_callback_view = get_callback_view
    of_oidcdb_required_claims = [
        "legal_subject_identifier_claim",
        "legal_subject_first_name_claim",
        "legal_subject_family_name_claim",
        "legal_subject_date_of_birth_claim",
    ]

    CLAIMS_CONFIGURATION = (
        {"field": "legal_subject_identifier_claim", "required": True},
        {"field": "legal_subject_identifier_type_claim", "required": True},
        {"field": "legal_subject_first_name_claim", "required": True},
        {"field": "legal_subject_family_name_claim", "required": True},
        {"field": "legal_subject_date_of_birth_claim", "required": True},
    )

    class Meta:
        verbose_name = _("eIDAS (OIDC)")

    @property
    def oidcdb_username_claim(self):
        return self.legal_subject_identifier_claim

    @property
    def oidcdb_sensitive_claims(self) -> Sequence[ClaimPath]:
        return [
            self.legal_subject_identifier_claim,
            self.legal_subject_first_name_claim,
            self.legal_subject_family_name_claim,
        ]

    @classproperty
    def oidc_authentication_callback_url(cls) -> str:
        return "oidc_authentication_callback"


@default_loa_choices(EIDASAssuranceLevels)
class OFEIDASCompanyConfig(BaseConfig):
    legal_subject_identifier_claim = ArrayField(
        verbose_name=_("company identifier claim"),
        default=ClaimFieldDefault(
            "urn:etoegang:1.11:EntityConcernedID:eIDASLegalIdentifier"
        ),
        base_field=models.CharField("claim path segment", max_length=100),
        help_text=_(
            "Name of the claim holding the identifier of the authenticated company."
        ),
    )
    legal_subject_name_claim = ArrayField(
        verbose_name=_("company name claim"),
        default=ClaimFieldDefault(
            "urn:etoegang:1.11:attribute-represented:CompanyName"
        ),
        base_field=models.CharField("claim path segment", max_length=100),
        help_text=_("Claim that holds the name of the authenticated company."),
    )

    acting_subject_identifier_claim = ClaimField(
        verbose_name=_("acting subject identifier claim"),
        default=ClaimFieldDefault("urn:etoegang:1.12:EntityConcernedID:PseudoID"),
        help_text=_("Name of the claim holding the identifier of the acting subject."),
    )
    acting_subject_identifier_type_claim = ClaimField(
        verbose_name=_("acting subject identifier type claim"),
        default=ClaimFieldDefault("namequalifier"),
        help_text=_(
            "Claim that specifies how the acting subject identifier claim must be "
            "interpreted. The expected claim value is one of: 'bsn', 'pseudo' or "
            "'national_id'."
        ),
    )
    acting_subject_first_name_claim = ClaimField(
        verbose_name=_("acting subject first name claim"),
        default=ClaimFieldDefault("urn:etoegang:1.9:attribute:FirstName"),
        help_text=_("Claim that holds the legal name of the acting subject."),
    )
    acting_subject_family_name_claim = ClaimField(
        verbose_name=_("acting subject family name claim"),
        default=ClaimFieldDefault("urn:etoegang:1.9:attribute:FamilyName"),
        help_text=_("Claim that holds the legal family name of the acting subject."),
    )
    acting_subject_date_of_birth_claim = ClaimField(
        verbose_name=_("acting subject date of birth claim"),
        default=ClaimFieldDefault("urn:etoegang:1.9:attribute:DateOfBirth"),
        help_text=_("Claim that holds the legal birthdate of the acting subject."),
    )
    mandate_service_id_claim = ClaimField(
        verbose_name=_("service ID claim"),
        default=ClaimFieldDefault("urn:etoegang:core:ServiceID"),
        help_text=_(
            "Name of the claim holding the service ID for which the acting subject "
            "is authorized."
        ),
    )

    oidc_rp_scopes_list = ArrayField(
        verbose_name=_("OpenID Connect scopes"),
        base_field=models.CharField(_("OpenID Connect scope"), max_length=50),
        default=get_default_scopes_eidas_company,
        blank=True,
        help_text=_(
            "OpenID Connect scopes that are requested during login. "
            "These scopes are hardcoded and must be supported by the identity provider."
        ),
    )

    get_callback_view = get_callback_view
    of_oidcdb_required_claims = [
        "legal_subject_identifier_claim",
        "legal_subject_name_claim",
        "acting_subject_identifier_claim",
        "acting_subject_first_name_claim",
        "acting_subject_family_name_claim",
        "acting_subject_date_of_birth_claim",
        "mandate_service_id_claim",
    ]

    CLAIMS_CONFIGURATION = (
        {"field": "legal_subject_identifier_claim", "required": True},
        {"field": "legal_subject_name_claim", "required": True},
        {"field": "acting_subject_identifier_claim", "required": True},
        {"field": "acting_subject_identifier_type_claim", "required": True},
        {"field": "acting_subject_first_name_claim", "required": True},
        {"field": "acting_subject_family_name_claim", "required": True},
        {"field": "acting_subject_date_of_birth_claim", "required": True},
        {"field": "mandate_service_id_claim", "required": True},
    )

    class Meta:
        verbose_name = _("eIDAS for companies (OIDC)")

    @property
    def oidcdb_username_claim(self):
        return self.legal_subject_identifier_claim

    @property
    def oidcdb_sensitive_claims(self) -> Sequence[ClaimPath]:
        return [
            self.legal_subject_identifier_claim,
            self.acting_subject_identifier_claim,
            self.acting_subject_first_name_claim,
            self.acting_subject_family_name_claim,
        ]

    @classproperty
    def oidc_authentication_callback_url(cls) -> str:
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
                stacklevel=2,
            )
            return "eherkenning_bewindvoering_oidc:callback"
        return "oidc_authentication_callback"
