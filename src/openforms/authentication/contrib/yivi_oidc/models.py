from django.db import models
from django.utils.functional import classproperty
from django.utils.translation import gettext_lazy as _

from digid_eherkenning.choices import DigiDAssuranceLevels
from digid_eherkenning.oidc.models import BaseConfig
from digid_eherkenning.oidc.models.base import default_loa_choices
from digid_eherkenning.oidc.models.eherkenning import AuthorizeeMixin
from django_jsonform.models.fields import ArrayField
from mozilla_django_oidc_db.fields import ClaimField, ClaimFieldDefault


def get_callback_view(self):
    from .views import callback_view

    return callback_view


@default_loa_choices(DigiDAssuranceLevels)
class YiviOpenIDConnectConfig(AuthorizeeMixin, BaseConfig):
    class Meta:
        verbose_name = _("Yivi (OIDC)")
        verbose_name_plural = _("Yivi (OIDC)")

    get_callback_view = get_callback_view
    of_oidcdb_required_claims = []

    bsn_claim = ClaimField(
        verbose_name=_("bsn claim"),
        default=ClaimFieldDefault("bsn"),
        help_text=_("Name of the claim holding the authenticated user's BSN."),
    )

    CLAIMS_CONFIGURATION = (
        # For bsn auth
        {"field": "bsn_claim", "required": False},
        # For kvk auth
        {"field": "identifier_type_claim", "required": False},
        {"field": "legal_subject_claim", "required": False},
        {"field": "acting_subject_claim", "required": False},
        {"field": "branch_number_claim", "required": False},
    )

    @classproperty
    def oidc_authentication_callback_url(cls) -> str:
        return "oidc_authentication_callback"


class AvailableScope(models.Model):
    config = models.ForeignKey(
        YiviOpenIDConnectConfig,
        on_delete=models.CASCADE,
        related_name="available_scopes",
    )
    scope = models.CharField(
        _("scope"),
        max_length=100,
        help_text=_("The scope that could be added to authentication requests."),
    )
    description = models.CharField(
        _("scope description"),
        max_length=200,
        help_text=_("A human-readable description of the scope."),
    )
    claims = ArrayField(
        base_field=models.CharField(
            _("claim resulting from the scope"),
            max_length=100,
            blank=True,
        ),
        default=list,
        verbose_name=_("claims resulting from the scope"),
        blank=True,
        help_text=_(
            "List of claims that will be available after authentication, when the scope "
            "is used."
        ),
    )

    class Meta:
        verbose_name = _("available scope")
        verbose_name_plural = _("available scopes")
