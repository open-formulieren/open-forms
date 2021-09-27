from typing import Dict

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.encoding import force_text
from django.utils.translation import gettext_lazy as _

from django_better_admin_arrayfield.models.fields import ArrayField
from solo.models import SingletonModel, get_cache

import mozilla_django_oidc_db.settings as oidc_settings


def get_default_scopes():
    """
    Returns the default scopes to request for OpenID Connect logins
    """
    return ["openid", "email", "profile"]


def get_claim_mapping() -> Dict[str, str]:
    # Map (some) claim names from https://openid.net/specs/openid-connect-core-1_0.html#Claims
    # to corresponding field names on the User model
    return {
        "email": "email",
        "first_name": "given_name",
        "last_name": "family_name",
    }


class OpenIDConnectConfig(SingletonModel):
    """
    Configuration for authentication/authorization via OpenID connect
    """

    enabled = models.BooleanField(
        _("enable"),
        default=False,
        help_text=_(
            "Indicates whether OpenID Connect for authentication/authorization is enabled"
        ),
    )

    oidc_rp_client_id = models.CharField(
        _("OpenID Connect client ID"),
        max_length=1000,
        help_text=_("OpenID Connect client ID provided by the OIDC Provider"),
    )
    oidc_rp_client_secret = models.CharField(
        _("OpenID Connect secret"),
        max_length=1000,
        help_text=_("OpenID Connect secret provided by the OIDC Provider"),
    )
    oidc_rp_sign_algo = models.CharField(
        _("OpenID sign algorithm"),
        max_length=50,
        help_text=_("Algorithm the Identity Provider uses to sign ID tokens"),
        default="HS256",
    )
    oidc_rp_scopes_list = ArrayField(
        verbose_name=_("OpenID Connect scopes"),
        base_field=models.CharField(_("OpenID Connect scope"), max_length=50),
        default=get_default_scopes,
        blank=True,
        help_text=_("OpenID Connect scopes that are requested during login"),
    )

    oidc_op_discovery_endpoint = models.URLField(
        _("Discovery endpoint"),
        max_length=1000,
        help_text=_(
            "URL of your OpenID Connect provider discovery endpoint ending with a slash "
            "(`.well-known/...` will be added automatically). "
            "If this is provided, the remaining endpoints can be omitted, as "
            "they will be derived from this endpoint."
        ),
        blank=True,
    )
    oidc_op_jwks_endpoint = models.URLField(
        _("JSON Web Key Set endpoint"),
        max_length=1000,
        help_text=_(
            "URL of your OpenID Connect provider JSON Web Key Set endpoint. Required if `RS256` is used as signing algorithm"
        ),
        blank=True,
    )
    oidc_op_authorization_endpoint = models.URLField(
        _("Authorization endpoint"),
        max_length=1000,
        help_text=_("URL of your OpenID Connect provider authorization endpoint"),
    )
    oidc_op_token_endpoint = models.URLField(
        _("Token endpoint"),
        max_length=1000,
        help_text=_("URL of your OpenID Connect provider token endpoint"),
    )
    oidc_op_user_endpoint = models.URLField(
        _("User endpoint"),
        max_length=1000,
        help_text=_("URL of your OpenID Connect provider userinfo endpoint"),
    )
    oidc_rp_idp_sign_key = models.CharField(
        _("Sign key"),
        max_length=1000,
        help_text=_(
            "Key the Identity Provider uses to sign ID tokens in the case of an RSA sign algorithm. Should be the signing key in PEM or DER format"
        ),
        blank=True,
    )

    claim_mapping = JSONField(
        _("claim mapping"),
        default=get_claim_mapping,
        help_text=("Mapping from user-model fields to OIDC claims"),
    )
    groups_claim = models.CharField(
        _("groups claim"),
        max_length=50,
        default="roles",
        help_text=_(
            "The name of the OIDC claim that holds the values to map to local user groups."
        ),
    )
    sync_groups = models.BooleanField(
        _("synchronize groups"),
        default=True,
        help_text=_(
            "Synchronize the local user groups with the provided groups. Note that this "
            "means a user is removed from all groups if there is no group claim. "
            "Uncheck to manage groups manually."
        ),
    )
    make_users_staff = models.BooleanField(
        _("make users staff"),
        default=False,
        help_text=_(
            "Users will be flagged as being a staff user automatically. This allows users to login to the admin interface. By default they have no permissions, even if they are staff."
        ),
    )

    class Meta:
        verbose_name = _("OpenID Connect configuration")

    def __str__(self):
        return force_text(self._meta.verbose_name)

    def clean(self):
        super().clean()

        # validate claim mapping
        User = get_user_model()
        for field in self.claim_mapping.keys():
            try:
                User._meta.get_field(field)
            except models.FieldDoesNotExist:
                raise ValidationError(
                    {
                        "claim_mapping": _(
                            "Field {field} does not exist on the user model"
                        ).format(field=field)
                    }
                )

        if User.USERNAME_FIELD in self.claim_mapping:
            raise ValidationError(
                {
                    "claim_mapping": _(
                        "The username field may not be in the claim mapping"
                    ),
                }
            )

    @property
    def oidc_rp_scopes(self):
        """
        Scopes should be formatted as a string with spaces
        """
        return " ".join(self.oidc_rp_scopes_list)

    @classmethod
    def clear_cache(cls):
        cache_name = getattr(
            settings, "OIDC_CACHE", oidc_settings.MOZILLA_DJANGO_OIDC_DB_CACHE
        )
        if cache_name:
            cache = get_cache(cache_name)
            cache_key = cls.get_cache_key()
            cache.delete(cache_key)

    def set_to_cache(self):
        cache_name = getattr(
            settings,
            "MOZILLA_DJANGO_OIDC_DB_CACHE",
            oidc_settings.MOZILLA_DJANGO_OIDC_DB_CACHE,
        )
        if not cache_name:
            return None
        cache = get_cache(cache_name)
        cache_key = self.get_cache_key()
        timeout = getattr(
            settings,
            "MOZILLA_DJANGO_OIDC_DB_CACHE_TIMEOUT",
            oidc_settings.MOZILLA_DJANGO_OIDC_DB_CACHE_TIMEOUT,
        )
        cache.set(cache_key, self, timeout)

    @classmethod
    def get_cache_key(cls):
        prefix = getattr(
            settings,
            "MOZILLA_DJANGO_OIDC_DB_PREFIX",
            oidc_settings.MOZILLA_DJANGO_OIDC_DB_PREFIX,
        )
        return "%s:%s" % (prefix, cls.__name__.lower())

    @classmethod
    def get_solo(cls):
        cache_name = getattr(
            settings,
            "MOZILLA_DJANGO_OIDC_DB_CACHE",
            oidc_settings.MOZILLA_DJANGO_OIDC_DB_CACHE,
        )
        if not cache_name:
            obj, created = cls.objects.get_or_create(pk=cls.singleton_instance_id)
            return obj
        cache = get_cache(cache_name)
        cache_key = cls.get_cache_key()
        obj = cache.get(cache_key)
        if not obj:
            obj, created = cls.objects.get_or_create(pk=cls.singleton_instance_id)
            obj.set_to_cache()
        return obj
