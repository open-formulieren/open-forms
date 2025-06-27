from copy import deepcopy

from django.db import models
from django.utils.functional import classproperty
from django.utils.translation import gettext_lazy as _

from digid_eherkenning.choices import AssuranceLevels, DigiDAssuranceLevels
from digid_eherkenning.oidc.models.base import LOA_MAPPING_SCHEMA
from digid_eherkenning.oidc.models.eherkenning import AuthorizeeMixin
from django_jsonform.models.fields import ArrayField, JSONField
from mozilla_django_oidc_db.fields import ClaimField, ClaimFieldDefault
from mozilla_django_oidc_db.models import OpenIDConnectConfigBase


def get_callback_view(self):
    from .views import callback_view

    return callback_view


def attach_loa_choices():
    """
    A custom adaptation of the digid_eherkenning.oidc.models.base default_loa_choices().
    Because Yivi supports bsn OR kvk authentication, we need 2 sets of loa config.
    As default_loa_choices() is designed to handle straight-forward situation where the
    default loa fields are used, we need a custom implementation that can handle multiple
    loa configs.
    """
    simple_loa_choices = (
        ("bsn_default_loa", DigiDAssuranceLevels),
        ("kvk_default_loa", AssuranceLevels),
    )
    value_mapping_loa_choices = (
        ("bsn_loa_value_mapping", DigiDAssuranceLevels),
        ("kvk_loa_value_mapping", AssuranceLevels),
    )

    def decorator(cls: type[OpenIDConnectConfigBase]):
        for field, choice_set in simple_loa_choices:
            # set the choices for the default_loa
            default_loa_field = cls._meta.get_field(field)
            assert isinstance(default_loa_field, models.CharField)
            default_loa_field.choices = choice_set.choices

        for field, choice_set in value_mapping_loa_choices:
            # specify the choices for the JSONField schema
            loa_mapping_field = cls._meta.get_field(field)
            assert isinstance(loa_mapping_field, JSONField)
            new_schema = deepcopy(loa_mapping_field.schema)
            new_schema["items"]["properties"]["to"]["choices"] = [
                {"value": val, "title": label} for val, label in choice_set.choices
            ]
            loa_mapping_field.schema = new_schema

        return cls

    return decorator


def get_default_scopes_yivi():
    """
    Returns the default scopes to request for OpenID Connect logins for Yivi.
    """
    return ["openid"]


@attach_loa_choices()
class YiviOpenIDConnectConfig(AuthorizeeMixin, OpenIDConnectConfigBase):
    class Meta:
        verbose_name = _("Yivi (OIDC)")
        verbose_name_plural = _("Yivi (OIDC)")

    get_callback_view = get_callback_view
    of_oidcdb_required_claims = []

    oidc_rp_scopes_list = ArrayField(
        verbose_name=_("OpenID Connect scopes"),
        base_field=models.CharField(_("OpenID Connect scope"), max_length=50),
        default=get_default_scopes_yivi,
        blank=True,
        help_text=_("OpenID Connect scopes that are requested during login"),
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
        choices=tuple(),  # set dynamically via the default_loa_choices decorator
        help_text=_(
            "Fallback level of assurance, in case no claim value could be extracted."
        ),
    )
    bsn_loa_value_mapping = JSONField(
        _("loa mapping"),
        schema=LOA_MAPPING_SCHEMA,
        default=list,
        blank=True,
        help_text=_(
            "Level of assurance claim value mappings. Useful if the values in the LOA "
            "claim are proprietary, so you can translate them into their standardized "
            "identifiers."
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
        choices=tuple(),  # set dynamically via the default_loa_choices decorator
        help_text=_(
            "Fallback level of assurance, in case no claim value could be extracted."
        ),
    )
    kvk_loa_value_mapping = JSONField(
        _("loa mapping"),
        schema=LOA_MAPPING_SCHEMA,
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
        default=ClaimFieldDefault("sub"),
        help_text=_(
            "Name of the claim holding the (opaque) identifier of the user. "
            "This claim will be used when the plugin is set to anonymous authentication "
            "(when neither bsn or kvk are selected as authentication options)."
        ),
    )

    CLAIMS_CONFIGURATION = (
        # For bsn auth
        {"field": "bsn_claim", "required": False},
        # For kvk auth
        {"field": "identifier_type_claim", "required": False},
        {"field": "legal_subject_claim", "required": False},
        {"field": "acting_subject_claim", "required": False},
        {"field": "branch_number_claim", "required": False},
        # For anonymous/pseudo auth
        {"field": "pseudo_claim", "required": False},
        # General claim
        {"field": "loa_claim", "required": False},
    )

    @classproperty
    def oidc_authentication_callback_url(cls) -> str:
        return "oidc_authentication_callback"


class AttributeGroup(models.Model):
    config = models.ForeignKey(
        YiviOpenIDConnectConfig,
        verbose_name=_("attribute groups"),
        on_delete=models.CASCADE,
        related_name="attribute_groups",
    )
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
            "choose whether to grant all these attributes, or non. If you want "
            "individually optional attributes, you can define them as separate "
            "attribute groups."
        ),
    )

    class Meta:
        verbose_name = _("attribute group")
        verbose_name_plural = _("attribute groups")
