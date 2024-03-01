import threading
import time
from unittest.mock import patch

from django.db import close_old_connections
from django.test import TestCase, TransactionTestCase

from ..public_references import set_submission_reference
from .factories import SubmissionFactory


class ObtainSubmissionReferenceTests(TestCase):
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
            "openforms.submissions.public_references.get_random_string",
            new=get_random_string,
        ):
            set_submission_reference(submission)

        submission.refresh_from_db()
        self.assertEqual(submission.public_registration_reference, "OF-OTHER")


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
                "openforms.submissions.public_references.generate_unique_submission_reference",
                new=generate_unique_submission_reference,
            ):
                set_submission_reference(submission1)
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
