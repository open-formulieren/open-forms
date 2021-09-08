from unittest.mock import patch

from django.test import TestCase, TransactionTestCase

from ..tasks.registration import (
    generate_unique_submission_reference,
    obtain_submission_reference,
)
from .factories import SubmissionFactory


class ObtainSubmissionReferenceTests(TestCase):
    @patch(
        "openforms.submissions.tasks.registration.generate_unique_submission_reference"
    )
    def test_source_reference_from_registration_result(self, mock_generate):
        """
        Check that a reference is sourced from the registration result if it's available.
        """
        submission = SubmissionFactory.create(
            form__registration_backend="zgw-create-zaak",
            completed=True,
            registration_success=True,
            registration_result={"zaak": {"identificatie": "AEY64"}},
        )

        obtain_submission_reference(submission.id)

        submission.refresh_from_db()
        self.assertEqual(submission.public_registration_reference, "AEY64")
        mock_generate.assert_not_called()

    @patch(
        "openforms.submissions.tasks.registration.generate_unique_submission_reference",
        wraps=generate_unique_submission_reference,
    )
    def test_fallback_to_local_reference_generation(self, mock_generate):
        """
        Assert that there is always a reference generated.

        Check that if sourcing the reference from the registration result fails, a
        local reference is generated.
        """
        submission = SubmissionFactory.create(
            form__registration_backend="zgw-create-zaak",
            completed=True,
            registration_success=True,
            registration_result={"bad": {"result": "shape"}},
        )

        with patch(
            "openforms.submissions.tasks.registration.get_random_string",
            return_value="UNIQUE",
        ):
            obtain_submission_reference(submission.id)

        submission.refresh_from_db()
        self.assertEqual(submission.public_registration_reference, "OF-UNIQUE")
        mock_generate.assert_called_once_with()

    def test_reference_generator_checks_for_used_references(self):
        RANDOM_STRINGS = ["UNIQUE", "OTHER"]
        SubmissionFactory.create(
            completed=True,
            registration_success=True,
            public_registration_reference=f"OF-{RANDOM_STRINGS[0]}",
        )
        submission = SubmissionFactory.create(
            form__registration_backend="zgw-create-zaak",
            completed=True,
            registration_success=True,
            registration_result={"bad": {"result": "shape"}},
        )

        def get_random_string(*args, **kwargs):
            return RANDOM_STRINGS.pop(0)

        with patch(
            "openforms.submissions.tasks.registration.get_random_string",
            new=get_random_string,
        ):
            obtain_submission_reference(submission.id)

        submission.refresh_from_db()
        self.assertEqual(submission.public_registration_reference, "OF-OTHER")


class RaceConditionTests(TransactionTestCase):
    def test_race_condition_generating_unique_reference(self):
        """
        Assert that race conditions don't cause crashes.
        """
        # start a separate thread simulating the coincidence that the same reference
        # is created while a reference is being generated, causing a unique constraint
        # violation. The reference generator should recover from this automatically.
        raise NotImplementedError
