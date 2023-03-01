"""
Test suspending a form.

Suspension of the form is an explicit action (api-wise), by making a POST call on a
sub-resource.

The backend collects information to send an e-mail to the user for resuming, for
example.
"""
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch
from urllib.parse import urljoin

from django.core import mail
from django.template import defaulttags
from django.test import override_settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

import dateutil
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import UserFactory
from openforms.authentication.constants import AuthAttribute
from openforms.config.models import GlobalConfiguration
from openforms.forms.tests.factories import FormFactory, FormStepFactory
from openforms.utils.tests.cache import clear_caches

from ..constants import SUBMISSIONS_SESSION_KEY
from ..tokens import submission_resume_token_generator
from .factories import SubmissionFactory, SubmissionStepFactory
from .mixins import SubmissionsMixin


class SubmissionSuspensionTests(SubmissionsMixin, APITestCase):
    def setUp(self):
        # clear caches to avoid problems with throttling; @override_settings not working
        # see https://github.com/encode/django-rest-framework/issues/6030
        self.addCleanup(clear_caches)
        super().setUp()

    def test_invalid_submission_id(self):
        submission = SubmissionFactory.create()
        endpoint = reverse("api:submission-suspend", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @freeze_time("2020-12-11T10:53:19+01:00")
    def test_suspended_submission(self):
        form = FormFactory.create()
        FormStepFactory.create(form=form)
        step2 = FormStepFactory.create(form=form)
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission, form_step=step2, data={"foo": "bar"}
        )
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-suspend", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint, {"email": "hello@open-forms.nl"})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        submission.refresh_from_db()
        self.assertEqual(submission.suspended_on, timezone.now())

        # test that submission ID is not removed from session
        submissions_in_session = response.wsgi_request.session[SUBMISSIONS_SESSION_KEY]
        self.assertIn(str(submission.uuid), submissions_in_session)

    @patch(
        "openforms.api.exception_handling.uuid.uuid4",
        return_value="95a55a81-d316-44e8-b090-0519dd21be5f",
    )
    def test_missing_email(self, _mock):
        form = FormFactory.create()
        FormStepFactory.create(form=form)
        step2 = FormStepFactory.create(form=form)
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission, form_step=step2, data={"foo": "bar"}
        )
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-suspend", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {
                "type": "http://testserver/fouten/ValidationError/",
                "code": "invalid",
                "title": _("Invalid input."),
                "status": 400,
                "detail": "",
                "instance": "urn:uuid:95a55a81-d316-44e8-b090-0519dd21be5f",
                "invalidParams": [
                    {
                        "name": "email",
                        "code": "required",
                        "reason": _("This field is required."),
                    }
                ],
            },
        )
        submission.refresh_from_db()
        self.assertIsNone(submission.suspended_on)

    @freeze_time("2021-11-15")
    @patch(
        "openforms.submissions.api.serializers.GlobalConfiguration.get_solo",
        return_value=GlobalConfiguration(
            save_form_email_subject="Saved form {{ form_name }}"
        ),
    )
    def test_email_sent(self, *mocks):
        submission = SubmissionFactory.create()
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-suspend", kwargs={"uuid": submission.uuid})

        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            response = self.client.post(endpoint, {"email": "hello@open-forms.nl"})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(callbacks), 1)
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        self.assertEqual(email.to, ["hello@open-forms.nl"])
        self.assertEqual(email.subject, f"Saved form {submission.form.name}")

        self.assertIn(submission.form.name, email.body)
        self.assertIn(defaulttags.date(timezone.now()), email.body)

        submission.refresh_from_db()
        token = submission_resume_token_generator.make_token(submission)
        resume_path = reverse(
            "submissions:resume",
            kwargs={
                "token": token,
                "submission_uuid": submission.uuid,
            },
        )
        expected_resume_url = urljoin("http://testserver", resume_path)

        self.assertIn(expected_resume_url, email.body)

        datetime_removed = datetime(2021, 11, 22, 12, 00, 00, tzinfo=timezone.utc)

        self.assertIn(defaulttags.date(datetime_removed), email.body)

    @freeze_time("2021-11-15")
    @patch("openforms.submissions.api.serializers.GlobalConfiguration.get_solo")
    @override_settings(LANGUAGE_CODE="nl")
    def test_email_sent_with_custom_configuration(self, m_solo):
        m_solo.return_value = GlobalConfiguration(
            save_form_email_subject="The Subject: {{ form_name }}",
            save_form_email_content="The Content: {{ form_name }} ({{ save_date }})",
        )

        submission = SubmissionFactory.create(form__name="Form 000")
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-suspend", kwargs={"uuid": submission.uuid})

        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            response = self.client.post(endpoint, {"email": "hello@open-forms.nl"})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(callbacks), 1)
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        self.assertEqual(email.to, ["hello@open-forms.nl"])
        self.assertEqual(email.subject, "The Subject: Form 000")
        self.assertEqual(
            email.body.strip(), "The Content: Form 000 (15 november 2021 01:00)"
        )

    @freeze_time("2020-11-15T12:00:00+01:00")
    def test_resume_url_does_not_work_after_submission_has_been_completed(self):
        form = FormFactory.create()
        FormStepFactory.create(form=form)
        step2 = FormStepFactory.create(form=form)
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission, form_step=step2, data={"foo": "bar"}
        )
        self._add_submission_to_session(submission)

        # Suspend the submission
        endpoint = reverse("api:submission-suspend", kwargs={"uuid": submission.uuid})
        response = self.client.post(endpoint, {"email": "hello@open-forms.nl"})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        submission.refresh_from_db()
        self.assertEqual(submission.suspended_on, timezone.now())

        # Get suspended link and resume submission
        submission.refresh_from_db()
        token = submission_resume_token_generator.make_token(submission)
        resume_path = reverse(
            "submissions:resume",
            kwargs={
                "token": token,
                "submission_uuid": submission.uuid,
            },
        )

        response = self.client.get(resume_path)
        self.assertEqual(response.status_code, 302)

        # Complete the submission
        submission.completed_on = timezone.now()
        submission.save(update_fields=["completed_on"])

        # Validate the link no longer works
        response = self.client.get(resume_path)
        self.assertEqual(response.status_code, 403)


