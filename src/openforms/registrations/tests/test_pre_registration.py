from unittest.mock import patch

from django.test import TestCase

from openforms.registrations.exceptions import RegistrationFailed
from openforms.registrations.tasks import register_submission
from openforms.submissions.tasks.registration import (
    obtain_submission_reference,
    pre_registration,
)
from openforms.submissions.tests.factories import SubmissionFactory


class PreRegistrationTests(TestCase):
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
        self.assertTrue(submission.pre_registration_completed)

    def test_if_preregistration_complete_retry_doesnt_repeat_it(self):
        submission = SubmissionFactory.create(
            form__registration_backend="zgw-create-zaak",
            completed=True,
        )

        with patch(
            "openforms.registrations.contrib.zgw_apis.plugin.ZGWRegistration.pre_register_submission"
        ) as mock_pre_register:
            pre_registration(submission.id)
            pre_registration(submission.id)

        mock_pre_register.assert_called_once()

    def test_pre_registration_task_with_invalid_options_does_not_raise_error(self):
        submission = SubmissionFactory.create(
            form__registration_backend="email",
            form__registration_backend_options={
                # "to_emails": ["foo@bar.baz"], # Missing required to_emails parameter
            },
            completed=True,
        )

        self.assertEqual(submission.public_registration_reference, "")

        with patch(
            "openforms.submissions.tasks.registration.generate_unique_submission_reference",
            return_value="OF-test-registration-failure",
        ):
            pre_registration(submission.id)

        submission.refresh_from_db()

        self.assertEqual(
            submission.public_registration_reference, "OF-test-registration-failure"
        )
        self.assertFalse(submission.pre_registration_completed)

    def test_pre_registration_task_errors_but_does_not_raise_error(self):
        submission = SubmissionFactory.create(
            form__registration_backend="zgw-create-zaak",
            completed=True,
        )

        self.assertEqual(submission.public_registration_reference, "")

        with patch(
            "openforms.submissions.tasks.registration.generate_unique_submission_reference",
            return_value="OF-test-registration-failure",
        ):
            with patch(
                "openforms.registrations.contrib.zgw_apis.plugin.ZGWRegistration.pre_register_submission",
                side_effect=Exception("I FAILED :("),
            ):
                pre_registration(submission.id)

        submission.refresh_from_db()

        self.assertEqual(
            submission.public_registration_reference, "OF-test-registration-failure"
        )
        self.assertFalse(submission.pre_registration_completed)
        self.assertEqual(submission.registration_result["traceback"], "I FAILED :(")

    def test_plugins_generating_reference_before_during_pre_registration(self):
        plugin_data = [
            ("email", {"to_emails": ["foo@bar.baz"]}),
            (
                "camunda",
                {
                    "process_definition": "invoice",
                    "process_definition_version": None,
                    "process_variables": [],
                    "complex_process_variables": [],
                },
            ),
            ("demo", {}),
            ("failing-demo", {}),
            ("exception-demo", {}),
            ("microsoft-graph", {}),
            ("objects_api", {}),
        ]

        for plugin_name, plugin_options in plugin_data:
            submission = SubmissionFactory.create(
                form__registration_backend=plugin_name,
                form__registration_backend_options=plugin_options,
                completed=True,
            )

            with self.subTest(plugin_name):
                self.assertEqual(submission.public_registration_reference, "")

                with patch(
                    "openforms.submissions.tasks.registration.generate_unique_submission_reference",
                    return_value=f"OF-{plugin_name}",
                ):
                    pre_registration(submission.id)

                submission.refresh_from_db()

                self.assertEqual(
                    submission.public_registration_reference, f"OF-{plugin_name}"
                )

    def test_plugins_post_registration_does_nothing(self):
        plugin_data = [
            ("email", {"to_emails": ["foo@bar.baz"]}),
            (
                "camunda",
                {
                    "process_definition": "invoice",
                    "process_definition_version": None,
                    "process_variables": [],
                    "complex_process_variables": [],
                },
            ),
            ("demo", {}),
            ("failing-demo", {}),
            ("exception-demo", {}),
            ("microsoft-graph", {}),
            ("objects_api", {}),
        ]

        for plugin_name, plugin_options in plugin_data:
            submission = SubmissionFactory.create(
                form__registration_backend=plugin_name,
                form__registration_backend_options=plugin_options,
                public_registration_reference=f"OF-{plugin_name}",
            )

            with self.subTest(plugin_name):
                self.assertEqual(
                    submission.public_registration_reference, f"OF-{plugin_name}"
                )

                obtain_submission_reference(submission.id)
                submission.refresh_from_db()

                self.assertEqual(
                    submission.public_registration_reference, f"OF-{plugin_name}"
                )

    def test_if_pre_registration_fails_registration_task_raises_error(self):
        submission = SubmissionFactory.create(
            form__registration_backend="email",
            form__registration_backend_options={
                # "to_emails": ["foo@bar.baz"], # Missing required to_emails parameter
            },
            completed=True,
        )

        pre_registration(submission.id)  # Fails because of invalid options

        with self.assertRaises(RegistrationFailed):
            register_submission(submission.id)

    def test_retry_doesnt_overwrite_internal_reference(self):
        submission = SubmissionFactory.create(
            form__registration_backend="zgw-create-zaak",
            completed=True,
        )

        with patch(
            "openforms.registrations.contrib.zgw_apis.plugin.ZGWRegistration.pre_register_submission",
            side_effect=Exception,
        ):
            with patch(
                "openforms.submissions.tasks.registration.generate_unique_submission_reference",
                return_value="OF-IM-NOT-OVERWRITTEN",
            ):
                pre_registration(submission.id)

            with patch(
                "openforms.submissions.tasks.registration.generate_unique_submission_reference",
                return_value="OF-IM-DIFFERENT",
            ):
                pre_registration(submission.id)

        submission.refresh_from_db()

        self.assertEqual(
            submission.public_registration_reference, "OF-IM-NOT-OVERWRITTEN"
        )

    def test_retry_keeps_track_of_internal_reference(self):
        submission = SubmissionFactory.create(
            form__registration_backend="zgw-create-zaak",
            completed=True,
        )

        with patch(
            "openforms.submissions.tasks.registration.generate_unique_submission_reference",
            return_value="OF-IM-TEMPORARY",
        ):
            with patch(
                "openforms.registrations.contrib.zgw_apis.plugin.ZGWRegistration.pre_register_submission",
                side_effect=Exception,
            ):
                pre_registration(submission.id)

        with patch(
            "openforms.registrations.contrib.zgw_apis.plugin.ZGWRegistration.pre_register_submission"
        ):
            pre_registration(submission.id)

        submission.refresh_from_db()

        self.assertEqual(
            submission.registration_result["temporary_internal_reference"],
            "OF-IM-TEMPORARY",
        )
