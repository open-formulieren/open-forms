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
from .factories import ReferenceHolderFactory
from .utils import patch_registry

register = Registry()

model_field = Form._meta.get_field("registration_backend")


@register("plugin1")
class Plugin(BasePlugin):
    configuration_options = serializers.Serializer

    def register_submission(self, submission, options):
        pass

    def get_reference_from_result(self, result) -> str:
        reference_holder = ReferenceHolderFactory.create()
        return reference_holder.reference


class GenericReferenceExtractionTests(TestCase):
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
