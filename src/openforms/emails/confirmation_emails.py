import logging
from typing import TYPE_CHECKING, Any, Dict, Tuple

from django.template import Context, Template
from django.template.defaultfilters import date as date_filter
from django.urls import reverse

from openforms.appointments.models import AppointmentInfo
from openforms.config.models import GlobalConfiguration
from openforms.forms.constants import ConfirmationEmailOptions
from openforms.utils.urls import build_absolute_uri

from .exceptions import SkipConfirmationEmail

if TYPE_CHECKING:
    from openforms.submissions.models import Submission


logger = logging.getLogger(__name__)


def get_confirmation_email_templates(submission: "Submission") -> Tuple[str, str]:
    template_option = submission.form.confirmation_email_option
    if template_option == ConfirmationEmailOptions.no_email:
        raise SkipConfirmationEmail("Confirmation e-mail sending is disabled.")

    if template_option == ConfirmationEmailOptions.form_specific_email:
        email_template = submission.form.confirmation_email_template
        return (
            email_template.subject,
            email_template.content,
        )

    if template_option == ConfirmationEmailOptions.global_email:
        config = GlobalConfiguration.get_solo()
        return (
            config.confirmation_email_subject,
            config.confirmation_email_content,
        )

    raise ValueError(f"Unexpected option '{template_option}'")  # noqa


def get_confirmation_email_context_data(submission: "Submission") -> Dict[str, Any]:
    context = {
        # use private variables that can't be accessed in the template data, so that
        # template designers can't call the .delete method, for example. Variables
        # starting with underscores are blocked by the Django template engine.
        "_submission": submission,
        "_form": submission.form,  # should be the same as self.form
        **submission.data,
        "public_reference": submission.public_registration_reference,
        "form_name": submission.form.name,
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
        context["payment_price"] = str(submission.form.product.price)

    try:
        context["_appointment_id"] = submission.appointment_info.appointment_id
    except AppointmentInfo.DoesNotExist:
        pass

    return context


def render_confirmation_email_template(
    template: str, context: dict, **extra_context: Any
) -> str:
    render_context = {**context, **extra_context}
    rendered_content = Template(template).render(Context(render_context))
    return rendered_content
