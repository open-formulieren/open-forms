from django.test import override_settings
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from openforms.forms.tests.factories import FormFactory
from openforms.submissions.models import Submission


class TranslationSignalTestCase(APITestCase):
    @override_settings(CORS_ALLOW_ALL_ORIGINS=True)
    def test_submission_start_set_language_code(self):
        form = FormFactory.create()

        response = self.client.post(
            reverse("api:submission-list"),
            data={
                "form": reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid}),
                "formUrl": "http://testserver.com/foo",
            },
            HTTP_ACCEPT_LANGUAGE="en",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        submission = Submission.objects.get()

        self.assertEqual(submission.language_code, "en")

    @override_settings(CORS_ALLOW_ALL_ORIGINS=True)
    def test_submission_start_set_language_code_default(self):
        form = FormFactory.create()

        response = self.client.post(
            reverse("api:submission-list"),
            data={
                "form": reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid}),
                "formUrl": "http://testserver.com/foo",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        submission = Submission.objects.get()

        self.assertEqual(submission.language_code, "nl")
