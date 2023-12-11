import logging
from typing import TYPE_CHECKING, Any, Dict

from django.template.defaultfilters import date as date_filter
from django.urls import reverse
from django.utils import translation

from openforms.appointments.models import AppointmentInfo
from openforms.config.models import GlobalConfiguration
from openforms.utils.urls import build_absolute_uri
from openforms.variables.utils import get_variables_for_context

if TYPE_CHECKING:
    from openforms.submissions.models import Submission  # pragma: nocover


logger = logging.getLogger(__name__)


def get_confirmation_email_templates(submission: "Submission") -> tuple[str, str]:
    with translation.override(submission.language_code):
        config = GlobalConfiguration.get_solo()
        assert isinstance(config, GlobalConfiguration)
        if not hasattr(submission.form, "confirmation_email_template"):
            return config.confirmation_email_subject, config.confirmation_email_content

        subject_template = (
            submission.form.confirmation_email_template.subject
            or config.confirmation_email_subject
        )
        content_template = (
            submission.form.confirmation_email_template.content
            or config.confirmation_email_content
        )

        return (subject_template, content_template)


def get_confirmation_email_context_data(submission: "Submission") -> Dict[str, Any]:
    with translation.override(submission.language_code):
        context = {
            # use private variables that can't be accessed in the template data, so that
            # template designers can't call the .delete method, for example. Variables
            # starting with underscores are blocked by the Django template engine.
            "_submission": submission,
            "_form": submission.form,  # should be the same as self.form
            # TODO: this should use the :func:`openforms.formio.service.format_value`
            # but be keyed by component.key instead of the label, which
            # submission.get_printable_data did.
            **get_variables_for_context(submission),
            "public_reference": submission.public_registration_reference,
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
