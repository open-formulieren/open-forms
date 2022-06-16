from datetime import datetime

from django.core.management import BaseCommand
from django.db import transaction
from django.db.models import Prefetch, Q
from django.utils import timezone

from glom import glom
from rest_framework.exceptions import ValidationError

from openforms.forms.models import Form, FormStep
from openforms.submissions.attachments import attach_uploads_to_submission_step
from openforms.submissions.models import Submission

WINDOW_START = datetime(2022, 6, 13, 16, 0, 0).replace(tzinfo=timezone.utc)


def get_affected_submissions():
    # check which forms are relevant
    affected_forms = []
    form_steps = FormStep.objects.select_related("form_definition")
    for form in Form.objects.prefetch_related(
        Prefetch("formstep_set", queryset=form_steps)
    ):
        for component in form.iter_components(recursive=True):
            if component.get("type") == "file":
                affected_forms.append(form)
                break

    potentially_affected_submissions = Submission.objects.filter(
        form__in=affected_forms
    ).exclude(completed_on__lt=WINDOW_START)

    return potentially_affected_submissions


def get_ref(submission):
    return submission.public_registration_reference or "(missing reference)"


class Command(BaseCommand):
    help = "Check if a partial DB restore is needed."

    @transaction.atomic()
    def handle(self, **options):
        potentially_affected_submissions = get_affected_submissions()
        self.stdout.write(
            f"Checking {potentially_affected_submissions.count()} potentially affected submission(s)..."
        )

        affected_submissions = set()

        for submission in potentially_affected_submissions:
            for submission_step in submission.submissionstep_set.all():
                try:
                    results = attach_uploads_to_submission_step(submission_step)
                    if any(created for (_, created) in results):
                        affected_submissions.add(submission)
                except ValidationError as exc:
                    self.stderr.write(
                        f"Submission {get_ref(submission)} with ID {submission.id} has invalid file uploads. Errors: {exc}"
                    )

        if not affected_submissions:
            self.stdout.write("No submissions were affected.")
        else:
            self.stdout.write(
                f"{len(affected_submissions)} submission(s) were affected:"
            )
            for submission in sorted(
                affected_submissions, key=lambda sub: sub.created_on
            ):
                self.stdout.write(f"  {get_ref(submission)}, ID: {submission.id}")
