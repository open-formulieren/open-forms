from django.db import models
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel

from openforms.template.validators import DjangoTemplateValidator


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

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        verbose_name = _("Objects API configuration")


class ObjectsAPIRegistrationData(models.Model):  # noqa: DJ008
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


class ObjectsAPISubmissionAttachment(models.Model):  # noqa: DJ008
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
