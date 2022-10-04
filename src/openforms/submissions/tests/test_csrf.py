from django.test import override_settings

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient, APITestCase

from openforms.forms.tests.factories import FormFactory

from .factories import SubmissionFactory
from .mixins import SubmissionsMixin


class CSRFAPIClient(APIClient):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("enforce_csrf_checks", True)
        super().__init__(*args, **kwargs)


@override_settings(ALLOWED_HOSTS=["testserver", "testserver.com"])
class CSRFForAnonymousUsersTests(SubmissionsMixin, APITestCase):
    client_class = CSRFAPIClient

    def test_anonymous_user_submission_start_require_csrf_token(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__login_required=False,
        )
        form_url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        form_response = self.client.get(form_url)

        body = {
            "form": f"http://testserver.com{form_url}",
            "formUrl": "http://testserver.com/my-form",
        }

        with self.subTest("missing CSRF token"):
            response = self.client.post(
                reverse("api:submission-list"),
                body,
                HTTP_HOST="testserver.com",
            )

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        with self.subTest("CSRF token included"):
            csrf_value = form_response.headers["X-CSRFToken"]

            response = self.client.post(
                reverse("api:submission-list"),
                body,
                HTTP_HOST="testserver.com",
                HTTP_X_CSRFTOKEN=csrf_value,
            )

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_anonymous_user_put_step_data_require_csrf_token(self):
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__login_required=False,
        )
        submission_response = self.client.get(
            reverse("api:submission-detail", kwargs={"uuid": submission.uuid})
        )
        self._add_submission_to_session(submission)
        endpoint = reverse(
            "api:submission-steps-detail",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": submission.form.formstep_set.get().uuid,
            },
        )
        body = {"data": {"component1": "henlo"}}

        with self.subTest("missing CSRF token"):
            response = self.client.put(endpoint, body)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        with self.subTest("CSRF token included"):
            csrf_value = submission_response.headers["X-CSRFToken"]

            response = self.client.put(
                endpoint,
                body,
                HTTP_X_CSRFTOKEN=csrf_value,
            )

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
