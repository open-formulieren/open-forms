"""
Assert that the session expiry works as intended.

Administrators can configure the maximum session duration. The intent is that the
session expires if there's no activity within that timespan.
"""

from copy import deepcopy
from datetime import datetime
from unittest.mock import patch

from django.conf import settings
from django.contrib import admin
from django.test import override_settings
from django.urls import path
from django.utils import timezone
from django.utils.translation import gettext as _

import csp.constants
from freezegun import freeze_time
from maykin_2fa.test import disable_admin_mfa
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from rest_framework.views import APIView

from openforms.config.models import GlobalConfiguration
from openforms.forms.tests.factories import FormFactory, FormStepFactory

from ..accounts.tests.factories import SuperUserFactory
from .utils import NOOP_CACHES

SESSION_CACHES = deepcopy(NOOP_CACHES)
SESSION_CACHES["session"] = {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}


class SessionTestView(APIView):
    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        return Response({"ok": True})


urlpatterns = [
    path("tests/session", SessionTestView.as_view()),
    path("admin/", admin.site.urls),
]


@override_settings(
    CORS_ALLOW_ALL_ORIGINS=True, CACHES=SESSION_CACHES, SESSION_CACHE_ALIAS="session"
)
class FormUserSessionExpiryTests(APITestCase):
    """
    Session expiry tests for non-admin users.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.form = FormFactory.create()
        cls.steps = FormStepFactory.create_batch(2, form=cls.form)
        cls.form_url = reverse(
            "api:form-detail", kwargs={"uuid_or_slug": cls.form.uuid}
        )

    def setUp(self):
        super().setUp()

        patcher = patch("openforms.middleware.GlobalConfiguration.get_solo")
        self.mock_global_config = patcher.start()
        self.addCleanup(patcher.stop)
        self.mock_global_config.return_value = GlobalConfiguration(
            form_session_timeout=5
        )  # minimum value

    def test_activity_within_expiry_does_not_expire_session(self):
        """
        Assert that any activity within the expiry period postpones the expiry.

        Django's session expiry is calculated against the last time the session is
        _modified_. Posting step submission data does not modify the session, so there
        is a chance the user is active and the session does still expire (which is
        not intended).
        """
        # start the submission - this modifies the session
        with self.subTest(part="start submission"):
            body = {
                "form": f"http://testserver{self.form_url}",
                "formUrl": "http://testserver.com/my-form",
            }
            with freeze_time("2021-07-29T14:00:00Z"):
                response = self.client.post(reverse("api:submission-list"), body)

                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                session = response.wsgi_request.session
                self.assertEqual(session.get_expiry_age(), 300)
                expected_expiry = datetime(2021, 7, 29, 14, 5).replace(
                    tzinfo=timezone.utc
                )
                self.assertEqual(session.get_expiry_date(), expected_expiry)

        # submit the first step, one minute later, simulating some time to fill out the step
        with self.subTest(part="fill out step 1"):
            with freeze_time("2021-07-29T14:01:00Z"):
                step1_response = self.client.put(
                    response.data["steps"][0]["url"], {"data": {"foo": "bar"}}
                )

                self.assertEqual(step1_response.status_code, status.HTTP_201_CREATED)
                session = step1_response.wsgi_request.session
                expected_expiry = datetime(2021, 7, 29, 14, 6).replace(
                    tzinfo=timezone.utc
                )
                self.assertEqual(session.get_expiry_date(), expected_expiry)

        # now, simulate the second step took 4 minutes and 30s to fill out. This puts us
        # 30s after the initial expiry. If the # previous step reset the session expiry,
        # this should go through, because the expiry is now 14:06:00.
        with self.subTest(part="fill out step 2"):
            with freeze_time("2021-07-29T14:05:30Z"):
                step2_response = self.client.put(
                    response.data["steps"][1]["url"], {"data": {"foo": "bar"}}
                )

                self.assertEqual(step2_response.status_code, status.HTTP_201_CREATED)
                session = step2_response.wsgi_request.session
                expected_expiry = datetime(2021, 7, 29, 14, 10, 30).replace(
                    tzinfo=timezone.utc
                )
                self.assertEqual(session.get_expiry_date(), expected_expiry)

    @patch(
        "openforms.api.exception_handling.uuid.uuid4",
        return_value="95a55a81-d316-44e8-b090-0519dd21be5f",
    )
    def test_activity_over_expiry_returns_a_403_error(self, _mock):
        """
        Assert that any activity outside of the expiry period returns a 403.
        """
        # start the submission - this modifies the session
        with self.subTest(part="start submission"):
            body = {
                "form": f"http://testserver{self.form_url}",
                "formUrl": "http://testserver.com/my-form",
            }
            with freeze_time("2021-07-29T14:00:00Z"):
                response = self.client.post(reverse("api:submission-list"), body)

                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                session = response.wsgi_request.session
                self.assertEqual(session.get_expiry_age(), 300)
                expected_expiry = datetime(2021, 7, 29, 14, 5).replace(
                    tzinfo=timezone.utc
                )
                self.assertEqual(session.get_expiry_date(), expected_expiry)

        # submit the first step, 5 and a half minutes later, simulating the session has expired
        with self.subTest(part="fill out step 1"):
            with freeze_time("2021-07-29T14:05:30Z"):
                step1_response = self.client.put(
                    response.data["steps"][0]["url"], {"data": {"foo": "bar"}}
                )

                self.assertEqual(step1_response.status_code, status.HTTP_403_FORBIDDEN)
                self.assertEqual(
                    step1_response.json(),
                    {
                        "type": "http://testserver/fouten/NotAuthenticated/",
                        "code": "not_authenticated",
                        "title": _("Authentication credentials were not provided."),
                        "status": 403,
                        "detail": _("Authentication credentials were not provided."),
                        "instance": "urn:uuid:95a55a81-d316-44e8-b090-0519dd21be5f",
                    },
                )

    @override_settings(
        ROOT_URLCONF=__name__,
        CONTENT_SECURITY_POLICY={
            "DIRECTIVES": {"default-src": [csp.constants.SELF]},
            "REPORT_URI": "/foo",
        },
        CONTENT_SECURITY_POLICY_REPORT_ONLY={},
    )
    def test_session_expiry_header_included(self):
        """
        Assert that the response contains a header indicating when the session expires.
        """
        response = self.client.get("/tests/session")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response["X-Session-Expires-In"], "300"
        )  # 5 minutes * 60s = 300s


@disable_admin_mfa()
@override_settings(
    CACHES=SESSION_CACHES,
    SESSION_CACHE_ALIAS="session",
)
class AdminSessionExpiryTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        config = GlobalConfiguration.get_solo()
        config.admin_session_timeout = 5  # minimum value
        config.save()

        # Just a random admin url to use for testing
        cls.url = reverse("admin:submissions_submission_changelist")
        cls.superuser = SuperUserFactory.create()

    def setUp(self):
        super().setUp()
        self.client.force_login(self.superuser)

    def test_admin_activity_session_timeout(self):
        """
        Assert that any activity outside of the expiry period returns a 302
        and redirects the admin to the login page
        """
        # make a request to the admin to validate this modifies the session
        with self.subTest(part="initial check"):
            with freeze_time("2021-07-29T14:00:00Z"):
                response = self.client.get(self.url, user=self.superuser)

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                session = response.wsgi_request.session
                self.assertEqual(session.get_expiry_age(), 300)
                expected_expiry = datetime(2021, 7, 29, 14, 5).replace(
                    tzinfo=timezone.utc
                )
                self.assertEqual(session.get_expiry_date(), expected_expiry)

        # make another request to the admin to validate the session has not expired yet
        with self.subTest(part="check not expired"):
            with freeze_time("2021-07-29T14:04:00Z"):
                response = self.client.get(self.url, user=self.superuser)

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                session = response.wsgi_request.session
                self.assertEqual(session.get_expiry_age(), 300)
                expected_expiry = datetime(2021, 7, 29, 14, 9).replace(
                    tzinfo=timezone.utc
                )
                self.assertEqual(session.get_expiry_date(), expected_expiry)

        # make another request to the admin to validate the session has expired
        #  and the user will be redirected to the admin login page
        with self.subTest(part="check expired and redirection to login page"):
            with freeze_time("2021-07-29T14:10:00Z"):
                response = self.client.get(self.url, user=self.superuser)

                self.assertEqual(response.status_code, status.HTTP_302_FOUND)
                self.assertEqual(response.url, f"{settings.LOGIN_URL}?next={self.url}")
