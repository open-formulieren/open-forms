from copy import deepcopy
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.template import TemplateSyntaxError
from django.test import TestCase, override_settings

from openforms.appointments.constants import AppointmentDetailsStatus
from openforms.appointments.tests.factories import AppointmentInfoFactory
from openforms.appointments.tests.test_base import TestPlugin
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

    def test_attachment(self):
        conf = deepcopy(NESTED_COMPONENT_CONF)
        conf["components"].append(
            {
                "id": "erttrr",
                "key": "file",
                "type": "file",
                "label": "File",
                "showInEmail": True,
            }
        )
        form_step = FormStepFactory.create(form_definition__configuration=conf)
        submission_step = SubmissionStepFactory.create(
            data={
                "name": "Jane",
                "lastName": "Doe",
                "email": "test@example.com",
                "file": [
                    {
                        "url": "http://server/api/v1/submissions/files/62f2ec22-da7d-4385-b719-b8637c1cd483",
                        "data": {
                            "url": "http://server/api/v1/submissions/files/62f2ec22-da7d-4385-b719-b8637c1cd483",
                            "form": "",
                            "name": "my-image.jpg",
                            "size": 46114,
                            "baseUrl": "http://server/form",
                            "project": "",
                        },
                        "name": "my-image-12305610-2da4-4694-a341-ccb919c3d543.jpg",
                        "size": 46114,
                        "type": "image/jpg",
                        "storage": "url",
                        "originalName": "my-image.jpg",
                    }
                ],
            },
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
        self.assertIn("<th>File</th>", rendered_content)
        self.assertIn("<th>my-image.jpg</th>", rendered_content)

    @patch(
        "openforms.emails.templatetags.appointments.get_client",
        return_value=TestPlugin(),
    )
    def test_appointment_information(self, get_client_mock):
        submission = SubmissionFactory.create()
        AppointmentInfoFactory.create(
            status=AppointmentDetailsStatus.success,
            appointment_id="123456789",
            submission=submission,
        )
        email = ConfirmationEmailTemplate(content="{% appointment_information %}")
        rendered_content = email.render(submission)

        self.assertIn("Test product 1", rendered_content)
        self.assertIn("Test product 2", rendered_content)
        self.assertIn("Test location", rendered_content)
        self.assertIn("1 januari 2021, 12:00 - 12:15", rendered_content)
        self.assertIn("Remarks", rendered_content)
        self.assertIn("Some", rendered_content)
        self.assertIn("<h1>Data</h1>", rendered_content)

    @patch("openforms.emails.templatetags.appointments.get_client")
    def test_get_appointment_links(self, get_client_mock):
        config = GlobalConfiguration.get_solo()
        config.email_template_netloc_allowlist = ["fake.nl"]
        config.save()

        get_client_mock.return_value.get_appointment_links.return_value = {
            "cancel_url": "http://fake.nl/api/v1/base64-submission-uuid/token/verify/"
        }
        submission = SubmissionFactory.create()
        AppointmentInfoFactory.create(
            status=AppointmentDetailsStatus.success,
            appointment_id="123456789",
            submission=submission,
        )
        email = ConfirmationEmailTemplate(
            content="""
        {% get_appointment_links as links %}
        {{ links.cancel_url|urlize }}
        """
        )
        rendered_content = email.render(submission)

        self.assertInHTML(
            '<a href="http://fake.nl/api/v1/base64-submission-uuid/token/verify/" rel="nofollow">'
            "http://fake.nl/api/v1/base64-submission-uuid/token/verify/"
            "</a>",
            rendered_content,
        )