class SuspendedSubmissionAPIMockData:
    """
    re-usable dataset to reduce setup code volume
    """

    def __init__(self):
        self.bsn = "123456789"

        self.submission = SubmissionFactory.create(
            form__name="form ok1 (value not hashed)",
            uuid="aaaaaaaa-0001-aaaa-aaaa-aaaaaaaaaaaa",
            suspended_on=timezone.now(),
            completed_on=None,
            auth_info__value=self.bsn,
            auth_info__attribute=AuthAttribute.bsn,
            # NOTE the suspended submissions aren't hashed
            auth_info__attribute_hashed=False,
        )
        self.listable_for_bsn = [
            self.submission,
            # SubmissionFactory.create(
            #     form__name="form ok2 (value is hashed)",
            #     uuid="aaaaaaaa-0002-aaaa-aaaa-aaaaaaaaaaaa",
            #     auth_info__value=self.bsn,
            #     auth_info__attribute=AuthAttribute.bsn,
            #     # NOTE the suspended trait sets hashed auth value
            #     suspended=True,
            # ),
        ]

        self.not_retrievable = [
            SubmissionFactory.create(
                uuid="bbbbbbbb-0001-bbbb-bbbb-bbbbbbbbbbbb",
                form__name="form completed",
                completed=True,
                auth_info__value=self.bsn,
                auth_info__attribute=AuthAttribute.bsn,
            ),
            SubmissionFactory.create(
                uuid="bbbbbbbb-0002-bbbb-bbbb-bbbbbbbbbbbb",
                form__name="suspended too long ago (via global config)",
                suspended_on=timezone.now() - timedelta(days=10),
                completed_on=None,
                auth_info__value=self.bsn,
                auth_info__attribute=AuthAttribute.bsn,
            ),
            SubmissionFactory.create(
                uuid="bbbbbbbb-0003-bbbb-bbbb-bbbbbbbbbbbb",
                form__name="suspended too long ago (via form config)",
                form__incomplete_submissions_removal_limit=1,
                suspended_on=timezone.now() - timedelta(days=2),
                completed_on=None,
                auth_info__value=self.bsn,
                auth_info__attribute=AuthAttribute.bsn,
            ),
            SubmissionFactory.create(
                uuid="bbbbbbbb-0004-bbbb-bbbb-bbbbbbbbbbbb",
                form__name="not our auth attribute",
                suspended_on=timezone.now(),
                completed_on=None,
                auth_info__value=self.bsn,
                auth_info__attribute=AuthAttribute.kvk,
            ),
            SubmissionFactory.create(
                uuid="bbbbbbbb-0005-bbbb-bbbb-bbbbbbbbbbbb",
                form__name="both dates",
                suspended_on=timezone.now(),
                completed_on=timezone.now(),
                auth_info__value=self.bsn,
                auth_info__attribute=AuthAttribute.bsn,
            ),
            SubmissionFactory.create(
                uuid="bbbbbbbb-0006-bbbb-bbbb-bbbbbbbbbbbb",
                form__name="null dates",
                suspended_on=None,
                completed_on=None,
                auth_info__value=self.bsn,
                auth_info__attribute=AuthAttribute.bsn,
            ),
            SubmissionFactory.create(
                uuid="bbbbbbbb-0007-bbbb-bbbb-bbbbbbbbbbbb",
                form__name="hashed BSN",
                suspended_on=None,
                completed_on=None,
                auth_info__value="[some hash value]",
                auth_info__attribute=AuthAttribute.bsn,
                auth_info__attribute_hashed=True,
            ),
        ]
        self.not_listable_for_bsn = self.not_retrievable + [
            SubmissionFactory.create(
                uuid="bbbbbbbb-0008-bbbb-bbbb-bbbbbbbbbbbb",
                form__name="not our BSN value",
                suspended_on=timezone.now(),
                completed_on=None,
                auth_info__value="999999999",
                auth_info__attribute=AuthAttribute.bsn,
            ),
        ]


