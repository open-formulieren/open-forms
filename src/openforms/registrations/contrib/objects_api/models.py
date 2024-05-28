from django.core.exceptions import ValidationError
from django.db import models
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from furl import furl
from solo.models import SingletonModel
from zgw_consumers.constants import APITypes

from openforms.template.validators import DjangoTemplateValidator
from openforms.utils.validators import validate_rsin


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

    objects_service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("Objects API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.orc},
        null=True,
        related_name="+",
    )
    objecttypes_service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("Objecttypes API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.orc},
        null=True,
        related_name="+",
    )
    drc_service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("Documenten API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.drc},
        null=True,
        related_name="+",
    )
    catalogi_service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("Catalogi API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.ztc},
        null=True,
        related_name="+",
    )

    # Overridable defaults
    objecttype = models.URLField(
        _("objecttype"),
        max_length=1000,
        blank=True,
        help_text=_(
            "Default URL of the ProductAanvraag OBJECTTYPE in the Objecttypes API. "
            "The objecttype should have the following three attributes: "
            "1) submission_id; "
            "2) type (the type of productaanvraag); "
            "3) data (the submitted form data)"
        ),
        editable=False,
    )
    objecttype_version = models.IntegerField(
        _("objecttype version"),
        null=True,
        blank=True,
        help_text=_("Default version of the OBJECTTYPE in the Objecttypes API"),
        editable=False,
    )
    productaanvraag_type = models.CharField(
        _("Productaanvraag type"),
        help_text=_(
            "Description of the 'ProductAanvraag' type. This value is saved in the 'type' attribute of the 'ProductAanvraag'."
        ),
        blank=True,
        max_length=255,
    )
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
    organisatie_rsin = models.CharField(
        _("organisation RSIN"),
        max_length=9,
        blank=True,
        validators=[validate_rsin],
        help_text=_("Default RSIN of organization, which creates the INFORMATIEOBJECT"),
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

    def clean(self) -> None:
        super().clean()

        if (
            self.objecttypes_service
            and self.objecttype
            and not furl(self.objecttype).host
            == furl(self.objecttypes_service.api_root).host
        ):
            raise ValidationError(
                {
                    "objecttype": _(
                        "The provided Objecttype is not part of the configured Objecttypes API."
                    )
                },
                code="invalid",
            )

    def apply_defaults_to(self, options):
        options.setdefault("version", 1)
        options.setdefault("objecttype", self.objecttype)
        options.setdefault("objecttype_version", self.objecttype_version)
        options.setdefault("productaanvraag_type", self.productaanvraag_type)
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
        if not options.get("content_json", "").strip():
            options["content_json"] = self.content_json

        if not options.get("payment_status_update_json", "").strip():
            options["payment_status_update_json"] = self.payment_status_update_json

        options.setdefault("auteur", "Aanvrager")


class ObjectsAPIGroupConfig(models.Model):
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

    # Overridable defaults
    objecttype = models.URLField(
        _("objecttype"),
        max_length=1000,
        blank=True,
        help_text=_(
            "Default URL of the ProductAanvraag OBJECTTYPE in the Objecttypes API. "
            "The objecttype should have the following three attributes: "
            "1) submission_id; "
            "2) type (the type of productaanvraag); "
            "3) data (the submitted form data)"
        ),
        editable=False,
    )
    objecttype_version = models.IntegerField(
        _("objecttype version"),
        null=True,
        blank=True,
        help_text=_("Default version of the OBJECTTYPE in the Objecttypes API"),
        editable=False,
    )
    productaanvraag_type = models.CharField(
        _("Productaanvraag type"),
        help_text=_(
            "Description of the 'ProductAanvraag' type. This value is saved in the 'type' attribute of the 'ProductAanvraag'."
        ),
        blank=True,
        max_length=255,
    )
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
    organisatie_rsin = models.CharField(
        _("organisation RSIN"),
        max_length=9,
        blank=True,
        validators=[validate_rsin],
        help_text=_("Default RSIN of organization, which creates the INFORMATIEOBJECT"),
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
        verbose_name = _("Objects API group")
        verbose_name_plural = _("Objects API groups")

    def __str__(self) -> str:
        return self.name

    def clean(self) -> None:
        super().clean()

        if (
            self.objecttypes_service
            and self.objecttype
            and not furl(self.objecttype).host
            == furl(self.objecttypes_service.api_root).host
        ):
            raise ValidationError(
                {
                    "objecttype": _(
                        "The provided Objecttype is not part of the configured Objecttypes API."
                    )
                },
                code="invalid",
            )

    def apply_defaults_to(self, options):
        options.setdefault("version", 1)
        options.setdefault("objecttype", self.objecttype)
        options.setdefault("objecttype_version", self.objecttype_version)
        options.setdefault("productaanvraag_type", self.productaanvraag_type)
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
        if not options.get("content_json", "").strip():
            options["content_json"] = self.content_json

        if not options.get("payment_status_update_json", "").strip():
            options["payment_status_update_json"] = self.payment_status_update_json

        options.setdefault("auteur", "Aanvrager")


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
