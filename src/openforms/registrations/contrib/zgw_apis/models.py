from django.db import models
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen
from zgw_consumers.constants import APITypes

from openforms.template.validators import DjangoTemplateValidator
from openforms.utils.validators import RSINValidator, validate_rsin, validate_uppercase


def get_content_text() -> str:
    return render_to_string("registrations/contrib/zgw_apis/content_json.txt").strip()


# Remove this model when migrations get squashed:
class ZgwConfig(SingletonModel):
    """
    global configuration and defaults
    """

    BLOCK_USAGE: bool = True

    def __init__(self, *args, **kwargs) -> None:  # pragma: nocover
        if self.BLOCK_USAGE:
            raise RuntimeError(
                f"{self.__class__.__name__} is scheduled for removal and shouldn't "
                "be instantiated."
            )
        super().__init__(*args, **kwargs)

    default_zgw_api_group = models.ForeignKey(
        to="ZGWApiGroupConfig",
        on_delete=models.PROTECT,
        verbose_name=_("default ZGW API set."),
        help_text=_("Which set of ZGW APIs should be used as default."),
        null=True,
    )

    class Meta:
        verbose_name = _("ZGW API's configuration")


# no catalogus specified, requires both RSIN and domain to be unspecified
_CATALOGUE_NOT_SET = models.Q(catalogue_domain="", catalogue_rsin="")
# catalogus specified, requires both RSIN and domain to be set
_CATALOGUE_SET = ~models.Q(catalogue_domain="") & ~models.Q(catalogue_rsin="")


class ZGWApiGroupConfig(models.Model):
    name = models.CharField(
        _("name"),
        max_length=255,
        help_text=_("A recognisable name for this set of ZGW APIs."),
    )
    zrc_service = models.ForeignKey(
        "zgw_consumers.Service",
        verbose_name=_("Zaken API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.zrc},
        related_name="zgwset_zrc_config",
        null=True,
    )
    drc_service = models.ForeignKey(
        "zgw_consumers.Service",
        verbose_name=_("Documenten API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.drc},
        related_name="zgwset_drc_config",
        null=True,
    )
    ztc_service = models.ForeignKey(
        "zgw_consumers.Service",
        verbose_name=_("Catalogi API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.ztc},
        related_name="zgwset_ztc_config",
        null=True,
    )

    #
    # Overridable defaults
    #
    catalogue_domain = models.CharField(
        _("catalogus domain"),
        # blank because: opt-in to new config pattern & may be specified on form-level
        # options instead of here.
        blank=True,
        max_length=5,
        help_text=_(
            "The 'domein' attribute for the Catalogus resource in the Catalogi API."
        ),
        validators=[validate_uppercase],
    )
    catalogue_rsin = models.CharField(
        _("catalogus RSIN"),
        # blank because: opt-in to new config pattern & may be specified on form-level
        # options instead of here.
        blank=True,
        max_length=9,
        help_text=_(
            "The 'rsin' attribute for the Catalogus resource in the Catalogi API."
        ),
        validators=[RSINValidator()],
    )

    organisatie_rsin = models.CharField(
        _("organisation RSIN"),
        max_length=9,
        blank=True,
        validators=[validate_rsin],
        help_text=_("Default RSIN of organization, which creates the ZAAK"),
    )
    zaak_vertrouwelijkheidaanduiding = models.CharField(
        _("vertrouwelijkheidaanduiding zaak"),
        max_length=24,
        choices=VertrouwelijkheidsAanduidingen.choices,
        blank=True,
        help_text=_(
            "Indication of the level to which extend the ZAAK is meant to be public. "
            "Can be overridden in the Registration tab of a given form."
        ),
    )
    doc_vertrouwelijkheidaanduiding = models.CharField(
        _("vertrouwelijkheidaanduiding document"),
        max_length=24,
        choices=VertrouwelijkheidsAanduidingen.choices,
        blank=True,
        help_text=_(
            "Indication of the level to which extend the document associated with the "
            "ZAAK is meant to be public. Can be overridden in the file upload "
            "component of a given form."
        ),
    )
    auteur = models.CharField(
        _("auteur"),
        max_length=200,
        default="Aanvrager",
    )

    # Objects API
    content_json = models.TextField(
        _("objects API - JSON content template"),
        validators=[
            DjangoTemplateValidator(
                backend="openforms.template.openforms_backend",
            ),
        ],
        blank=True,
        default=get_content_text,
        help_text=_(
            "This template is evaluated with the submission data and the resulting JSON is sent to the objects API."
        ),
    )

    class Meta:
        verbose_name = _("ZGW API set")
        verbose_name_plural = _("ZGW API sets")
        constraints = [
            models.CheckConstraint(
                check=_CATALOGUE_NOT_SET | _CATALOGUE_SET,
                name="registrations_zgw_apis_catalogue_composite_key",
                violation_error_message=_(
                    "You must specify both domain and RSIN to uniquely identify a "
                    "catalogue.",
                ),
            ),
        ]

    def __str__(self):
        return self.name

    def apply_defaults_to(self, options):
        options.setdefault("organisatie_rsin", self.organisatie_rsin)
        options.setdefault(
            "zaak_vertrouwelijkheidaanduiding", self.zaak_vertrouwelijkheidaanduiding
        )
        options.setdefault(
            "doc_vertrouwelijkheidaanduiding",
            self.doc_vertrouwelijkheidaanduiding,
        )
        options.setdefault("auteur", self.auteur)

        # Objects API
        if not options.get("content_json", "").strip():
            options["content_json"] = self.content_json
