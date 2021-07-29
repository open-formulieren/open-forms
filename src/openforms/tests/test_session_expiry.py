"""
Assert that the session expiry works as intended.

Administrators can configure the maximum session duration. The intent is that the
session expires if there's no activity within that timespan.
"""
from datetime import datetime

from django.test import override_settings
from django.utils import timezone

from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.config.models import GlobalConfiguration
from openforms.forms.tests.factories import FormFactory, FormStepFactory

from .utils import NOOP_CACHES


@override_settings(CACHES=NOOP_CACHES)
class FormUserSessionExpiryTests(APITestCase):
    """
    Session expiry tests for non-admin users.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        config = GlobalConfiguration.get_solo()
        config.form_session_timeout = 5  # minimum value
        config.save()

        cls.form = FormFactory.create()
        cls.steps = FormStepFactory.create_batch(2, form=cls.form)
        cls.form_url = reverse(
            "api:form-detail", kwargs={"uuid_or_slug": cls.form.uuid}
        )

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
