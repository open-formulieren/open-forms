from django.db import models
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.constants import APITypes

from openforms.template.validators import DjangoTemplateValidator
from openforms.utils.validators import RSINValidator, validate_rsin


def get_content_text() -> str:
    return render_to_string(
        "registrations/contrib/objects_api/content_json.txt"
    ).strip()


def get_payment_status_update_text() -> str:
    return render_to_string(
        "registrations/contrib/objects_api/payment_status_update_json.txt"
    ).strip()


class ObjectsAPIConfig(SingletonModel):
    """
    global configuration and defaults
    """

    productaanvraag_type = models.CharField(
        _("Productaanvraag type"),
        help_text=_(
            "Description of the 'ProductAanvraag' type. This value is saved in the 'type' attribute of the 'ProductAanvraag'."
        ),
        blank=True,
        max_length=255,
    )
    content_json = models.TextField(
        _("JSON content template"),
        validators=[
            DjangoTemplateValidator(
                backend="openforms.template.openforms_backend",
            ),
        ],
        blank=False,
        default=get_content_text,
        help_text=_(
            "This template is evaluated with the submission data and the resulting JSON is sent to the objects API."
        ),
    )
    payment_status_update_json = models.TextField(
        _("payment status update JSON template"),
        validators=[
            DjangoTemplateValidator(
                backend="openforms.template.openforms_backend",
            ),
        ],
        blank=False,
        default=get_payment_status_update_text,
        help_text=_(
            "This template is evaluated with the submission data and the resulting JSON is sent to the objects API "
            "with a PATCH to update the payment field."
        ),
    )

    class Meta:
        verbose_name = _("Objects API configuration")


# no catalogus specified, requires both RSIN and domain to be unspecified
_CATALOGUE_NOT_SET = models.Q(catalogue_domain="", catalogue_rsin="")
# catalogus specified, requires both RSIN and domain to be set
_CATALOGUE_SET = ~models.Q(catalogue_domain="") & ~models.Q(catalogue_rsin="")


class ObjectsAPIGroupConfig(models.Model):
    # TODO OF 3.0: remove `null=True` from the service fields
    name = models.CharField(
        _("name"),
        max_length=255,
        help_text=_("A recognisable name for this set of Objects APIs."),
    )
    objects_service = models.ForeignKey(
        "zgw_consumers.Service",
        verbose_name=_("Objects API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.orc},
        null=True,
        related_name="+",
    )
    objecttypes_service = models.ForeignKey(
        "zgw_consumers.Service",
        verbose_name=_("Objecttypes API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.orc},
        null=True,
        related_name="+",
    )
    drc_service = models.ForeignKey(
        "zgw_consumers.Service",
        verbose_name=_("Documenten API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.drc},
        null=True,
        related_name="+",
    )
    catalogi_service = models.ForeignKey(
        "zgw_consumers.Service",
        verbose_name=_("Catalogi API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.ztc},
        null=True,
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
    # DeprecationWarning: remove in OF 3.0
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

    def clean(self) -> None:
        # circular imports otherwise between client/models/validators
        from .validators import (
            validate_catalogue_reference,
            validate_document_type_references,
        )

        super().clean()

        catalogus = validate_catalogue_reference(self)
        if catalogus is not None:
            validate_document_type_references(self, catalogus)

    def apply_defaults_to(self, options) -> None:
        options.setdefault("version", 1)
        options.setdefault(
            "informatieobjecttype_submission_report",
            self.informatieobjecttype_submission_report,
        )
        options.setdefault(
            "informatieobjecttype_submission_csv",
            self.informatieobjecttype_submission_csv,
        )
        options.setdefault(
            "informatieobjecttype_attachment", self.informatieobjecttype_attachment
        )
        options.setdefault("organisatie_rsin", self.organisatie_rsin)

        # now, normalize the catalogue information and associated document types
        has_catalogue_override = (catalogue := options.get("catalogue")) is not None
        if not has_catalogue_override and self.catalogue_domain:
            # domain implies RSIN is set
            catalogue = {"domain": self.catalogue_domain, "rsin": self.catalogue_rsin}
        options.setdefault("catalogue", catalogue)

        # if we don't have a catalogue override, we can just pick the first non-empty
        # document reference
        for opt in (
            "iot_submission_report",
            "iot_submission_csv",
            "iot_attachment",
        ):
            default_value = getattr(self, opt)
            match options.get(opt):
                # if there's a catalogue override, do not use fallback document
                # description
                case "" | None if has_catalogue_override:
                    pass
                # if there's no catalogue override, use the fallback value, which *may*
                # be an empty string too (in this case, the missing key is normalized)
                case "" | None if not has_catalogue_override:
                    options[opt] = default_value
                # if there's a non-empty override, leave it untouched
                case str(some_val) if len(some_val) > 0:
                    pass


class ObjectsAPIRegistrationData(models.Model):
    """Holds the temporary data available when registering a submission to the Objects API.

    When starting the submission registration, this model is first populated. The Objects API
    registration variables can then safely make use of this model to provide their data.
    """

    submission = models.OneToOneField(
        "submissions.Submission",
        on_delete=models.CASCADE,
        verbose_name=_("submission"),
        help_text=_("The submission linked to the registration data."),
        related_name="objects_api_registration_data",
    )
    pdf_url = models.URLField(
        _("pdf url"),
        help_text=_("The PDF URL of the document on the Documents API."),
        blank=True,
    )
    csv_url = models.URLField(
        _("csv url"),
        help_text=_("The CSV URL of the document on the Documents API."),
        blank=True,
    )


class ObjectsAPISubmissionAttachment(models.Model):
    """A utility model to link a submission file attachment with the Documents API URL."""

    submission_file_attachment = models.ForeignKey(
        "submissions.SubmissionFileAttachment",
        on_delete=models.CASCADE,
        verbose_name=_("submission file attachment"),
        help_text=_("The submission file attachment."),
    )

    document_url = models.URLField(
        _("document_url"),
        help_text=_(
            "The URL of the submission attachment registered in the Documents API."
        ),
    )
