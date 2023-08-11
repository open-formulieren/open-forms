from unittest.mock import patch

from django.test import override_settings
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from openforms.submissions.tests.factories import SubmissionFactory
from openforms.submissions.tests.mixins import SubmissionsMixin

from ...models import GlobalConfiguration


@override_settings(LANGUAGE_CODE="en")
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
            'I read the <a href="http://example-privacy.com" target="_blank" '
            'rel="noreferrer noopener">privacy policy</a>',
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


@override_settings(LANGUAGE_CODE="en")
class DeclarationsInfoListViewTests(SubmissionsMixin, APITestCase):
    def test_requires_active_submission(self):
        response = self.client.get(reverse("api:config:statements-info-list"))

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

    def test_returns_list_checkboxes(self):
        conf = GlobalConfiguration(
            ask_privacy_consent=True,
            privacy_policy_url="http://example-privacy.com",
            privacy_policy_label="I read the {% privacy_policy %}",
            ask_statement_of_truth=True,
            statement_of_truth_label="I am honest",
        )
        submission = SubmissionFactory.create()
        self._add_submission_to_session(submission)

        with patch(
            "openforms.config.api.views.GlobalConfiguration.get_solo", return_value=conf
        ):
            response = self.client.get(reverse("api:config:statements-info-list"))

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        data = response.json()

        privacy_checkbox = data[0]
        self.assertTrue(privacy_checkbox["validate"]["required"])
        self.assertHTMLEqual(
            'I read the <a href="http://example-privacy.com" target="_blank" '
            'rel="noreferrer noopener">privacy policy</a>',
            privacy_checkbox["label"],
        )
        self.assertEqual(privacy_checkbox["key"], "privacyPolicyAccepted")

        truth_checkbox = data[1]
        self.assertTrue(truth_checkbox["validate"]["required"])
        self.assertHTMLEqual(
            "I am honest",
            truth_checkbox["label"],
        )
        self.assertEqual(truth_checkbox["key"], "statementOfTruthAccepted")

    def test_declarations_not_required(self):
        conf = GlobalConfiguration(
            ask_privacy_consent=False,
            privacy_policy_url="http://example-privacy.com",
            privacy_policy_label="I read the {% privacy_policy %}",
            ask_statement_of_truth=False,
            statement_of_truth_label="I am honest",
        )
        submission = SubmissionFactory.create()
        self._add_submission_to_session(submission)

        with patch(
            "openforms.config.api.views.GlobalConfiguration.get_solo", return_value=conf
        ):
            response = self.client.get(reverse("api:config:statements-info-list"))

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        data = response.json()

        privacy_checkbox = data[0]
        self.assertFalse(privacy_checkbox["validate"]["required"])
        self.assertHTMLEqual(
            'I read the <a href="http://example-privacy.com" target="_blank" '
            'rel="noreferrer noopener">privacy policy</a>',
            privacy_checkbox["label"],
        )
        self.assertEqual(privacy_checkbox["key"], "privacyPolicyAccepted")

        truth_checkbox = data[1]
        self.assertFalse(truth_checkbox["validate"]["required"])
        self.assertHTMLEqual(
            "I am honest",
            truth_checkbox["label"],
        )
        self.assertEqual(truth_checkbox["key"], "statementOfTruthAccepted")
