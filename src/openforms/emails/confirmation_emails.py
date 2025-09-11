from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.template.defaultfilters import date as date_filter
from django.urls import reverse
from django.utils import translation

from openforms.appointments.models import AppointmentInfo
from openforms.config.models import GlobalConfiguration
from openforms.utils.urls import build_absolute_uri
from openforms.variables.utils import get_variables_for_context

from .models import ConfirmationEmailTemplate

if TYPE_CHECKING:
    from openforms.submissions.models import Submission  # pragma: nocover


def get_confirmation_email_templates(submission: Submission) -> tuple[str, str]:
    with translation.override(submission.language_code):
        config = GlobalConfiguration.get_solo()
        custom_templates = getattr(submission.form, "confirmation_email_template", None)
        cosign = submission.cosign_state

        match (cosign.is_required, custom_templates):
            # no cosign, definitely no custom templates exist
            case (False, None):
                return (
                    config.confirmation_email_subject,
                    config.confirmation_email_content,
                )

            # no cosign, possibly custom templates exist
            case (False, ConfirmationEmailTemplate()):
                return (
                    custom_templates.subject or config.confirmation_email_subject,
                    custom_templates.content or config.confirmation_email_content,
                )

            # with cosign, definitely no custom templates exist
            case (True, None):
                return (
                    config.cosign_confirmation_email_subject,
                    config.cosign_confirmation_email_content,
                )

            # with cosign, possibly custom templates exist
            case (True, ConfirmationEmailTemplate()):
                return (
                    custom_templates.cosign_subject
                    or config.cosign_confirmation_email_subject,
                    custom_templates.cosign_content
                    or config.cosign_confirmation_email_content,
                )
            case _:  # pragma: no cover
                raise Exception("Unexpected case")


def get_confirmation_email_context_data(submission: Submission) -> dict[str, Any]:
    with translation.override(submission.language_code):
        context = {
            # use private variables that can't be accessed in the template data, so that
            # template designers can't call the .delete method, for example. Variables
            # starting with underscores are blocked by the Django template engine.
            "_submission": submission,
            "_form": submission.form,  # should be the same as self.form
            **get_variables_for_context(submission, is_confirmation_email=True),
            "public_reference": submission.public_registration_reference,
            "registration_completed": submission.is_registered,
            "waiting_on_cosign": submission.cosign_state.is_waiting,
        }

    # use the ``|date`` filter so that the timestamp is first localized to the correct
    # timezone, and then the date is formatted according to the django global setting.
    # This makes date representations consistent across the system.
    context["submission_date"] = date_filter(submission.completed_on)

    if submission.payment_required:
        context["payment_required"] = True
        context["payment_user_has_paid"] = submission.payment_user_has_paid
        context["payment_url"] = build_absolute_uri(
            reverse("payments:link", kwargs={"uuid": submission.uuid})
        )
        context["payment_price"] = submission.price

    try:
        context["_appointment_id"] = submission.appointment_info.appointment_id
    except AppointmentInfo.DoesNotExist:
        pass

    return context
