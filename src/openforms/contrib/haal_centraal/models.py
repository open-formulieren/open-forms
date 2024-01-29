"""
Configuration for Haal Centraal APIs
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.constants import APITypes

from .constants import BRPVersions
from .validators import validate_verwerking_header


class HaalCentraalConfigManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.select_related(
            "brp_personen_service",
            "brp_personen_service__client_certificate",
            "brp_personen_service__server_certificate",
        )


class HaalCentraalConfig(SingletonModel):
    """
    Global configuration and defaults.
    """

    brp_personen_service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("BRP Personen Bevragen API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.orc},
        related_name="+",
        null=True,
    )
    brp_personen_version = models.CharField(
        _("BRP Personen Bevragen API version"),
        max_length=30,
        choices=BRPVersions.choices,
        default=BRPVersions.v13,  # TODO: should be change the default to v2?
        help_text=_("The API version provided by the selected service."),
    )
    default_brp_personen_purpose_limitation_header_value = models.CharField(
        _("default BRP Personen purpose limitation header value"),
        max_length=255,
        blank=True,
        help_text=_(
            'The default purpose limitation ("doelbinding") for queries to the BRP Persoon API. '
            "If a more specific value is configured on a form, that value is used instead."
        ),
    )
    default_brp_personen_processing_header_value = models.CharField(
        _("default BRP Personen processing header value"),
        max_length=242,
        blank=True,
        validators=[validate_verwerking_header],
        help_text=_(
            'The default processing ("verwerking") for queries to the BRP Persoon API. '
            "If a more specific value is configured on a form, that value is used instead."
        ),
    )

    objects = HaalCentraalConfigManager()

    class Meta:
        verbose_name = _("Haal Centraal configuration")


class BRPPersonenRequestOptions(models.Model):
    """Form specific options to be used when making requests to the Haal Centraal APIs.

    Each client can make use of this model to customize the request behavior (e.g. adding some headers).
    See :func:`openforms.contrib.haal_centraal.clients.get_brp_client` as an example.
    """

    form = models.OneToOneField(
        "forms.Form",
        verbose_name=_("Form"),
        on_delete=models.CASCADE,
        related_name="brp_personen_request_options",
    )
    brp_personen_purpose_limitation_header_value = models.CharField(
        _("BRP Personen purpose limitation header value"),
        max_length=255,
        blank=True,
        help_text=_(
            'The purpose limitation ("doelbinding") for queries to the BRP Persoon API.'
        ),
    )
    brp_personen_processing_header_value = models.CharField(
        _("BRP Personen processing header value"),
        max_length=242,
        blank=True,
        validators=[validate_verwerking_header],
        help_text=_(
            'The processing ("verwerking") for queries to the BRP Persoon API.'
        ),
    )

    class Meta:
        verbose_name = _("BRP Personen request options")
        verbose_name_plural = _("BRP Personen request options")

    def __str__(self) -> str:
        return _("BRP Request options for form {form_pk}").format(form_pk=self.form.pk)