@freeze_time("2022-01-01")
class SuspendedSubmissionListAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.endpoint = reverse("api:submission-suspended-list")

    @patch("openforms.forms.admin.mixins.GlobalConfiguration.get_solo")
    def test_api_lists_suspended_submissions_for_bsn(self, mock_get_solo):
        mock_get_solo.return_value = GlobalConfiguration(
            incomplete_submissions_removal_limit=7
        )

        data = SuspendedSubmissionAPIMockData()

        user = UserFactory(user_permissions=["submissions.list_suspended_submissions"])
        self.client.force_authenticate(user=user)

        with self.subTest("with our BSN"):
            response = self.client.get(f"{self.endpoint}?bsn={data.bsn}")
            self.assertEqual(response.status_code, 200)
            data = response.json()

            # check only our suspended submissions for this BSN are listed
            actual_uuids = {r["naam"] for r in data["results"]}
            expected_uuids = {s.form.name for s in data.listable_for_bsn}
            self.assertEqual(actual_uuids, expected_uuids)

            # check we got pagination
            self.assertEqual(data["count"], len(data.listable_for_bsn))
            self.assertEqual(data["previous"], None)
            self.assertEqual(data["next"], None)

            # basic serialisation check (more at retrieve)
            result = data["results"][0]
            expected_fields = {
                "uuid",
                "naam",
                "url",
                "vervolgLink",
                "datumLaatsteWijziging",
                "eindDatumGeldigheid",
            }
            self.assertEqual(set(result.keys()), expected_fields)

        with self.subTest("with other BSN"):
            response = self.client.get(f"{self.endpoint}?bsn=000000000")
            self.assertEqual(response.status_code, 200)
            data = response.json()

            # no results
            self.assertEqual(data["results"], [])

    def test_api_requires_auth(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, 401)

    def test_auth_fails_without_permission(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)

        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, 403)

    def test_auth_requires_permission_and_url_param(self):
        user = UserFactory(user_permissions=["submissions.list_suspended_submissions"])
        self.client.force_authenticate(user=user)

        with self.subTest("without required URL param"):
            response = self.client.get(self.endpoint)
            self.assertEqual(response.status_code, 400)

        with self.subTest("with required URL param"):
            response = self.client.get(f"{self.endpoint}?bsn=123456789")
            self.assertEqual(response.status_code, 200)

    def test_api_allows_safe_method_only(self):
        user = UserFactory(user_permissions=["submissions.list_suspended_submissions"])
        self.client.force_authenticate(user=user)

        for method in ["GET", "HEAD", "OPTIONS"]:
            response = self.client.generic(method, f"{self.endpoint}?bsn=123456789")
            self.assertEqual(response.status_code, 200, method)

        for method in ["POST", "PUT", "PATCH", "DELETE"]:
            response = self.client.generic(method, f"{self.endpoint}?bsn=123456789")
            self.assertEqual(response.status_code, 405, method)


