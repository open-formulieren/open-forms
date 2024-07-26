from django.db import models
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen
from zgw_consumers.constants import APITypes

from openforms.template.validators import DjangoTemplateValidator
from openforms.utils.validators import validate_rsin


def get_content_text() -> str:
    return render_to_string("registrations/contrib/zgw_apis/content_json.txt").strip()


# Remove this model when migrations get squashed:
class ZgwConfig(SingletonModel):
    """
    global configuration and defaults
    """

    def __init__(self, *args, **kwargs) -> None:
        raise RuntimeError(
            f"{self.__class__.__name__} is scheduled for removal and shouldn't be instanciated."
        )  # pragma: nocover

    default_zgw_api_group = models.ForeignKey(
        to="ZGWApiGroupConfig",
        on_delete=models.PROTECT,
        verbose_name=_("default ZGW API set."),
        help_text=_("Which set of ZGW APIs should be used as default."),
        null=True,
    )

    class Meta:
        verbose_name = _("ZGW API's configuration")


class ZGWApiGroupConfig(models.Model):
    name = models.CharField(
        _("name"),
        max_length=255,
        help_text=_("A recognisable name for this set of ZGW APIs."),
        unique=True,
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
    # Overridable defaults
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
