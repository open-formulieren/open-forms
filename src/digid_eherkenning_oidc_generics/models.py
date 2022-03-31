from django.db import models
from django.utils.functional import classproperty
from django.utils.translation import gettext_lazy as _

from django_better_admin_arrayfield.models.fields import ArrayField
from mozilla_django_oidc_db.models import CachingMixin, OpenIDConnectConfigBase

from openforms.authentication.constants import AuthAttribute

from .digid_settings import DIGID_CUSTOM_OIDC_DB_PREFIX
from .eherkenning_settings import EHERKENNING_CUSTOM_OIDC_DB_PREFIX


def get_default_scopes_bsn():
    """
    Returns the default scopes to request for OpenID Connect logins
    """
    return ["openid", AuthAttribute.bsn]


def get_default_scopes_kvk():
    """
    Returns the default scopes to request for OpenID Connect logins
    """
    return ["openid", AuthAttribute.kvk]


class OpenIDConnectBaseConfig(CachingMixin, OpenIDConnectConfigBase):
    """
    Configuration for DigiD authentication via OpenID connect
    """

    oidc_op_logout_endpoint = models.URLField(
        _("Logout endpoint"),
        max_length=1000,
        help_text=_("URL of your OpenID Connect provider logout endpoint"),
        blank=True,
    )

    # Keycloak specific config
    oidc_keycloak_idp_hint = models.CharField(
        _("Keycloak Identity Provider hint"),
        max_length=1000,
        help_text=_(
            "Specific for Keycloak: parameter that indicates which identity provider "
            "should be used (therefore skipping the Keycloak login screen)."
        ),
        blank=True,
    )

    class Meta:
        verbose_name = _("OpenID Connect configuration")
        abstract = True


class OpenIDConnectPublicConfig(OpenIDConnectBaseConfig):
    """
    Configuration for DigiD authentication via OpenID connect
    """

    identifier_claim_name = models.CharField(
        _("BSN claim name"),
        max_length=100,
        help_text=_("The name of the claim in which the BSN of the user is stored"),
        default=AuthAttribute.bsn,
    )
    oidc_rp_scopes_list = ArrayField(
        verbose_name=_("OpenID Connect scopes"),
        base_field=models.CharField(_("OpenID Connect scope"), max_length=50),
        default=get_default_scopes_bsn,
        blank=True,
        help_text=_(
            "OpenID Connect scopes that are requested during login. "
            "These scopes are hardcoded and must be supported by the identity provider"
        ),
    )
    vertegenwoordigde_claim_name = models.CharField(
        verbose_name=_("vertegenwoordigde claim name"),
        default="aanvrager.bsn",
        max_length=50,
        help_text=_(
            "Name of the claim in which the BSN of the person being represented is stored"
        ),
    )
    gemachtigde_claim_name = models.CharField(
        verbose_name=_("gemachtigde claim name"),
        default="gemachtigde.bsn",
        max_length=50,
        help_text=_(
            "Name of the claim in which the BSN of the person representing someone else is stored"
        ),
    )

    @classproperty
    def custom_oidc_db_prefix(cls):
        return DIGID_CUSTOM_OIDC_DB_PREFIX

    class Meta:
        verbose_name = _("OpenID Connect configuration for DigiD")


class OpenIDConnectEHerkenningConfig(OpenIDConnectBaseConfig):
    """
    Configuration for eHerkenning authentication via OpenID connect
    """

    identifier_claim_name = models.CharField(
        _("KVK claim name"),
        max_length=100,
        help_text=_("The name of the claim in which the KVK of the user is stored"),
        default=AuthAttribute.kvk,
    )
    oidc_rp_scopes_list = ArrayField(
        verbose_name=_("OpenID Connect scopes"),
        base_field=models.CharField(_("OpenID Connect scope"), max_length=50),
        default=get_default_scopes_kvk,
        blank=True,
        help_text=_(
            "OpenID Connect scopes that are requested during login. "
            "These scopes are hardcoded and must be supported by the identity provider"
        ),
    )

    @classproperty
    def custom_oidc_db_prefix(cls):
        return EHERKENNING_CUSTOM_OIDC_DB_PREFIX

    class Meta:
        verbose_name = _("OpenID Connect configuration for eHerkenning")