@freeze_time("2022-01-01")
class SuspendedSubmissionRetrieveAPITest(APITestCase):
    def test_api_retrieves_suspended_submissions(self):
        user = UserFactory(user_permissions=["submissions.list_suspended_submissions"])
        self.client.force_authenticate(user=user)

        submission = SubmissionFactory.create(
            form__name="form ok1 (value not hashed)",
            uuid="aaaaaaaa-0001-aaaa-aaaa-aaaaaaaaaaaa",
            suspended_on=timezone.now(),
            completed_on=None,
            auth_info__value="123456789",
            auth_info__attribute=AuthAttribute.bsn,
        )

        url = reverse(
            "api:submission-suspended-detail", kwargs={"uuid": submission.uuid}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # check serialisation
        self.assertEqual(data["uuid"], str(submission.uuid))
        self.assertEqual(data["naam"], "form ok1 (value not hashed)")
        self.assertEqual(
            data["url"],
            "http://testserver"
            + reverse("api:submission-detail", kwargs={"uuid": submission.uuid}),
        )
        self.assertEqual(
            dateutil.parser.parse(data["datumLaatsteWijziging"]), timezone.now()
        )
        self.assertEqual(
            dateutil.parser.parse(data["eindDatumGeldigheid"]),
            (timezone.now() + timedelta(days=7)),
        )
        self.assertRegex(
            data["vervolgLink"],
            f"^http://testserver/submissions/{submission.uuid}/[^/]+/resume$",
        )

    def test_api_does_not_retrieve_invalid_or_not_suspended(self):
        user = UserFactory(user_permissions=["submissions.list_suspended_submissions"])
        self.client.force_authenticate(user=user)

        data = SuspendedSubmissionAPIMockData()

        for submission in data.not_retrievable:
            with self.subTest(submission.form.name):
                url = reverse(
                    "api:submission-suspended-detail", kwargs={"uuid": submission.uuid}
                )
                response = self.client.get(url)
                self.assertEqual(response.status_code, 404)

    def test_api_requires_auth(self):
        url = reverse("api:submission-suspended-detail", kwargs={"uuid": uuid.uuid4()})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def test_auth_fails_without_permission(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)
        url = reverse("api:submission-suspended-detail", kwargs={"uuid": uuid.uuid4()})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_api_allows_safe_method_only(self):
        user = UserFactory(user_permissions=["submissions.list_suspended_submissions"])
        self.client.force_authenticate(user=user)

        url = reverse("api:submission-suspended-detail", kwargs={"uuid": uuid.uuid4()})

        for method in ["GET", "HEAD", "OPTIONS"]:
            response = self.client.generic(method, url)
            self.assertIn(response.status_code, (200, 404), method)

        for method in ["POST", "PUT", "PATCH", "DELETE"]:
            response = self.client.generic(method, url)
            self.assertEqual(response.status_code, 405, method)
