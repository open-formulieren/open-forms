from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, tag
from django.utils import timezone

from celery import states
from freezegun import freeze_time
from privates.test import temp_private_root
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.appointments.tests.factories import AppointmentInfoFactory
from openforms.config.models import GlobalConfiguration
from openforms.config.tests.factories import ThemeFactory
from openforms.frontend import get_frontend_redirect_url
from openforms.payments.constants import PaymentStatus
from openforms.payments.contrib.ogone.tests.factories import OgoneMerchantFactory
from openforms.payments.tests.factories import SubmissionPaymentFactory

from ..constants import (
    SUBMISSIONS_SESSION_KEY,
    PostSubmissionEvents,
    ProcessingResults,
    ProcessingStatuses,
)
from ..tasks import cleanup_on_completion_results
from ..tokens import submission_status_token_generator
from .factories import (
    PostCompletionMetadataFactory,
    SubmissionFactory,
    SubmissionReportFactory,
)


class SubmissionStatusPermissionTests(APITestCase):
    def setUp(self):
        super().setUp()
        self.addCleanup(GlobalConfiguration.clear_cache)

    def test_valid_token(self):
        # Use empty task ID to not need a real broker
        submission = SubmissionFactory.create(
            completed=True,
            metadata__tasks_ids=[],
            metadata__trigger_event=PostSubmissionEvents.on_completion,
        )
        token = submission_status_token_generator.make_token(submission)
        check_status_url = reverse(
            "api:submission-status", kwargs={"uuid": submission.uuid, "token": token}
        )

        with freeze_time(timedelta(days=1)):
            response = self.client.get(check_status_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @freeze_time(
        "2023-02-24T10:05:00+01:00"
    )  # between 0-1am this fails because the tokens "roll over""
    def test_expired_token(self):
        # Use empty task ID to not need a real broker
        submission = SubmissionFactory.create(completed=True, metadata__tasks_ids=[])
        token = submission_status_token_generator.make_token(submission)
        check_status_url = reverse(
            "api:submission-status", kwargs={"uuid": submission.uuid, "token": token}
        )

        with freeze_time(timedelta(days=2)):
            response = self.client.get(check_status_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_token_invalidated_by_new_completion(self):
        submission = SubmissionFactory.create(completed=True, metadata__tasks_ids=[])
        old_token = submission_status_token_generator.make_token(submission)
        submission.completed_on = timezone.now()
        submission.save()
        check_status_url = reverse(
            "api:submission-status",
            kwargs={"uuid": submission.uuid, "token": old_token},
        )

        response = self.client.get(check_status_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_wrongly_formatted_token(self):
        submission = SubmissionFactory.create(completed=True, metadata__tasks_ids=[])
        # can't reverse because bad format lol
        check_status_url = f"/api/v2/submissions/{submission.uuid}/badformat/status"

        response = self.client.get(check_status_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_token_timestamp(self):
        submission = SubmissionFactory.create(completed=True, metadata__tasks_ids=[])
        # can't reverse because bad format lol
        check_status_url = (
            f"/api/v2/submissions/{submission.uuid}/$$$-{'a' * 20}/status"
        )

        response = self.client.get(check_status_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class SubmissionStatusStatusAndResultTests(APITestCase):
    def setUp(self):
        super().setUp()
        self.addCleanup(GlobalConfiguration.clear_cache)

    def test_no_task_id_registered(self):
        submission = SubmissionFactory.create(
            completed=True,
            metadata__tasks_ids=[],
            metadata__trigger_event=PostSubmissionEvents.on_completion,
        )
        token = submission_status_token_generator.make_token(submission)
        check_status_url = reverse(
            "api:submission-status", kwargs={"uuid": submission.uuid, "token": token}
        )

        response = self.client.get(check_status_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(response_data["status"], ProcessingStatuses.in_progress)
        self.assertEqual(response_data["paymentUrl"], "")
        self.assertEqual(response_data["reportDownloadUrl"], "")
        self.assertEqual(response_data["confirmationPageContent"], "")

    @tag("gh-4505")
    def test_submission_with_authentication_context(self):
        submission = SubmissionFactory.create(
            completed=True,
            form__authentication_backend="demo",
            auth_info__is_digid=True,
            auth_info__with_hashed_identifying_attributes=True,
        )
        assert submission.is_authenticated
        assert submission.auth_info.attribute_hashed
        token = submission_status_token_generator.make_token(submission)
        check_status_url = reverse(
            "api:submission-status", kwargs={"uuid": submission.uuid, "token": token}
        )

        with patch("openforms.submissions.status.AsyncResult") as mock_AsyncResult:
            mock_AsyncResult.return_value.state = states.SUCCESS

            response = self.client.get(check_status_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_in_progress_celery_states(self):
        submission = SubmissionFactory.create(completed=True)
        token = submission_status_token_generator.make_token(submission)
        check_status_url = reverse(
            "api:submission-status", kwargs={"uuid": submission.uuid, "token": token}
        )

        in_progress_states = [
            states.PENDING,
            states.RECEIVED,
            states.STARTED,
            states.RETRY,
        ]

        with patch("openforms.submissions.status.AsyncResult") as mock_AsyncResult:
            for state in in_progress_states:
                with self.subTest(celery_state=state):
                    mock_AsyncResult.return_value.state = state

                    response = self.client.get(check_status_url)

                    self.assertEqual(response.status_code, status.HTTP_200_OK)
                    response_data = response.json()
                    self.assertEqual(
                        response_data["status"], ProcessingStatuses.in_progress
                    )
                    self.assertEqual(response_data["result"], "")
                    self.assertEqual(response_data["paymentUrl"], "")

    def test_finished_celery_states(self):
        submission = SubmissionFactory.create(completed=True)
        token = submission_status_token_generator.make_token(submission)
        check_status_url = reverse(
            "api:submission-status", kwargs={"uuid": submission.uuid, "token": token}
        )

        finished_states = [
            states.SUCCESS,
            states.FAILURE,
        ]

        with patch("openforms.submissions.status.AsyncResult") as mock_AsyncResult:
            for state in finished_states:
                with self.subTest(celery_state=state):
                    mock_AsyncResult.return_value.state = state

                    response = self.client.get(check_status_url)

                    self.assertEqual(response.status_code, status.HTTP_200_OK)
                    response_data = response.json()
                    self.assertEqual(response_data["status"], ProcessingStatuses.done)
                    self.assertNotEqual(response_data["result"], "")

    def test_result_for_done_states(self):
        submission = SubmissionFactory.create(completed=True)
        token = submission_status_token_generator.make_token(submission)
        check_status_url = reverse(
            "api:submission-status", kwargs={"uuid": submission.uuid, "token": token}
        )

        expected = (
            (states.SUCCESS, ProcessingResults.success),
            (states.FAILURE, ProcessingResults.failed),
        )

        with patch("openforms.submissions.status.AsyncResult") as mock_AsyncResult:
            for state, expected_result in expected:
                with self.subTest(celery_state=state):
                    mock_AsyncResult.return_value.state = state

                    response = self.client.get(check_status_url)

                    self.assertEqual(response.status_code, status.HTTP_200_OK)
                    response_data = response.json()
                    self.assertEqual(response_data["status"], ProcessingStatuses.done)
                    self.assertEqual(response_data["result"], expected_result)
                    # no payment configured
                    self.assertEqual(response_data["paymentUrl"], "")

    def test_submission_id_in_session_for_failed_result(self):
        submission = SubmissionFactory.create(completed=True)
        token = submission_status_token_generator.make_token(submission)
        check_status_url = reverse(
            "api:submission-status", kwargs={"uuid": submission.uuid, "token": token}
        )

        with patch("openforms.submissions.status.AsyncResult") as mock_AsyncResult:
            mock_AsyncResult.return_value.state = states.FAILURE

            response = self.client.get(check_status_url)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            response_data = response.json()
            self.assertEqual(response_data["status"], ProcessingStatuses.done)
            self.assertEqual(response_data["result"], ProcessingResults.failed)
            # check that the submission ID is in the session
            self.assertEqual(
                response.wsgi_request.session[SUBMISSIONS_SESSION_KEY],
                [str(submission.uuid)],
            )


@temp_private_root()
class SubmissionStatusExtraInformationTests(APITestCase):
    """
    Assert that the extra information fields relay the necessary information.

    Only when the status is 'done' should these fields emit data.
    """

    def setUp(self):
        super().setUp()
        self.addCleanup(GlobalConfiguration.clear_cache)

    def test_succesful_processing(self):
        submission = SubmissionFactory.create(
            completed=True,
            form__submission_confirmation_template="You get a cookie!",
            public_registration_reference="OF-ABCDE",
            metadata__tasks_ids=["some-id"],
            metadata__trigger_event=PostSubmissionEvents.on_completion,
        )
        SubmissionReportFactory.create(submission=submission)
        token = submission_status_token_generator.make_token(submission)
        check_status_url = reverse(
            "api:submission-status", kwargs={"uuid": submission.uuid, "token": token}
        )

        with patch("openforms.submissions.status.AsyncResult") as mock_AsyncResult:
            mock_AsyncResult.return_value.state = states.SUCCESS

            response = self.client.get(check_status_url)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            response_data = response.json()
            self.assertEqual(response_data["status"], ProcessingStatuses.done)
            self.assertEqual(response_data["result"], ProcessingResults.success)
            self.assertEqual(response_data["publicReference"], "OF-ABCDE")
            self.assertEqual(response_data["errorMessage"], "")
            self.assertEqual(
                response_data["confirmationPageContent"], "You get a cookie!"
            )
            self.assertTrue(
                response_data["reportDownloadUrl"].startswith("http://testserver")
            )
            # no payment configured/required -> no URL
            self.assertEqual(response_data["paymentUrl"], "")

    def test_appointment_user_error(self):
        submission = SubmissionFactory.create(
            completed=True, form__submission_confirmation_template="You get a cookie!"
        )
        AppointmentInfoFactory.create(submission=submission, has_missing_info=True)

        token = submission_status_token_generator.make_token(submission)
        check_status_url = reverse(
            "api:submission-status", kwargs={"uuid": submission.uuid, "token": token}
        )

        with patch("openforms.submissions.status.AsyncResult") as mock_AsyncResult:
            mock_AsyncResult.return_value.state = states.FAILURE

            response = self.client.get(check_status_url)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            response_data = response.json()
            self.assertEqual(response_data["status"], ProcessingStatuses.done)
            self.assertEqual(response_data["result"], ProcessingResults.failed)
            self.assertEqual(response_data["errorMessage"], "Some fields are missing.")
            self.assertEqual(response_data["confirmationPageContent"], "")
            self.assertEqual(response_data["reportDownloadUrl"], "")

    @patch(
        "openforms.submissions.api.serializers.GlobalConfiguration.get_solo",
        return_value=GlobalConfiguration(main_website="https://maykinmedia.nl"),
    )
    def test_displaying_main_website_link_returns_main_link_through_api(
        self, mock_get_solo
    ):
        submission = SubmissionFactory.create(
            completed=True,
            form__display_main_website_link=True,
            metadata__tasks_ids=["some-id"],
            metadata__trigger_event=PostSubmissionEvents.on_completion,
        )

        token = submission_status_token_generator.make_token(submission)
        check_status_url = reverse(
            "api:submission-status", kwargs={"uuid": submission.uuid, "token": token}
        )

        with patch("openforms.submissions.status.AsyncResult") as mock_AsyncResult:
            mock_AsyncResult.return_value.state = states.SUCCESS

            response = self.client.get(check_status_url)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            response_data = response.json()
            self.assertEqual(response_data["status"], ProcessingStatuses.done)
            self.assertEqual(response_data["result"], ProcessingResults.success)
            self.assertEqual(response_data["mainWebsiteUrl"], "https://maykinmedia.nl")

    @patch(
        "openforms.submissions.api.serializers.GlobalConfiguration.get_solo",
        return_value=GlobalConfiguration(main_website="https://maykinmedia.nl"),
    )
    def test_displaying_main_website_link_does_not_return_link_when_link_should_not_be_displayed(
        self, mock_get_solo
    ):
        submission = SubmissionFactory.create(
            completed=True, form__display_main_website_link=False
        )

        token = submission_status_token_generator.make_token(submission)
        check_status_url = reverse(
            "api:submission-status", kwargs={"uuid": submission.uuid, "token": token}
        )

        with patch("openforms.submissions.status.AsyncResult") as mock_AsyncResult:
            mock_AsyncResult.return_value.state = states.SUCCESS

            response = self.client.get(check_status_url)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            response_data = response.json()
            self.assertEqual(response_data["status"], ProcessingStatuses.done)
            self.assertEqual(response_data["result"], ProcessingResults.success)
            self.assertEqual(response_data["mainWebsiteUrl"], "")

    @patch(
        "openforms.submissions.api.serializers.GlobalConfiguration.get_solo",
        return_value=GlobalConfiguration(main_website="https://maykinmedia.nl"),
    )
    def test_displaying_main_website_link_from_theme_connected_to_form(
        self, mock_get_solo
    ):
        theme = ThemeFactory.create(
            organization_name="The company", main_website="http://example.com"
        )
        submission = SubmissionFactory.create(completed=True, form__theme=theme)

        token = submission_status_token_generator.make_token(submission)
        check_status_url = reverse(
            "api:submission-status", kwargs={"uuid": submission.uuid, "token": token}
        )

        with patch("openforms.submissions.status.AsyncResult") as mock_AsyncResult:
            mock_AsyncResult.return_value.state = states.SUCCESS
            response = self.client.get(check_status_url)
            response_data = response.json()

            self.assertEqual(response_data["mainWebsiteUrl"], "http://example.com")

    @patch(
        "openforms.submissions.api.serializers.GlobalConfiguration.get_solo",
        return_value=GlobalConfiguration(
            default_theme=ThemeFactory.build(
                organization_name="The company", main_website="http://example.com"
            ),
            main_website="https://maykinmedia.nl",
        ),
    )
    def test_displaying_main_website_link_from_general_configs_default_theme(
        self, mock_get_solo
    ):
        submission = SubmissionFactory.create(completed=True)

        token = submission_status_token_generator.make_token(submission)
        check_status_url = reverse(
            "api:submission-status", kwargs={"uuid": submission.uuid, "token": token}
        )

        with patch("openforms.submissions.status.AsyncResult") as mock_AsyncResult:
            mock_AsyncResult.return_value.state = states.SUCCESS
            response = self.client.get(check_status_url)
            response_data = response.json()

            self.assertEqual(response_data["mainWebsiteUrl"], "http://example.com")

    @patch(
        "openforms.submissions.api.serializers.GlobalConfiguration.get_solo",
        return_value=GlobalConfiguration(
            default_theme=ThemeFactory.build(
                organization_name="The company", main_website="http://example.com"
            ),
            main_website="https://maykinmedia.nl",
        ),
    )
    def test_displaying_main_website_link_from_config(self, mock_get_solo):
        submission = SubmissionFactory.create(completed=True)

        token = submission_status_token_generator.make_token(submission)
        check_status_url = reverse(
            "api:submission-status", kwargs={"uuid": submission.uuid, "token": token}
        )

        with patch("openforms.submissions.status.AsyncResult") as mock_AsyncResult:
            mock_AsyncResult.return_value.state = states.SUCCESS
            response = self.client.get(check_status_url)
            response_data = response.json()

            self.assertEqual(response_data["mainWebsiteUrl"], "http://example.com")

    def test_payment_required(self):
        merchant = OgoneMerchantFactory.create()
        submission = SubmissionFactory.create(
            completed=True,
            form__product__price=Decimal("10"),
            form__payment_backend="ogone-legacy",
            # see PR#650 which drops this requirement
            form__payment_backend_options={"merchant_id": merchant.id},
        )
        submission.calculate_price()
        SubmissionReportFactory.create(submission=submission)
        token = submission_status_token_generator.make_token(submission)
        check_status_url = reverse(
            "api:submission-status", kwargs={"uuid": submission.uuid, "token": token}
        )

        with patch("openforms.submissions.status.AsyncResult") as mock_AsyncResult:
            mock_AsyncResult.return_value.state = states.SUCCESS

            response = self.client.get(check_status_url)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            response_data = response.json()

            expected_url = reverse(
                "payments:start",
                kwargs={"uuid": submission.uuid, "plugin_id": "ogone-legacy"},
            )
            self.assertEqual(
                response_data["paymentUrl"], f"http://testserver{expected_url}"
            )

    def test_payment_already_received(self):
        submission = SubmissionFactory.create(
            completed=True,
            public_registration_reference="OF-ABCDE",
            form__product__price=Decimal("12.34"),
            form__payment_backend="test",
        )
        SubmissionPaymentFactory.for_submission(
            submission, status=PaymentStatus.completed
        )
        token = submission_status_token_generator.make_token(submission)
        check_status_url = reverse(
            "api:submission-status", kwargs={"uuid": submission.uuid, "token": token}
        )

        with patch("openforms.submissions.status.AsyncResult") as mock_AsyncResult:
            mock_AsyncResult.return_value.state = states.SUCCESS

            response = self.client.get(check_status_url)
            response_data = response.json()

            # Payment is required, but has already been done -> No URL
            self.assertEqual(response_data["paymentUrl"], "")

    def test_succesful_processing_submission_with_cosign(self):
        config = GlobalConfiguration.get_solo()
        config.cosign_submission_confirmation_title = "Pending ({{ public_reference }})"
        config.cosign_submission_confirmation_template = (
            "<p>Email sent to {{ cosigner_email }}, reference {{ public_reference }}.</p>\n"
            "<p>Cosign now: {% cosign_button text='Cosign now' %}</p>"
        )
        config.save()
        submission = SubmissionFactory.from_components(
            components_list=[{"type": "cosign", "key": "cosign"}],
            submitted_data={
                "cosign": "test@example.com",
            },
            form_url="http://frontend/form",
            completed=True,
            public_registration_reference="OF-ABCDE",
            metadata__tasks_ids=["some-id"],
            metadata__trigger_event=PostSubmissionEvents.on_completion,
        )
        token = submission_status_token_generator.make_token(submission)
        check_status_url = reverse(
            "api:submission-status", kwargs={"uuid": submission.uuid, "token": token}
        )

        with patch("openforms.submissions.status.AsyncResult") as mock_AsyncResult:
            mock_AsyncResult.return_value.state = states.SUCCESS

            response = self.client.get(
                check_status_url, headers={"X-CSP-Nonce": "-dummy-"}
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(response_data["status"], ProcessingStatuses.done)
        self.assertEqual(response_data["result"], ProcessingResults.success)
        self.assertEqual(response_data["publicReference"], "OF-ABCDE")
        self.assertEqual(response_data["errorMessage"], "")
        self.assertEqual(response_data["confirmationPageTitle"], "Pending (OF-ABCDE)")
        expected_cosign_url = get_frontend_redirect_url(
            submission,
            action="cosign-init",
            action_params={"code": submission.public_registration_reference},
        )
        expected_html = f"""
            <p>Email sent to test@example.com, reference OF-ABCDE.</p>
            <p>Cosign now:
            <a href="{expected_cosign_url}">
                <button class="utrecht-button utrecht-button--primary-action" type="button">
                    Cosign now
                </button>
            </a></p>
            """
        self.assertHTMLEqual(response_data["confirmationPageContent"], expected_html)
        self.assertTrue(
            response_data["reportDownloadUrl"].startswith("http://testserver")
        )
        # no payment configured/required -> no URL
        self.assertEqual(response_data["paymentUrl"], "")


@patch("openforms.submissions.status.AsyncResult.forget", return_value=None)
class CleanupTaskTests(TestCase):
    def setUp(self):
        super().setUp()
        self.addCleanup(GlobalConfiguration.clear_cache)

    def test_incomplete_submission(self, mock_forget):
        SubmissionFactory.create(
            completed=False,
            suspended_on=None,
        )

        cleanup_on_completion_results()

        mock_forget.assert_not_called()

    def test_complete_but_too_young(self, mock_forget):
        SubmissionFactory.create(
            completed=True,
            completed_on=timezone.now() - timedelta(seconds=10),
            suspended_on=None,
        )

        cleanup_on_completion_results()

        mock_forget.assert_not_called()

    def test_suspended(self, mock_forget):
        SubmissionFactory.create(
            completed=False,
            suspended_on=timezone.now() - timedelta(seconds=10),
        )

        cleanup_on_completion_results()

        mock_forget.assert_not_called()

    def test_completed_and_old_enough(self, mock_forget):
        submission = SubmissionFactory.create(
            completed=True,
            completed_on=timezone.now() - timedelta(days=2, seconds=10),
            suspended_on=None,
        )

        cleanup_on_completion_results()

        mock_forget.assert_called_once_with()
        submission.refresh_from_db()
        self.assertEqual(submission.post_completion_task_ids, [])

    def test_multiple_cleanup_calls_only_forget_once(self, mock_forget):
        SubmissionFactory.create(
            completed=True,
            completed_on=timezone.now() - timedelta(days=2, seconds=10),
            suspended_on=None,
        )

        cleanup_on_completion_results()
        cleanup_on_completion_results()

        mock_forget.assert_called_once_with()

    def test_cleanup_skips_completed_submissions_without_tasks(self, mock_forget):
        SubmissionFactory.create(
            completed=True,
            completed_on=timezone.now() - timedelta(days=2, seconds=10),
            suspended_on=None,
            metadata__tasks_ids=[],
        )

        cleanup_on_completion_results()

        mock_forget.assert_not_called()

    def test_cleanup_for_submission_with_multiple_post_completion_events(
        self, mock_forget
    ):
        submission = SubmissionFactory.create(
            completed=True,
            completed_on=timezone.now() - timedelta(days=2, seconds=10),
            suspended_on=None,
        )
        submission.postcompletionmetadata_set.all().delete()

        PostCompletionMetadataFactory.create(
            submission=submission,
            tasks_ids=["some-id-1", "some-id-2"],
            trigger_event=PostSubmissionEvents.on_completion,
        )
        PostCompletionMetadataFactory.create(
            submission=submission,
            tasks_ids=["some-id-3"],
            trigger_event=PostSubmissionEvents.on_cosign_complete,
        )
        PostCompletionMetadataFactory.create(
            submission=submission,
            tasks_ids=[],
            trigger_event=PostSubmissionEvents.on_payment_complete,
        )

        cleanup_on_completion_results()

        self.assertEqual(3, mock_forget.call_count)

    def test_cleanup_for_submission_without_any_metadata(self, mock_forget):
        submission = SubmissionFactory.create(
            completed=True,
            completed_on=timezone.now() - timedelta(days=2, seconds=10),
            suspended_on=None,
        )
        submission.postcompletionmetadata_set.all().delete()

        cleanup_on_completion_results()

        self.assertEqual(0, mock_forget.call_count)
