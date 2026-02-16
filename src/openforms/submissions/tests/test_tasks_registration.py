from unittest.mock import patch

from django.test import TestCase

from freezegun import freeze_time

from ...config.models import GlobalConfiguration
from ..public_references import generate_unique_submission_reference
from .factories import SubmissionFactory


class ObtainSubmissionReferenceTests(TestCase):
    def test_generate_public_reference_seeded_on_pk(self):
        """
        test that the generated reference is idempotent and with pk as a seed value
        """
        submission = SubmissionFactory.create()
        reference = generate_unique_submission_reference(submission)

        with self.subTest("check idempotency"):
            for _ in range(5):  # just some number of repetitions
                regenerated_reference = generate_unique_submission_reference(submission)

                self.assertEqual(reference, regenerated_reference)

        with self.subTest("check pk as seed value"):
            another_submission = SubmissionFactory.create()
            another_reference = generate_unique_submission_reference(another_submission)

            self.assertNotEqual(reference, another_reference)

    @freeze_time("2026-01-01")
    def test_generate_public_reference_with_different_templates(self):
        submission = SubmissionFactory.create()

        # get random sequence first
        with patch(
            "openforms.submissions.public_references.GlobalConfiguration.get_solo",
            return_value=GlobalConfiguration(public_reference_template="{uid}"),
        ):
            uid = generate_unique_submission_reference(submission)

            self.assertEqual(len(uid), 6)

        # assert public reference for different templates
        template_reference_mapping = {
            "OF-{uid}": f"OF-{uid}",
            "NL-{year}-{uid}": f"NL-2026-{uid}",
            "{uid}/xyz": f"{uid}/xyz",
        }
        for template, expected_reference in template_reference_mapping.items():
            with self.subTest(template):
                with patch(
                    "openforms.submissions.public_references.GlobalConfiguration.get_solo",
                    return_value=GlobalConfiguration(
                        public_reference_template=template
                    ),
                ):
                    reference = generate_unique_submission_reference(submission)

                self.assertEqual(reference, expected_reference)

    def test_generate_public_reference_with_different_alphabet(self):
        submission = SubmissionFactory.create()

        with patch(
            "openforms.submissions.public_references.GlobalConfiguration.get_solo",
            return_value=GlobalConfiguration(
                public_reference_alphabet="ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
            ),
        ):
            reference1 = generate_unique_submission_reference(submission)

        with patch(
            "openforms.submissions.public_references.GlobalConfiguration.get_solo",
            return_value=GlobalConfiguration(
                public_reference_alphabet="69SRQPAXEWMZB8LNY4GFU7THVDJ523KC"
            ),
        ):
            reference2 = generate_unique_submission_reference(submission)

        self.assertNotEqual(reference1, reference2)
