"""
Test the submission reference extraction behaviour, independent from the plugin.
"""
from django.test import TestCase

from rest_framework import serializers

from openforms.forms.models import Form
from openforms.submissions.tests.factories import SubmissionFactory

from ..base import BasePlugin
from ..registry import Registry
from ..service import NoSubmissionReference, extract_submission_reference
from .utils import patch_registry

# Set up a registry with plugins for the tests

register = Registry()

model_field = Form._meta.get_field("registration_backend")


@register("plugin1")
class Plugin1(BasePlugin):
    configuration_options = serializers.Serializer

    def register_submission(self, submission, options):
        pass

    def get_reference_from_result(self, result) -> str:
        return result.get("reference")


@register("plugin2")
class Plugin2(BasePlugin):
    configuration_options = serializers.Serializer

    def register_submission(self, submission, options):
        pass

    def get_reference_from_result(self, result: dict) -> str:
        return str(result["reference"])


# Define the actual test cases


class NoExtractableSubmissionReferenceTests(TestCase):
    def test_submission_without_registration_backend(self):
        submission = SubmissionFactory.create(form__registration_backend="")

        with self.assertRaises(NoSubmissionReference):
            extract_submission_reference(submission)

    def test_submission_not_completed(self):
        submission = SubmissionFactory.create(
            completed=False, form__registration_backend="plugin1"
        )

        with patch_registry(model_field, register):
            with self.assertRaises(NoSubmissionReference):
                extract_submission_reference(submission)

    def test_submission_registration_not_completed(self):
        submissions = [
            SubmissionFactory.create(
                registration_failed=True, form__registration_backend="plugin1"
            ),
            SubmissionFactory.create(
                registration_pending=True, form__registration_backend="plugin1"
            ),
            SubmissionFactory.create(
                registration_in_progress=True, form__registration_backend="plugin1"
            ),
        ]

        with patch_registry(model_field, register):
            for submission in submissions:
                with self.subTest(registration_status=submission.registration_status):
                    with self.assertRaises(NoSubmissionReference):
                        extract_submission_reference(submission)

    def test_submission_registered_but_no_registration_result(self):
        submission = SubmissionFactory.create(
            registration_success=True,
            registration_result={},
            form__registration_backend="plugin1",
        )

        with patch_registry(model_field, register):
            with self.assertRaises(NoSubmissionReference):
                extract_submission_reference(submission)


class ExtractableSubmissionReferenceTests(TestCase):
    def test_completed_submission_without_result_serializer(self):
        submission = SubmissionFactory.create(
            registration_success=True,
            registration_result={"reference": "some-unique-reference"},
            form__registration_backend="plugin1",
        )

        with patch_registry(model_field, register):
            reference = extract_submission_reference(submission)

        self.assertEqual(reference, "some-unique-reference")

    def test_completed_but_extraction_errors(self):
        submission = SubmissionFactory.create(
            registration_success=True,
            registration_result={"foo": "bar"},
            form__registration_backend="plugin2",
        )

        with patch_registry(model_field, register):
            with self.assertRaises(NoSubmissionReference):
                extract_submission_reference(submission)
