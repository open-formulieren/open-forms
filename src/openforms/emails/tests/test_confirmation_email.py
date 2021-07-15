from django.core.exceptions import ValidationError
from django.template import TemplateSyntaxError
from django.test import TestCase, override_settings

from openforms.config.models import GlobalConfiguration
from openforms.forms.tests.factories import FormStepFactory
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionStepFactory,
)
from openforms.tests.utils import NOOP_CACHES

from ..models import ConfirmationEmailTemplate

NESTED_COMPONENT_CONF = {
    "display": "form",
    "components": [
        {
            "id": "e4jv16",
            "key": "fieldset",
            "type": "fieldset",
            "label": "",
            "components": [
                {
                    "id": "e66yf7q",
                    "key": "name",
                    "type": "textfield",
                    "label": "Name",
                    "showInEmail": True,
                },
                {
                    "id": "ewr4r44",
                    "key": "lastName",
                    "type": "textfield",
                    "label": "Last name",
                    "showInEmail": True,
                },
                {
                    "id": "emccur",
                    "key": "email",
                    "type": "email",
                    "label": "Email",
                    "showInEmail": False,
                },
            ],
        }
    ],
}


@override_settings(CACHES=NOOP_CACHES)
class ConfirmationEmailTests(TestCase):
    def test_validate_content_can_be_parsed(self):
        email = ConfirmationEmailTemplate(content="{{{}}}")

        with self.assertRaises(ValidationError):
            email.clean()

    def test_strip_non_allowed_urls(self):
        config = GlobalConfiguration.get_solo()
        config.email_template_netloc_allowlist = ["allowed.com"]
        config.save()
        email = ConfirmationEmailTemplate(
            content="test https://google.com https://www.google.com https://allowed.com test"
        )

        rendered = email.render(SubmissionFactory.build())

        self.assertNotIn("google.com", rendered)
        self.assertIn("https://allowed.com", rendered)

    def test_strip_non_allowed_urls_from_context(self):
        form_step = FormStepFactory.create()
        subm_step = SubmissionStepFactory.create(
            data={"url1": "https://allowed.com", "url2": "https://google.com"},
            form_step=form_step,
            submission__form=form_step.form,
        )
        config = GlobalConfiguration.get_solo()
        config.email_template_netloc_allowlist = ["allowed.com"]
        config.save()

        email = ConfirmationEmailTemplate(content="test {{url1}} {{url2}} test")

        rendered = email.render(subm_step.submission)

        self.assertNotIn("google.com", rendered)
        self.assertIn("https://allowed.com", rendered)

    def test_strip_non_allowed_urls_without_config_strips_all_urls(self):
        email = ConfirmationEmailTemplate(
            content="test https://google.com https://www.google.com https://allowed.com test"
        )

        rendered = email.render(SubmissionFactory.build())

        self.assertNotIn("google.com", rendered)
        self.assertNotIn("allowed.com", rendered)

    def test_cant_delete_model_instances(self):
        form_step = FormStepFactory.create()
        subm_step = SubmissionStepFactory.create(
            data={"url1": "https://allowed.com", "url2": "https://google.com"},
            form_step=form_step,
            submission__form=form_step.form,
        )
        submission = subm_step.submission
        email = ConfirmationEmailTemplate(content="{{ _submission.delete }}")

        with self.assertRaises(ValidationError):
            email.full_clean()

        with self.assertRaises(TemplateSyntaxError):
            email.render(submission)

        submission.refresh_from_db()
        self.assertIsNotNone(submission.pk)

    def test_nested_components(self):
        form_step = FormStepFactory.create(
            form_definition__configuration=NESTED_COMPONENT_CONF
        )
        submission_step = SubmissionStepFactory.create(
            data={"name": "Jane", "lastName": "Doe", "email": "test@example.com"},
            form_step=form_step,
            submission__form=form_step.form,
        )
        submission = submission_step.submission
        email = ConfirmationEmailTemplate(content="{% summary %}")
        rendered_content = email.render(submission)

        self.assertIn("<th>Name</th>", rendered_content)
        self.assertIn("<th>Jane</th>", rendered_content)
        self.assertIn("<th>Last name</th>", rendered_content)
        self.assertIn("<th>Doe</th>", rendered_content)
