import re
from functools import partial

from django.conf import settings
from django.core.mail import send_mail
from django.template import Context, Template
from django.template.loader import get_template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from openforms.config.models import GlobalConfiguration
from openforms.emails.constants import URL_REGEX
from openforms.emails.models import sanitize_urls
from openforms.submissions.models import Submission

from ...exceptions import RegistrationFailed
from ...registry import register
from .config import EmailOptionsSerializer


@register(
    unique_identifier="email",
    name=_("Email registration"),
    configuration_options=EmailOptionsSerializer,
)
def email_submission(submission: Submission, options: dict) -> None:
    submitted_data = submission.get_merged_data()
    config = GlobalConfiguration.get_solo()

    if not submission.completed_on:
        raise RegistrationFailed("Submission should be completed first")

    template = _("Submission details for {} (submitted on {})").format(
        submission.form.name, submission.completed_on.strftime("%H:%M:%S %d-%m-%Y")
    )

    template += """
        <table>
        {% for field, value in submitted_data.items %}
            {{field}}: {{value}}
        {% endfor %}
        </table>
    """

    # render the e-mail body - the template from this model.
    rendered_content = Template(template).render(
        Context({"submitted_data": submitted_data})
    )

    # strip out any hyperlinks that are not in the configured allowlist
    replace_urls = partial(sanitize_urls, config.email_template_netloc_allowlist)
    stripped = re.sub(URL_REGEX, replace_urls, rendered_content)

    default_template = get_template("confirmation_mail.html")
    content = default_template.render({"body": mark_safe(stripped)})

    send_mail(
        _("[Open Forms] {} - submission {}").format(
            submission.form.name, submission.uuid
        ),
        content,
        settings.DEFAULT_FROM_EMAIL,
        options["to_emails"],
        fail_silently=False,
        html_message=content,
    )
