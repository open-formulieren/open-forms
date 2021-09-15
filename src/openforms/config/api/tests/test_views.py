from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from openforms.submissions.tests.factories import SubmissionFactory
from openforms.submissions.tests.mixins import SubmissionsMixin

from ...models import GlobalConfiguration


class PrivacyInfoViewTests(SubmissionsMixin, APITestCase):
    def test_requires_active_submission(self):
        response = self.client.get(reverse("api:config:privacy-policy-info"))

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

    def test_returns_privacy_label(self):
        conf = GlobalConfiguration.get_solo()
        conf.ask_privacy_consent = True
        conf.privacy_policy_url = "http://example-privacy.com"
        conf.privacy_policy_label = "I read the {% privacy_policy %}"
        conf.save()
        submission = SubmissionFactory.create()
        self._add_submission_to_session(submission)

        response = self.client.get(reverse("api:config:privacy-policy-info"))

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        data = response.json()

        self.assertEqual(True, data["requiresPrivacyConsent"])
        self.assertHTMLEqual(
            'I read the <a href="http://example-privacy.com">privacy policy</a>',
            data["privacyLabel"],
        )

    def test_doesnt_require_policy_consent(self):
        conf = GlobalConfiguration.get_solo()
        conf.ask_privacy_consent = False
        conf.save()
        submission = SubmissionFactory.create()
        self._add_submission_to_session(submission)

        response = self.client.get(reverse("api:config:privacy-policy-info"))

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        data = response.json()

        self.assertEqual(False, data["requiresPrivacyConsent"])
        self.assertIsNone(data["privacyLabel"])
