"""
Management command to render the text email template.
"""
from django.core.management import BaseCommand
from django.template import Context
from django.template.loader import get_template

from openforms.submissions.models import Submission
from openforms.submissions.rendering import Renderer, RenderModes


class Command(BaseCommand):
    help = (
        "Display the submission data as it would be shown in the confirmation email (text)."
        "For HTML, use the development view dev/email/confirmation/<int:submission_id>"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "submission_id",
            type=int,
            help="Submission ID to display the data from.",
        )

    def handle(self, **options):
        submission = Submission.objects.get(id=options["submission_id"])

        renderer = Renderer(
            submission=submission,
            mode=RenderModes.confirmation_email,
            as_html=False,
        )
        name = "emails/templatetags/form_summary.txt"
        context = Context({"renderer": renderer})
        rendered_email = get_template(name).render(context.flatten())
        self.stdout.write(rendered_email, ending="")
