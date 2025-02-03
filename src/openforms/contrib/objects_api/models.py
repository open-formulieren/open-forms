from django.db import models
from django.utils.translation import gettext_lazy as _

from zgw_consumers.constants import APITypes

from openforms.utils.validators import RSINValidator, validate_rsin

# no catalogus specified, requires both RSIN and domain to be unspecified
_CATALOGUE_NOT_SET = models.Q(catalogue_domain="", catalogue_rsin="")
# catalogus specified, requires both RSIN and domain to be set
_CATALOGUE_SET = ~models.Q(catalogue_domain="") & ~models.Q(catalogue_rsin="")


class ObjectsAPIGroupConfig(models.Model):
    name = models.CharField(
        _("name"),
        max_length=255,
        help_text=_("A recognisable name for this set of Objects APIs."),
    )
    identifier = models.SlugField(
        _("identifier"),
        blank=False,
        null=False,
        unique=True,
        help_text=_("A unique, human-friendly identifier to identify this group."),
    )
    objects_service = models.ForeignKey(
        "zgw_consumers.Service",
        verbose_name=_("Objects API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.orc},
        null=False,
        related_name="+",
    )
    objecttypes_service = models.ForeignKey(
        "zgw_consumers.Service",
        verbose_name=_("Objecttypes API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.orc},
        null=False,
        related_name="+",
    )
    drc_service = models.ForeignKey(
        "zgw_consumers.Service",
        verbose_name=_("Documenten API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.drc},
        null=True,
        blank=True,
        related_name="+",
    )
    catalogi_service = models.ForeignKey(
        "zgw_consumers.Service",
        verbose_name=_("Catalogi API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.ztc},
        null=True,
        blank=True,
        related_name="+",
    )

    #
    # Overridable defaults
    #

    # Specify which catalogus to use to look up document types. See
    # https://catalogi-api.vng.cloud/ for the API specification. A catalogus is uniquely
    # identified by the combination (domein, rsin)
    catalogue_domain = models.CharField(
        _("catalogus domain"),
        # blank because: opt-in to new config pattern & may be specified on form-level
        # options instead of here.
        blank=True,
        max_length=5,
        help_text=_(
            "The 'domein' attribute for the Catalogus resource in the Catalogi API."
        ),
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
        help_text=_("Default RSIN of organization, which creates the INFORMATIEOBJECT"),
    )

    # Replaces informatiobjecttype_submission_report
    iot_submission_report = models.CharField(
        _("submission report document type description"),
        # InformatieObjecttype.omschrijving resource attribute in Catalogi API spec
        max_length=80,
        blank=True,
        help_text=_(
            "Description of the document type in the Catalogi API to be used for the "
            "submission report PDF (i.e. the INFORMATIEOBJECTTYPE.omschrijving "
            "attribute). The appropriate version will automatically be selected based "
            "on the submission timestamp and validity dates of the "
            "document type versions."
        ),
    )
    # Replaces informatiobjecttype_submission_csv
    iot_submission_csv = models.CharField(
        _("submission report CSV document type description"),
        # InformatieObjecttype.omschrijving resource attribute in Catalogi API spec
        max_length=80,
        blank=True,
        help_text=_(
            "Description of the document type in the Catalogi API to be used for the "
            "submission report CSV (i.e. the INFORMATIEOBJECTTYPE.omschrijving "
            "attribute). The appropriate version will automatically be selected based "
            "on the submission timestamp and validity dates of the "
            "document type versions."
        ),
    )
    # Replaces informatiobjecttype_attachment
    iot_attachment = models.CharField(
        _("attachment document type description"),
        # InformatieObjecttype.omschrijving resource attribute in Catalogi API spec
        max_length=80,
        blank=True,
        help_text=_(
            "Description of the document type in the Catalogi API to be used for the "
            "submission attachments (i.e. the INFORMATIEOBJECTTYPE.omschrijving "
            "attribute). The appropriate version will automatically be selected based "
            "on the submission timestamp and validity dates of the "
            "document type versions."
        ),
    )

    # XXX: the URLFields are to be replaced with charfields storing the omschrijving.
    # DeprecationWarning: remove in OF 4.0
    informatieobjecttype_submission_report = models.URLField(
        _("submission report informatieobjecttype"),
        max_length=1000,
        blank=True,
        help_text=_(
            "Default URL that points to the INFORMATIEOBJECTTYPE in the Catalogi API "
            "to be used for the submission report PDF"
        ),
    )
    informatieobjecttype_submission_csv = models.URLField(
        _("submission report CSV informatieobjecttype"),
        max_length=1000,
        blank=True,
        help_text=_(
            "Default URL that points to the INFORMATIEOBJECTTYPE in the Catalogi API "
            "to be used for the submission report CSV"
        ),
    )
    informatieobjecttype_attachment = models.URLField(
        _("attachment informatieobjecttype"),
        max_length=1000,
        blank=True,
        help_text=_(
            "Default URL that points to the INFORMATIEOBJECTTYPE in the Catalogi API "
            "to be used for the submission attachments"
        ),
    )

    class Meta:
        verbose_name = _("Objects API group")
        verbose_name_plural = _("Objects API groups")
        constraints = [
            models.CheckConstraint(
                check=_CATALOGUE_NOT_SET | _CATALOGUE_SET,
                name="catalogue_composite_key",
                violation_error_message=_(
                    "You must specify both domain and RSIN to uniquely identify a "
                    "catalogue.",
                ),
            ),
            models.CheckConstraint(
                check=(
                    models.Q(iot_submission_report="")
                    | (~models.Q(iot_submission_report="") & _CATALOGUE_SET)
                ),
                name="iot_report_requires_catalogue",
                violation_error_message=_(
                    "You must specify a catalogue when specifying the submission "
                    "report PDF document type.",
                ),
            ),
            models.CheckConstraint(
                check=(
                    models.Q(iot_submission_csv="")
                    | (~models.Q(iot_submission_csv="") & _CATALOGUE_SET)
                ),
                name="iot_csv_requires_catalogue",
                violation_error_message=_(
                    "You must specify a catalogue when specifying the submission "
                    "report CSV document type.",
                ),
            ),
            models.CheckConstraint(
                check=(
                    models.Q(iot_attachment="")
                    | (~models.Q(iot_attachment="") & _CATALOGUE_SET)
                ),
                name="iot_attachment_requires_catalogue",
                violation_error_message=_(
                    "You must specify a catalogue when specifying the submission "
                    "attachment document type.",
                ),
            ),
        ]

    def __str__(self) -> str:
        return self.name

    def full_clean(self, *args, **kwargs) -> None:
        # Due to circular imports
        from .validators import (
            validate_catalogue_reference,
            validate_document_type_references,
        )

        super().full_clean(*args, **kwargs)

        catalogus = validate_catalogue_reference(self)
        if catalogus is not None:
            validate_document_type_references(self, catalogus)
