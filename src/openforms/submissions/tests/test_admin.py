from decimal import Decimal
from unittest.mock import patch

from django.contrib.admin import AdminSite
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from django_webtest import WebTest
from freezegun import freeze_time
from furl import furl
from maykin_2fa.test import disable_admin_mfa

from openforms.accounts.tests.factories import UserFactory
from openforms.forms.tests.factories import FormVariableFactory
from openforms.logging.logevent import submission_start
from openforms.logging.models import TimelineLogProxy
from openforms.submissions.models.submission import Submission
from openforms.variables.constants import FormVariableDataTypes

from ...config.models import GlobalConfiguration
from ..admin import SubmissionAdmin, SubmissionTimeListFilter
from ..constants import PostSubmissionEvents, RegistrationStatuses
from .factories import SubmissionFactory


@disable_admin_mfa()
class TestSubmissionAdmin(WebTest):
    @classmethod
    def setUpTestData(cls):
        cls.submission_1 = SubmissionFactory.from_components(
            [
                {"type": "textfield", "key": "adres"},
                {"type": "textfield", "key": "voornaam"},
                {"type": "textfield", "key": "familienaam"},
                {"type": "date", "key": "geboortedatum"},
                {"type": "signature", "key": "signature"},
            ],
            submitted_data={
                "adres": "Voorburg",
                "voornaam": "shea",
                "familienaam": "meyers",
            },
            completed=True,
        )

        cls.submission_step_1 = cls.submission_1.steps[0]

    def setUp(self):
        super().setUp()
        self.user = UserFactory.create(is_superuser=True, is_staff=True)

    def test_viewing_submission_details_in_admin_creates_log(self):
        self.app.get(
            reverse(
                "admin:submissions_submission_change", args=(self.submission_1.pk,)
            ),
            user=self.user,
        )

        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/submission_details_view_admin.txt"
            ).count(),
            1,
        )

    @patch("openforms.submissions.admin.on_post_submission_event")
    def test_retry_processing_submissions_only_resends_failed_submissions(
        self, mock_on_post_submission_event
    ):
        failed = SubmissionFactory.create(
            needs_on_completion_retry=True,
            completed=True,
            registration_status=RegistrationStatuses.failed,
        )
        not_failed = SubmissionFactory.create(
            needs_on_completion_retry=False,
            completed=True,
            registration_status=RegistrationStatuses.pending,
        )

        response = self.app.get(
            reverse("admin:submissions_submission_changelist"), user=self.user
        )

        form = response.forms["changelist-form"]
        form["action"] = "retry_processing_submissions"
        form["_selected_action"] = [str(failed.pk), str(not_failed.pk)]

        form.submit()

        mock_on_post_submission_event.assert_called_once_with(
            failed.id, PostSubmissionEvents.on_retry
        )

    @patch("openforms.submissions.admin.on_post_submission_event")
    def test_retry_processing_submissions_resends_all_failed_submissions(
        self, mock_on_post_submission_event
    ):
        failed = SubmissionFactory.create(
            needs_on_completion_retry=False,
            completed=True,
            registration_status=RegistrationStatuses.failed,
        )
        failed_needs_retry = SubmissionFactory.create(
            needs_on_completion_retry=True,
            completed=True,
            registration_status=RegistrationStatuses.failed,
        )
        pending = SubmissionFactory.create(
            needs_on_completion_retry=False,
            completed=True,
            registration_status=RegistrationStatuses.pending,
        )
        pending_needs_retry = SubmissionFactory.create(
            needs_on_completion_retry=True,
            completed=True,
            registration_status=RegistrationStatuses.pending,
        )

        response = self.app.get(
            reverse("admin:submissions_submission_changelist"), user=self.user
        )

        form = response.forms["changelist-form"]
        form["action"] = "retry_processing_submissions"
        form["_selected_action"] = [
            str(failed.pk),
            str(failed_needs_retry.pk),
            str(pending.pk),
            str(pending_needs_retry.pk),
        ]

        form.submit()

        mock_on_post_submission_event.assert_any_call(
            failed.id, PostSubmissionEvents.on_retry
        )
        mock_on_post_submission_event.assert_any_call(
            failed_needs_retry.id, PostSubmissionEvents.on_retry
        )
        self.assertEqual(mock_on_post_submission_event.call_count, 2)

    @patch("openforms.submissions.admin.on_post_submission_event")
    @patch("openforms.registrations.tasks.GlobalConfiguration.get_solo")
    def test_retry_processing_submissions_resets_submission_registration_attempts(
        self, mock_get_solo, mock_on_post_submission_event
    ):
        mock_get_solo.return_value = GlobalConfiguration(registration_attempt_limit=5)

        failed_above_limit = SubmissionFactory.create(
            completed=True,
            registration_status=RegistrationStatuses.failed,
            registration_attempts=10,
        )
        failed_below_limit = SubmissionFactory.create(
            completed=True,
            registration_status=RegistrationStatuses.failed,
            registration_attempts=2,
        )

        response = self.app.get(
            reverse("admin:submissions_submission_changelist"), user=self.user
        )

        form = response.forms["changelist-form"]
        form["action"] = "retry_processing_submissions"
        form["_selected_action"] = [
            str(failed_above_limit.pk),
            str(failed_below_limit.pk),
        ]

        form.submit()

        mock_on_post_submission_event.assert_any_call(
            failed_above_limit.id, PostSubmissionEvents.on_retry
        )
        mock_on_post_submission_event.assert_any_call(
            failed_below_limit.id, PostSubmissionEvents.on_retry
        )
        self.assertEqual(mock_on_post_submission_event.call_count, 2)

        failed_above_limit.refresh_from_db()
        failed_below_limit.refresh_from_db()

        self.assertEqual(failed_above_limit.registration_attempts, 0)
        self.assertEqual(failed_below_limit.registration_attempts, 0)

    def test_change_view_displays_logs_if_not_avg(self):
        # add regular submission log
        submission_start(self.submission_1)

        # viewing this generates an AVG log
        response = self.app.get(
            reverse(
                "admin:submissions_submission_change", args=(self.submission_1.pk,)
            ),
            user=self.user,
        )
        start_log, avg_log = TimelineLogProxy.objects.order_by("pk")

        # regular log visible
        self.assertContains(response, start_log.get_message())

        # avg log not visible
        self.assertNotContains(response, avg_log.get_message())

    def test_search(self):
        list_url = furl(reverse("admin:submissions_submission_changelist"))
        list_url.args["q"] = "some value"

        response = self.app.get(
            list_url.url,
            user=self.user,
        )

        self.assertEqual(200, response.status_code)

    def test_change_view(self):
        change_url = reverse(
            "admin:submissions_submission_change", kwargs={"object_id": "0"}
        )
        self.app.get(change_url, user=self.user, status=404)

    def test_change_view_with_broken_price_variable_config(self):
        submission = SubmissionFactory.create(
            completed=True,
            form__generate_minimal_setup=False,
            form__product__price=Decimal("123.45"),
            form__payment_backend="demo",
            form__price_variable_key="",
        )
        FormVariableFactory.create(
            user_defined=True,
            key="calculatedPrice",
            form=submission.form,
            data_type=FormVariableDataTypes.string,
            initial_value="bwoken",
        )
        submission.form.price_variable_key = "calculatedPrice"
        submission.form.save()
        change_url = reverse(
            "admin:submissions_submission_change", kwargs={"object_id": submission.pk}
        )

        change_page = self.app.get(change_url, user=self.user)

        self.assertEqual(change_page.status_code, 200)


class TestSubmissionTimeListFilterAdmin(TestCase):
    def test_time_filtering(self):
        with freeze_time("2023-04-02T12:30:00+01:00"):
            # registered in the past 24 hours
            submission_1 = SubmissionFactory.create(
                last_register_date=timezone.now(),
                registration_status=RegistrationStatuses.failed,
            )

        with freeze_time("2023-01-02T12:30:00+01:00"):
            # registered out of filtering bounds
            submission_2 = SubmissionFactory.create(
                last_register_date=timezone.now(),
                registration_status=RegistrationStatuses.failed,
            )

        with freeze_time("2023-04-02T18:30:00+01:00"):
            site = AdminSite()
            model_admin = SubmissionAdmin(Submission, site)
            filter_instance = SubmissionTimeListFilter(
                request=None,
                params={"registration_time": "24hAgo"},
                model=Submission,
                model_admin=model_admin,
            )

            queryset = Submission.objects.all()
            filtered_queryset = filter_instance.queryset(None, queryset)

        self.assertQuerySetEqual(queryset, [submission_1, submission_2], ordered=False)
        self.assertQuerySetEqual(filtered_queryset, [submission_1], ordered=False)
