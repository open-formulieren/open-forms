import hashlib
from unittest.mock import patch

from celery import states
from csp.middleware import CSPMiddleware
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIRequestFactory, APITestCase

from openforms.config.models import GlobalConfiguration
from openforms.forms.tests.factories import FormFactory
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.submissions.tokens import submission_status_token_generator

NONCE_HTTP_HEADER = "HTTP_X_CSP_NONCE"


def md5hash(value: str) -> str:
    md5 = hashlib.md5(value.encode("ascii"))
    return md5.hexdigest()


class CSPMixin:
    def setUp(self):
        super().setUp()

        self.setUpNonce()
        self.setUpMocks()

    def setUpNonce(self):
        middleware = CSPMiddleware(get_response=lambda req: None)
        factory = APIRequestFactory()
        request = factory.get("/irrelevant")
        middleware._make_nonce(request)

        self.csp_nonce = request._csp_nonce

    def setUpMocks(self):
        patcher = patch("csp_post_processor.processor.get_html_id", return_value="1234")
        self.mock_get_html_id = patcher.start()
        self.addCleanup(patcher.stop)


class FormInlineStyleCSPTests(CSPMixin, APITestCase):
    """
    Assert that WYSIWYG content in the API responses is post-processed.

    The post-processing must convert inline attribute styles
    (``<span style="...">...</span>``) into an inline style element
    (``<style nonce="...">...</style>``) if a CSP nonce is provided.

    This testcase collects all the API endpoints/resources with such fields.
    """

    def test_form_explanation_template_html(self):
        form = FormFactory.create(
            explanation_template="""
            <p>This is some <span style="color: red;">inline styled</span> HTML.</p>
            """
        )
        endpoint = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})

        response = self.client.get(endpoint, **{NONCE_HTTP_HEADER: self.csp_nonce})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        html_id = f"nonce-{md5hash(self.csp_nonce)}-1234"
        expected = f"""
        <style nonce="{self.csp_nonce}">
            #{html_id} {{
                color: red;
            }}
        </style>
        <p>This is some <span id="{html_id}">inline styled</span> HTML.</p>
        """
        self.assertHTMLEqual(response.json()["explanationTemplate"], expected)

    def test_form_explanation_template_plain_text(self):
        form = FormFactory.create(
            explanation_template='This is some style="color: red;" that should be untouched.'
        )
        endpoint = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})

        response = self.client.get(endpoint, **{NONCE_HTTP_HEADER: self.csp_nonce})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected = 'This is some style="color: red;" that should be untouched.'
        self.assertEqual(response.json()["explanationTemplate"], expected)


@patch("openforms.submissions.status.AsyncResult")
@patch(
    "openforms.submissions.models.submission.GlobalConfiguration.get_solo",
    return_value=GlobalConfiguration(),
)
class SubmissionConfirmationInlineStyleCSPTests(CSPMixin, APITestCase):
    def test_form_level_confirmation_template(self, mock_get_solo, mock_AsyncResult):
        mock_AsyncResult.return_value.state = states.SUCCESS
        submission = SubmissionFactory.create(
            completed=True,
            with_report=False,
            form__submission_confirmation_template="""
            <p>This is some <span style="color: red;">inline styled</span> HTML.</p>
            """,
            metadata__tasks_ids=["123"],
        )
        token = submission_status_token_generator.make_token(submission)
        check_status_url = reverse(
            "api:submission-status", kwargs={"uuid": submission.uuid, "token": token}
        )

        response = self.client.get(
            check_status_url, **{NONCE_HTTP_HEADER: self.csp_nonce}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        confirmation_page = response.json()["confirmationPageContent"]

        html_id = f"nonce-{md5hash(self.csp_nonce)}-1234"
        expected = f"""
        <style nonce="{self.csp_nonce}">
            #{html_id} {{
                color: red;
            }}
        </style>
        <p>This is some <span id="{html_id}">inline styled</span> HTML.</p>
        """
        self.assertHTMLEqual(confirmation_page, expected)

    def test_global_config_level_confirmation_template(
        self, mock_get_solo, mock_AsyncResult
    ):
        mock_AsyncResult.return_value.state = states.SUCCESS
        mock_get_solo.return_value = GlobalConfiguration(
            submission_confirmation_template="""
            <p>This is some <span style="color: red;">inline styled</span> HTML.</p>
            """
        )
        submission = SubmissionFactory.create(
            completed=True, with_report=False, metadata__tasks_ids=["123"]
        )
        token = submission_status_token_generator.make_token(submission)
        check_status_url = reverse(
            "api:submission-status", kwargs={"uuid": submission.uuid, "token": token}
        )

        response = self.client.get(
            check_status_url, **{NONCE_HTTP_HEADER: self.csp_nonce}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        confirmation_page = response.json()["confirmationPageContent"]

        html_id = f"nonce-{md5hash(self.csp_nonce)}-1234"
        expected = f"""
        <style nonce="{self.csp_nonce}">
            #{html_id} {{
                color: red;
            }}
        </style>
        <p>This is some <span id="{html_id}">inline styled</span> HTML.</p>
        """
        self.assertHTMLEqual(confirmation_page, expected)
