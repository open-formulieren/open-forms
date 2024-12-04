from unittest.mock import patch

from django.core.exceptions import PermissionDenied
from django.test import TestCase, tag

from rest_framework.exceptions import ValidationError
from testfixtures import LogCapture

from openforms.config.models import GlobalConfiguration
from openforms.forms.models import FormRegistrationBackend
from openforms.registrations.base import PreRegistrationResult
from openforms.registrations.contrib.zgw_apis.tests.factories import (
    ZGWApiGroupConfigFactory,
)
from openforms.submissions.constants import PostSubmissionEvents
from openforms.submissions.tasks.registration import pre_registration
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.utils.tests.logging import ensure_logger_level

from ..contrib.demo.plugin import DemoRegistration
from ..fields import RegistrationBackendChoiceField
from ..registry import Registry
from ..tasks import register_submission
from .utils import patch_registry as _patch_registry


# TODO: make this implementation the default, project-wide
def patch_registry(register: Registry):
    model_field = FormRegistrationBackend._meta.get_field("backend")
    assert isinstance(model_field, RegistrationBackendChoiceField)
    return _patch_registry(model_field, register)


class PreRegistrationTests(TestCase):
    def setUp(self):
        super().setUp()
        self.addCleanup(GlobalConfiguration.clear_cache)

    def test_pre_registration_with_submission_not_completed(self):
        submission = SubmissionFactory.create()

        with LogCapture() as logs:
            pre_registration(submission.id, PostSubmissionEvents.on_completion)

        logs.check_present(
            (
                "openforms.registrations.tasks",
                "ERROR",
                f"Trying to pre-register submission '{submission}' which is not completed.",
            )
        )

    @patch(
        "openforms.submissions.public_references.generate_unique_submission_reference",
        return_value="OF-1234",
    )
    def test_pre_registration_no_registration_backend(self, m):
        """If no registration backend is specified, the reference is generated before the registration"""

        submission = SubmissionFactory.create(
            completed_not_preregistered=True,
        )

        self.assertEqual(submission.public_registration_reference, "")

        pre_registration(submission.id, PostSubmissionEvents.on_completion)
        submission.refresh_from_db()

        self.assertIsNone(submission.last_register_date)
        self.assertEqual(submission.registration_attempts, 0)
        self.assertEqual(submission.public_registration_reference, "OF-1234")
        self.assertTrue(submission.pre_registration_completed)

    def test_if_preregistration_complete_retry_doesnt_repeat_it(self):
        zgw_group = ZGWApiGroupConfigFactory.create()
        submission = SubmissionFactory.create(
            form__registration_backend="zgw-create-zaak",
            form__registration_backend_options={
                "zgw_api_group": zgw_group.pk,
                "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
                "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
                "objects_api_group": None,
            },
            completed_not_preregistered=True,
        )

        with patch(
            "openforms.registrations.contrib.zgw_apis.plugin.ZGWRegistration.pre_register_submission",
            return_value=PreRegistrationResult(reference="OF-TRALALA"),
        ) as mock_pre_register:
            pre_registration(submission.id, PostSubmissionEvents.on_completion)
            pre_registration(submission.id, PostSubmissionEvents.on_retry)

        mock_pre_register.assert_called_once()

    def test_pre_registration_task_with_invalid_options_raises_error_only_on_retry(
        self,
    ):
        submission = SubmissionFactory.create(
            form__registration_backend="email",
            form__registration_backend_options={
                # "to_emails": ["foo@bar.baz"], # Missing required to_emails parameter
            },
            completed_not_preregistered=True,
        )

        self.assertEqual(submission.public_registration_reference, "")

        with patch(
            "openforms.submissions.public_references.generate_unique_submission_reference",
            return_value="OF-test-registration-failure",
        ):
            with self.subTest("On completion - no error raised"):
                pre_registration(submission.id, PostSubmissionEvents.on_completion)

            submission.refresh_from_db()

            self.assertEqual(
                submission.public_registration_reference, "OF-test-registration-failure"
            )
            self.assertFalse(submission.pre_registration_completed)

            with self.subTest("On retry -  raises errors"):
                with self.assertRaises(ValidationError):
                    pre_registration(submission.id, PostSubmissionEvents.on_retry)

    def test_pre_registration_task_errors_but_does_not_raise_error(self):
        zgw_group = ZGWApiGroupConfigFactory.create()
        submission = SubmissionFactory.create(
            form__registration_backend="zgw-create-zaak",
            form__registration_backend_options={
                "zgw_api_group": zgw_group.pk,
                "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
                "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
                "objects_api_group": None,
            },
            completed_not_preregistered=True,
        )

        self.assertEqual(submission.public_registration_reference, "")

        with (
            patch(
                "openforms.submissions.public_references.generate_unique_submission_reference",
                return_value="OF-test-registration-failure",
            ),
            patch(
                "openforms.registrations.contrib.zgw_apis.plugin.ZGWRegistration.pre_register_submission",
                side_effect=Exception("I FAILED :("),
            ),
        ):
            pre_registration(submission.id, PostSubmissionEvents.on_completion)

        submission.refresh_from_db()

        self.assertEqual(
            submission.public_registration_reference, "OF-test-registration-failure"
        )
        self.assertFalse(submission.pre_registration_completed)
        self.assertIn("I FAILED :(", submission.registration_result["traceback"])

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
                completed_not_preregistered=True,
            )

            with self.subTest(plugin_name):
                self.assertEqual(submission.public_registration_reference, "")

                with patch(
                    "openforms.submissions.public_references.generate_unique_submission_reference",
                    return_value=f"OF-{plugin_name}",
                ):
                    pre_registration(submission.id, PostSubmissionEvents.on_completion)

                submission.refresh_from_db()

                self.assertEqual(
                    submission.public_registration_reference, f"OF-{plugin_name}"
                )

    def test_if_pre_registration_fails_registration_task_skips(self):
        submission = SubmissionFactory.create(
            form__registration_backend="email",
            form__registration_backend_options={
                # "to_emails": ["foo@bar.baz"], # Missing required to_emails parameter
            },
            completed_not_preregistered=True,
        )

        pre_registration(
            submission.id, PostSubmissionEvents.on_completion
        )  # Fails because of invalid options

        with patch(
            "openforms.registrations.contrib.zgw_apis.plugin.ZGWRegistration.register_submission",
        ) as registration_patch:
            register_submission(submission.id, PostSubmissionEvents.on_completion)

        submission.refresh_from_db()

        registration_patch.assert_not_called()
        self.assertIsNotNone(submission.last_register_date)
        self.assertEqual(submission.registration_attempts, 1)

    def test_retry_doesnt_overwrite_internal_reference(self):
        zgw_group = ZGWApiGroupConfigFactory.create()
        submission = SubmissionFactory.create(
            form__registration_backend="zgw-create-zaak",
            form__registration_backend_options={
                "zgw_api_group": zgw_group.pk,
                "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
                "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
                "objects_api_group": None,
            },
            completed_not_preregistered=True,
        )

        with patch(
            "openforms.registrations.contrib.zgw_apis.plugin.ZGWRegistration.pre_register_submission",
            side_effect=Exception,
        ):
            with patch(
                "openforms.submissions.public_references.generate_unique_submission_reference",
                return_value="OF-IM-NOT-OVERWRITTEN",
            ):
                pre_registration(submission.id, PostSubmissionEvents.on_completion)

            with patch(
                "openforms.submissions.public_references.generate_unique_submission_reference",
                return_value="OF-IM-DIFFERENT",
            ):
                with self.assertRaises(Exception):
                    pre_registration(submission.id, PostSubmissionEvents.on_retry)

        submission.refresh_from_db()

        self.assertEqual(
            submission.public_registration_reference, "OF-IM-NOT-OVERWRITTEN"
        )

    def test_retry_keeps_track_of_internal_reference(self):
        zgw_group = ZGWApiGroupConfigFactory.create()
        submission = SubmissionFactory.create(
            form__registration_backend="zgw-create-zaak",
            form__registration_backend_options={
                "zgw_api_group": zgw_group.pk,
                "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
                "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
                "objects_api_group": None,
            },
            completed_not_preregistered=True,
        )

        with (
            patch(
                "openforms.submissions.public_references.generate_unique_submission_reference",
                return_value="OF-IM-TEMPORARY",
            ),
            patch(
                "openforms.registrations.contrib.zgw_apis.plugin.ZGWRegistration.pre_register_submission",
                side_effect=Exception,
            ),
        ):
            pre_registration(submission.id, PostSubmissionEvents.on_completion)

        with patch(
            "openforms.registrations.contrib.zgw_apis.plugin.ZGWRegistration.pre_register_submission",
            return_value=PreRegistrationResult(reference="OF-IM-FINAL"),
        ):
            pre_registration(submission.id, PostSubmissionEvents.on_retry)

        submission.refresh_from_db()

        self.assertEqual(
            submission.registration_result["temporary_internal_reference"],
            "OF-IM-TEMPORARY",
        )

    @patch("openforms.plugins.plugin.GlobalConfiguration.get_solo")
    def test_retry_after_too_many_attempts_skips(self, m_get_solo):
        zgw_group = ZGWApiGroupConfigFactory.create()
        submission = SubmissionFactory.create(
            form__registration_backend="zgw-create-zaak",
            form__registration_backend_options={
                "zgw_api_group": zgw_group.pk,
                "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
                "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
                "objects_api_group": None,
            },
            completed_not_preregistered=True,
            registration_attempts=3,
        )

        TEST_NUM_ATTEMPTS = 3
        m_get_solo.return_value = GlobalConfiguration(
            registration_attempt_limit=TEST_NUM_ATTEMPTS,
        )

        with (
            patch(
                "openforms.registrations.contrib.zgw_apis.plugin.ZGWRegistration.pre_register_submission"
            ) as mock_pre_register,
            ensure_logger_level("DEBUG"),
            self.assertLogs(level="DEBUG") as logs,
        ):
            pre_registration(submission.id, PostSubmissionEvents.on_retry)

        mock_pre_register.assert_not_called()
        self.assertEqual(
            "Skipping pre-registration for submission '%s' because it retried and failed too many times.",
            logs.records[-1].msg,
        )

    def test_update_registration_result_after_pre_registration(self):
        zgw_group = ZGWApiGroupConfigFactory.create()
        submission = SubmissionFactory.create(
            form__registration_backend="zgw-create-zaak",
            form__registration_backend_options={
                "zgw_api_group": zgw_group.pk,
                "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
                "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
                "objects_api_group": None,
            },
            completed_not_preregistered=True,
        )

        with patch(
            "openforms.registrations.contrib.zgw_apis.plugin.ZGWRegistration.pre_register_submission",
            return_value=PreRegistrationResult(
                reference="ZAAK-TRALALA", data={"zaak": {"ohlalla": "a property!"}}
            ),
        ):
            pre_registration(submission.id, PostSubmissionEvents.on_completion)

        submission.refresh_from_db()
        self.assertEqual(submission.public_registration_reference, "ZAAK-TRALALA")
        self.assertEqual(
            submission.registration_result, {"zaak": {"ohlalla": "a property!"}}
        )

    @patch("openforms.plugins.plugin.GlobalConfiguration.get_solo")
    def test_traceback_removed_from_result_after_success(self, m_get_solo):
        zgw_group = ZGWApiGroupConfigFactory.create()
        submission = SubmissionFactory.create(
            form__registration_backend="zgw-create-zaak",
            form__registration_backend_options={
                "zgw_api_group": zgw_group.pk,
                "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
                "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
                "objects_api_group": None,
            },
            completed_not_preregistered=True,
            registration_attempts=1,
            registration_result={"traceback": "An error, how sad."},
        )

        TEST_NUM_ATTEMPTS = 3
        m_get_solo.return_value = GlobalConfiguration(
            registration_attempt_limit=TEST_NUM_ATTEMPTS,
        )

        with patch(
            "openforms.registrations.contrib.zgw_apis.plugin.ZGWRegistration.pre_register_submission",
            return_value=PreRegistrationResult(
                reference="OF-TRALALAL", data={"something": "irrelevant"}
            ),
        ):
            pre_registration(submission.id, PostSubmissionEvents.on_retry)

        submission.refresh_from_db()

        self.assertNotIn("traceback", submission.registration_result)

    @tag("gh-4398")
    def test_verify_initial_data_ownership(self):
        # set up a separate registry with plugins we control, to test the generic
        # mechanism
        register = Registry()

        class TestPlugin(DemoRegistration):
            def verify_initial_data_ownership(self, submission, options):
                if submission.initial_data_reference == "trigger-crash":
                    raise Exception("arbitrary crash!")
                raise PermissionDenied("you shall not pass")

        register("ownership-check-fails")(TestPlugin)

        patcher = patch_registry(register)
        patcher.__enter__()
        self.addCleanup(lambda: patcher.__exit__(None, None, None))

        with self.subTest("no ownership check without initial data reference"):
            submission1 = SubmissionFactory.create(
                form__registration_backend="ownership-check-fails",
                completed_not_preregistered=True,
                initial_data_reference="",
            )
            assert not submission1.pre_registration_completed

            pre_registration(submission1.id, PostSubmissionEvents.on_completion)

            submission1.refresh_from_db()
            self.assertTrue(submission1.pre_registration_completed)

        with self.subTest("ownership check runs when initial data reference given"):
            submission2 = SubmissionFactory.create(
                form__registration_backend="ownership-check-fails",
                completed_not_preregistered=True,
                initial_data_reference="some reference",
            )
            assert not submission2.pre_registration_completed

            pre_registration(submission2.id, PostSubmissionEvents.on_completion)

            submission2.refresh_from_db()
            # False because the ownership check prevented it from completing
            self.assertFalse(submission2.pre_registration_completed)
            self.assertIn(
                "PermissionDenied", submission2.registration_result["traceback"]
            )
            self.assertIn(
                "you shall not pass", submission2.registration_result["traceback"]
            )

        with self.subTest("arbitrary errors in ownership check abort registration"):
            submission3 = SubmissionFactory.create(
                form__registration_backend="ownership-check-fails",
                completed_not_preregistered=True,
                initial_data_reference="trigger-crash",
            )
            assert not submission3.pre_registration_completed

            pre_registration(submission3.id, PostSubmissionEvents.on_completion)

            submission3.refresh_from_db()
            # False because the ownership check prevented it from completing
            self.assertFalse(submission3.pre_registration_completed)
            self.assertIn("Exception", submission3.registration_result["traceback"])
            self.assertIn(
                "arbitrary crash!", submission3.registration_result["traceback"]
            )
