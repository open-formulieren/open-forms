from django.test import override_settings
from django.utils.translation import gettext as _

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.authentication.service import FORM_AUTH_SESSION_KEY, AuthAttribute
from openforms.forms.tests.factories import (
    FormFactory,
)
from openforms.logging.models import TimelineLogProxy

from ..models import Submission


class LogEventTests(APITestCase):
    """
    Test that log events are emitted for submissions.
    """

    def _start_submission(self) -> Submission:
        form = FormFactory.create()
        form_url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        endpoint = reverse("api:submission-list")
        body = {
            "form": f"http://testserver.com{form_url}",
            "formUrl": "http://testserver.com/my-form",
        }

        with override_settings(
            CORS_ALLOW_ALL_ORIGINS=False,
            ALLOWED_HOSTS=["*"],
            CORS_ALLOWED_ORIGINS=["http://testserver.com"],
        ):
            response = self.client.post(endpoint, body, HTTP_HOST="testserver.com")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return Submission.objects.get(uuid=response.json()["id"])

    def test_submission_start(self):
        with self.subTest("anon"):
            # Github #1467
            submission_1 = self._start_submission()

            log_1 = TimelineLogProxy.objects.for_object(submission_1).last()
            assert log_1 is not None
            self.assertEqual(log_1.fmt_user, _("Anonymous user"))

        with self.subTest("auth bsn"):
            session = self.client.session
            session[FORM_AUTH_SESSION_KEY] = {
                "plugin": "digid",
                "attribute": AuthAttribute.bsn,
                "value": "123456789",
            }
            session.save()

            submission_2 = self._start_submission()

            log_2 = TimelineLogProxy.objects.for_object(submission_2).last()
            assert log_2 is not None
            self.assertEqual(
                log_2.fmt_user,
                _("Authenticated via plugin {auth}").format(auth="digid (bsn)"),
            )
