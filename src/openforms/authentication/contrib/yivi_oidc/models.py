from copy import deepcopy

from django.db import models
from django.utils.functional import classproperty
from django.utils.translation import gettext_lazy as _

from digid_eherkenning.choices import AssuranceLevels, DigiDAssuranceLevels
from digid_eherkenning.oidc.models.base import LOA_MAPPING_SCHEMA, BaseConfig
from django_jsonform.models.fields import ArrayField, JSONField
from mozilla_django_oidc_db.fields import ClaimField, ClaimFieldDefault


def get_callback_view(self):
    from .views import callback_view

    return callback_view


def get_default_scopes_yivi():
    """
    Returns the default scopes to request for OpenID Connect logins for Yivi.
    """
    return ["openid"]


def get_loa_schema(choices_cls: type[models.TextChoices]):
    new_schema = deepcopy(LOA_MAPPING_SCHEMA)
    new_schema["items"]["properties"]["to"]["choices"] = [
        {"value": val, "title": label} for val, label in choices_cls.choices
    ]
    return new_schema


class YiviOpenIDConnectConfig(BaseConfig):
    get_callback_view = get_callback_view
    of_oidcdb_required_claims = []

    oidc_rp_scopes_list = ArrayField(
        verbose_name=_("OpenID Connect scopes"),
        base_field=models.CharField(_("OpenID Connect scope"), max_length=50),
        default=get_default_scopes_yivi,
        blank=True,
        help_text=_("OpenID Connect scopes that are requested during login."),
    )

    bsn_claim = ClaimField(
        verbose_name=_("bsn claim"),
        default=ClaimFieldDefault("bsn"),
        help_text=_("Name of the claim holding the authenticated user's BSN."),
    )
    bsn_loa_claim = ClaimField(
        verbose_name=_("LoA claim"),
        default=None,
        help_text=_(
            "Name of the claim holding the level of assurance. If left empty, it is "
            "assumed there is no LOA claim and the configured fallback value will be "
            "used."
        ),
        null=True,
        blank=True,
    )
    bsn_default_loa = models.CharField(
        _("default LOA"),
        max_length=100,
        blank=True,
        choices=DigiDAssuranceLevels.choices,
        help_text=_(
            "Fallback level of assurance, in case no claim value could be extracted."
        ),
    )
    bsn_loa_value_mapping = JSONField(
        _("loa mapping"),
        schema=get_loa_schema(DigiDAssuranceLevels),
        default=list,
        blank=True,
        help_text=_(
            "Level of assurance claim value mappings. Useful if the values in the LOA "
            "claim are proprietary, so you can translate them into their standardized "
            "identifiers."
        ),
    )

    kvk_claim = ClaimField(
        verbose_name=_("KVK claim"),
        default=ClaimFieldDefault("kvk"),
        help_text=_(
            "Name of the claim holding the KVK identifier of the authenticated company."
        ),
    )
    kvk_loa_claim = ClaimField(
        verbose_name=_("LoA claim"),
        default=None,
        help_text=_(
            "Name of the claim holding the level of assurance. If left empty, it is "
            "assumed there is no LOA claim and the configured fallback value will be "
            "used."
        ),
        null=True,
        blank=True,
    )
    kvk_default_loa = models.CharField(
        _("default LOA"),
        max_length=100,
        blank=True,
        choices=AssuranceLevels.choices,
        help_text=_(
            "Fallback level of assurance, in case no claim value could be extracted."
        ),
    )
    kvk_loa_value_mapping = JSONField(
        _("loa mapping"),
        schema=get_loa_schema(AssuranceLevels),
        default=list,
        blank=True,
        help_text=_(
            "Level of assurance claim value mappings. Useful if the values in the LOA "
            "claim are proprietary, so you can translate them into their standardized "
            "identifiers."
        ),
    )

    pseudo_claim = ClaimField(
        verbose_name=_("pseudo identifier claim"),
        default=ClaimFieldDefault("pbdf.sidn-pbdf.irma.pseudonym"),
        help_text=_(
            "Name of the claim holding the (opaque) identifier of the user. "
            "This claim will be used when the pseudo authentication option is used, or "
            "when the plugin is set to anonymous authentication "
            "(when no authentication options are selected)."
        ),
    )

    CLAIMS_CONFIGURATION = (
        # For bsn auth
        {"field": "bsn_claim", "required": False},
        # For kvk auth
        {"field": "kvk_claim", "required": False},
        # For anonymous/pseudo auth
        {"field": "pseudo_claim", "required": False},
    )

    class Meta:
        verbose_name = _("Yivi (OIDC)")

    @classproperty
    def oidc_authentication_callback_url(cls) -> str:
        return "oidc_authentication_callback"


class AttributeGroup(models.Model):
    name = models.CharField(
        _("group name"),
        max_length=100,
        unique=True,
        help_text=_(
            "A human-readable name for the group of attributes, used in the form "
            "configuration."
        ),
    )
    description = models.CharField(
        _("group description"),
        max_length=200,
        help_text=_(
            "A longer human-readable description for the group of attributes, used in "
            "the form configuration."
        ),
    )
    attributes = ArrayField(
        base_field=models.CharField(
            _("attribute"),
            max_length=100,
            blank=True,
        ),
        default=list,
        verbose_name=_("attributes"),
        blank=True,
        help_text=_(
            "List of attributes that will be requested from the user. The user can "
            "choose whether to grant access to all these attributes, or none. If you "
            "want individually optional attributes, you should define them as separate "
            "attribute groups."
        ),
    )

    class Meta:
        verbose_name = _("yivi attribute group")
        verbose_name_plural = _("yivi attribute groups")
