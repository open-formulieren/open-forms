import threading
import time
from unittest.mock import patch

from django.db import close_old_connections
from django.test import TestCase, TransactionTestCase

from ..tasks.registration import obtain_submission_reference, pre_registration
from .factories import SubmissionFactory


class RaceConditionTests(TransactionTestCase):
    def test_race_condition_generating_unique_reference(self):
        """
        Assert that race conditions don't cause crashes.

        This test starts a separate thread simulating the coincidence that the same
        reference is created while a reference is being generated, causing a unique
        constraint violation. The reference generator should recover from this
        automatically.
        """
        RANDOM_STRINGS = ["UNIQUE", "OTHER"]
        submission1, submission2 = SubmissionFactory.create_batch(
            2,
            form__registration_backend="zgw-create-zaak",
            completed=True,
            registration_success=True,
            registration_result={"bad": {"result": "shape"}},
        )

        def generate_unique_submission_reference(*args, **kwargs):
            string = RANDOM_STRINGS.pop(0)
            # introduce a delay so that the other thread can insert the same reference
            time.sleep(0.5)
            return f"OF-{string}"

        def race_condition():
            submission2.public_registration_reference = "OF-UNIQUE"
            submission2.save(update_fields=["public_registration_reference"])
            close_old_connections()

        # code affected by race condition
        def obtain_reference():
            with patch(
                "openforms.submissions.tasks.registration.generate_unique_submission_reference",
                new=generate_unique_submission_reference,
            ):
                obtain_submission_reference(submission1.id)
                close_old_connections()

        race_condition_thread = threading.Thread(target=race_condition)
        obtain_reference_thread = threading.Thread(target=obtain_reference)

        # start and wait for threads to finish
        obtain_reference_thread.start()
        race_condition_thread.start()
        race_condition_thread.join()
        obtain_reference_thread.join()

        submission1.refresh_from_db()
        submission2.refresh_from_db()
        self.assertEqual(submission2.public_registration_reference, "OF-UNIQUE")
        self.assertEqual(submission1.public_registration_reference, "OF-OTHER")


class GenerateSubmissionReferenceTests(TestCase):
    @patch(
        "openforms.submissions.tasks.registration.generate_unique_submission_reference",
        return_value="OF-1234",
    )
    def test_pre_registration_no_registration_backend(self, m):
        """If no registration backend is specified, the reference is generated before the registration"""

        submission = SubmissionFactory.create(
            completed=True,
        )

        self.assertEqual(submission.public_registration_reference, "")

        pre_registration(submission.id)
        submission.refresh_from_db()

        self.assertEqual(submission.public_registration_reference, "OF-1234")

    @patch(
        "openforms.submissions.tasks.registration.generate_unique_submission_reference",
        return_value="OF-1234",
    )
    def test_pre_registration_registration_backend_does_not_generate_reference(self, m):
        """If the registration backend does not generate a reference, then reference is generated before the registration"""

        submission = SubmissionFactory.create(
            form__registration_backend="email",
            completed=True,
        )

        self.assertEqual(submission.public_registration_reference, "")

        pre_registration(submission.id)
        submission.refresh_from_db()

        self.assertEqual(submission.public_registration_reference, "OF-1234")

    def test_registration_backend_generates_reference(self):
        """If the registration backend sets the reference, then it should not be only set after registration"""

        submission = SubmissionFactory.create(
            form__registration_backend="zgw-create-zaak",
            completed=True,
            registration_success=True,
            registration_result={"zaak": {"identificatie": "AEY64"}},
        )

        self.assertEqual(submission.public_registration_reference, "")

        pre_registration(submission.id)
        submission.refresh_from_db()

        self.assertEqual(submission.public_registration_reference, "")

        obtain_submission_reference(submission.id)
        submission.refresh_from_db()

        self.assertEqual(submission.public_registration_reference, "AEY64")
