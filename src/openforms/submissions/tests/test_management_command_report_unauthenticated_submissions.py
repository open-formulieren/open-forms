from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from .factories import SubmissionFactory


class CommandTests(TestCase):
    def test_no_problematic_submissions(self):
        SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__authentication_backends=[],
            form__formstep__form_definition__login_required=False,
        )
        SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__authentication_backends=["demo"],
            form__formstep__form_definition__login_required=False,
        )
        SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__authentication_backends=["demo"],
            form__formstep__form_definition__login_required=False,
            auth_info__plugin="demo",
        )
        SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__authentication_backends=["demo"],
            form__formstep__form_definition__login_required=True,
            auth_info__plugin="demo",
            auth_info__value="123456782",
        )
        stdout, stderr = StringIO(), StringIO()

        call_command(
            "report_unauthenticated_submissions",
            stdout=stdout,
            stderr=stderr,
            no_color=True,
        )

        stdout.seek(0)
        stderr.seek(0)

        self.assertEqual(stderr.read(), "")
        self.assertEqual(stdout.read(), "No problematic submissions found.\n")

    def test_with_problematic_submissions(self):
        SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__authentication_backends=[],
            form__formstep__form_definition__login_required=False,
        )
        SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__authentication_backends=["demo"],
            form__formstep__form_definition__login_required=False,
        )
        sub3 = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__authentication_backends=["demo"],
            form__formstep__form_definition__login_required=True,
        )
        SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__authentication_backends=["demo"],
            form__formstep__form_definition__login_required=True,
            auth_info__plugin="demo",
            auth_info__value="123456782",
        )
        stdout, stderr = StringIO(), StringIO()

        call_command(
            "report_unauthenticated_submissions",
            stdout=stdout,
            stderr=stderr,
            no_color=True,
        )

        stdout.seek(0)
        stderr.seek(0)

        self.assertEqual(stderr.read(), "")
        self.assertEqual(
            stdout.read(),
            (
                "Found 1 problematic submission(s):\n"
                f"- ID: {sub3.id} (UUID: {sub3.uuid})\n"
            ),
        )
