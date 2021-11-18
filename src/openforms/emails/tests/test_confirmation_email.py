import inspect
import re
from copy import deepcopy
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

from django.core import mail
from django.core.exceptions import ValidationError
from django.template import TemplateSyntaxError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.translation import gettext as _

from openforms.appointments.base import (
    AppointmentDetails,
    AppointmentLocation,
    AppointmentProduct,
    BasePlugin,
)
from openforms.appointments.constants import AppointmentDetailsStatus
from openforms.appointments.tests.factories import AppointmentInfoFactory
from openforms.appointments.tests.test_base import TestPlugin
from openforms.config.models import GlobalConfiguration
from openforms.forms.tests.factories import FormStepFactory
from openforms.payments.constants import PaymentStatus
from openforms.payments.tests.factories import SubmissionPaymentFactory
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionStepFactory,
)
from openforms.submissions.utils import send_confirmation_email
from openforms.tests.utils import NOOP_CACHES
from openforms.utils.tests.html_assert import HTMLAssertMixin
from openforms.utils.urls import build_absolute_uri

from ..confirmation_emails import (
    get_confirmation_email_context_data,
    render_confirmation_email_template,
)
from ..models import ConfirmationEmailTemplate
from ..utils import unwrap_anchors
from .factories import ConfirmationEmailTemplateFactory

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
                    "confirmationRecipient": True,
                },
            ],
        }
    ],
}


class FixedCancelAndChangeLinkPlugin(TestPlugin):
    def get_cancel_link(self, submission) -> str:
        return "http://fake.nl/api/v1/submission-uuid/token/verify/"

    def get_change_link(self, submission) -> str:
        return "http://fake.nl/api/v1/submission-uuid/token/change/"


@override_settings(CACHES=NOOP_CACHES)
class ConfirmationEmailTests(HTMLAssertMixin, TestCase):
    def test_validate_content_syntax(self):
        email = ConfirmationEmailTemplate(subject="foo", content="{{{}}}")

        with self.assertRaisesRegex(ValidationError, "Could not parse the remainder:"):
            email.full_clean()

    def test_validate_content_required_tags(self):
        email = ConfirmationEmailTemplate(subject="foo", content="no tags here")
        with self.assertRaisesRegex(
            ValidationError,
            _("Missing required template-tag {tag}").format(
                tag="{% appointment_information %}"
            ),
        ):
            email.full_clean()

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
            context = get_confirmation_email_context_data(submission)
            render_confirmation_email_template(email.content, context)

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
        context = get_confirmation_email_context_data(submission)
        rendered_content = render_confirmation_email_template(email.content, context)

        self.assertTagWithTextIn("td", "Name", rendered_content)
        self.assertTagWithTextIn("td", "Jane", rendered_content)
        self.assertTagWithTextIn("td", "Last name", rendered_content)
        self.assertTagWithTextIn("td", "Doe", rendered_content)

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
        context = get_confirmation_email_context_data(submission)
        rendered_content = render_confirmation_email_template("{% summary %}", context)

        self.assertTagWithTextIn("td", "Name", rendered_content)
        self.assertTagWithTextIn("td", "Jane", rendered_content)
        self.assertTagWithTextIn("td", "Last name", rendered_content)
        self.assertTagWithTextIn("td", "Doe", rendered_content)
        self.assertTagWithTextIn("td", "File", rendered_content)
        self.assertTagWithTextIn("td", "my-image.jpg", rendered_content)

    @patch(
        "openforms.emails.templatetags.appointments.get_client",
        return_value=FixedCancelAndChangeLinkPlugin(),
    )
    def test_appointment_information(self, get_client_mock):
        config = GlobalConfiguration.get_solo()
        config.email_template_netloc_allowlist = ["fake.nl"]
        config.save()

        submission = SubmissionFactory.create()
        AppointmentInfoFactory.create(
            status=AppointmentDetailsStatus.success,
            appointment_id="123456789",
            submission=submission,
        )
        email = ConfirmationEmailTemplate(content="{% appointment_information %}")
        context = get_confirmation_email_context_data(submission)
        rendered_content = render_confirmation_email_template(email.content, context)

        self.assertIn("Test product 1", rendered_content)
        self.assertIn("Test product 2", rendered_content)
        self.assertIn("Test location", rendered_content)
        self.assertIn("1 januari 2021, 12:00 - 12:15", rendered_content)
        self.assertIn("Remarks", rendered_content)
        self.assertIn("Some", rendered_content)
        self.assertIn("&lt;h1&gt;Data&lt;/h1&gt;", rendered_content)

        self.assertInHTML(
            '<a href="http://fake.nl/api/v1/submission-uuid/token/verify/" rel="nofollow">'
            + _("Cancel appointment")
            + "</a>",
            rendered_content,
        )

        self.assertInHTML(
            '<a href="http://fake.nl/api/v1/submission-uuid/token/change/" rel="nofollow">'
            + _("Change appointment")
            + "</a>",
            rendered_content,
        )

    def test_appointment_information_with_no_appointment_id(self):
        submission = SubmissionFactory.create()
        AppointmentInfoFactory.create(
            status=AppointmentDetailsStatus.missing_info,
            appointment_id="",
            submission=submission,
        )
        email = ConfirmationEmailTemplate(content="{% appointment_information %}")
        empty_email = ConfirmationEmailTemplate(content="")

        context = get_confirmation_email_context_data(submission)
        rendered_content = render_confirmation_email_template(email.content, context)
        empty_rendered_content = render_confirmation_email_template(
            empty_email.content, context
        )

        self.assertEqual(empty_rendered_content, rendered_content)

    def test_checkboxes_ordering(self):
        submission = SubmissionFactory.from_components(
            completed=True,
            components_list=[
                {
                    "key": "selectBoxes",
                    "type": "selectboxes",
                    "values": [
                        {"label": "Value 1", "value": "value1"},
                        {"label": "Value 2", "value": "value2"},
                        {"label": "Value 3", "value": "value3"},
                    ],
                    "showInEmail": True,
                }
            ],
            submitted_data={
                "selectBoxes": {
                    "value2": True,
                    "value1": True,
                },
            },
        )

        context = get_confirmation_email_context_data(submission)
        rendered_content = render_confirmation_email_template("{% summary %}", context)

        self.assertIn("Value 1, Value 2", rendered_content)


@override_settings(
    CACHES=NOOP_CACHES,
)
class PaymentConfirmationEmailTests(TestCase):
    def test_email_payment_not_required(self):
        email = ConfirmationEmailTemplate(content="test {% payment_information %}")
        submission = SubmissionFactory.create()
        self.assertFalse(submission.payment_required)
        self.assertFalse(submission.payment_user_has_paid)

        context = get_confirmation_email_context_data(submission)
        rendered_content = render_confirmation_email_template(email.content, context)

        literals = [
            _("Payment of &euro; %(payment_price)s received."),
            _("Payment of &euro; %(payment_price)s is required."),
        ]
        for literal in literals:
            with self.subTest(literal=literal):
                self.assertNotIn(
                    literal % {"payment_price": submission.form.product.price},
                    rendered_content,
                )

    def test_email_payment_incomplete(self):
        email = ConfirmationEmailTemplate(content="test {% payment_information %}")
        submission = SubmissionFactory.create(
            form__product__price=Decimal("12.34"),
            form__payment_backend="test",
        )
        self.assertTrue(submission.payment_required)
        self.assertFalse(submission.payment_user_has_paid)

        context = get_confirmation_email_context_data(submission)
        rendered_content = render_confirmation_email_template(email.content, context)

        # show amount
        literal = _(
            "Payment of &euro; %(payment_price)s is required. You can pay using the link below."
        ) % {"payment_price": "12,34"}
        self.assertIn(literal, rendered_content)

        # show link
        url = build_absolute_uri(
            reverse("payments:link", kwargs={"uuid": submission.uuid})
        )
        self.assertIn(url, rendered_content)

    def test_email_payment_completed(self):
        email = ConfirmationEmailTemplate(content="test {% payment_information %}")
        submission = SubmissionFactory.create(
            form__product__price=Decimal("12.34"),
            form__payment_backend="test",
        )
        SubmissionPaymentFactory.for_submission(
            submission, status=PaymentStatus.completed
        )

        self.assertTrue(submission.payment_required)
        self.assertTrue(submission.payment_user_has_paid)

        context = get_confirmation_email_context_data(submission)
        rendered_content = render_confirmation_email_template(email.content, context)

        # still show amount
        literal = _("Payment of &euro; %(payment_price)s received.") % {
            "payment_price": "12,34"
        }
        self.assertIn(literal, rendered_content)

        # no payment link
        url = reverse("payments:link", kwargs={"uuid": submission.uuid})
        self.assertNotIn(url, rendered_content)


class TestAppointmentPlugin(BasePlugin):
    def get_appointment_details(self, identifier: str):
        return AppointmentDetails(
            identifier=identifier,
            products=[
                AppointmentProduct(identifier="1", name="Test product 1 & 2"),
                AppointmentProduct(identifier="2", name="Test product 3"),
            ],
            location=AppointmentLocation(
                identifier="1",
                name="Test location",
                city="Teststad",
                postalcode="1234ab",
            ),
            start_at=datetime(2021, 1, 1, 12, 0),
            end_at=datetime(2021, 1, 1, 12, 15),
            remarks="Remarks",
            other={"Some": "<h1>Data</h1>"},
        )


@override_settings(DEFAULT_FROM_EMAIL="foo@sender.com")
class ConfirmationEmailRenderingIntegrationTest(HTMLAssertMixin, TestCase):
    template = """
    <p>Geachte heer/mevrouw,</p>

    <p>Wij hebben uw inzending, met referentienummer {{ public_reference }}, in goede orde ontvangen.</p>

    <p>Kijk voor meer informatie op <a href="http://gemeente.nl">de homepage</a></p>

    {% summary %}

    {% appointment_information %}

    {% payment_information %}

    <p>Met vriendelijke groet,</p>

    <p>Open Formulieren</p>
    """
    maxDiff = None

    @patch(
        "openforms.emails.templatetags.appointments.get_client",
        return_value=TestAppointmentPlugin(),
    )
    def test_send_confirmation_mail_text_kitchensink(self, appointment_client_mock):
        config = GlobalConfiguration.get_solo()
        config.email_template_netloc_allowlist = ["gemeente.nl"]
        config.save()

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

        submission = SubmissionFactory.from_components(
            conf["components"],
            {
                "name": "Foo",
                "lastName": "de Bar & de Baas",
                "email": "foo@bar.baz",
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
            registration_success=True,
            public_registration_reference="xyz123",
            form__product__price=Decimal("12.34"),
            form__payment_backend="test",
            form_url="http://server/form",
        )
        AppointmentInfoFactory.create(
            status=AppointmentDetailsStatus.success,
            appointment_id="123456789",
            submission=submission,
        )
        self.assertTrue(submission.payment_required)
        self.assertFalse(submission.payment_user_has_paid)

        template = inspect.cleandoc(self.template)
        ConfirmationEmailTemplateFactory.create(
            form=submission.form, subject="My Subject", content=template
        )

        send_confirmation_email(submission)

        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]
        self.assertEqual(message.subject, "My Subject")
        self.assertEqual(message.recipients(), ["foo@bar.baz"])
        self.assertEqual(message.from_email, "foo@sender.com")

        ref = submission.public_registration_reference

        url_exp = r"https?://[a-z0-9:/._-]+"
        pay_line = _(
            "Payment of EUR %(payment_price)s is required. You can pay using the link below."
        ) % {"payment_price": "12,34"}

        with self.subTest("text"):
            expected_text = inspect.cleandoc(
                f"""
            Geachte heer/mevrouw,

            Wij hebben uw inzending, met referentienummer {ref}, in goede orde ontvangen.

            Kijk voor meer informatie op de homepage (#URL#)

            {_("Summary")}

            - Name: Foo
            - Last name: de Bar & de Baas
            - File: my-image.jpg

            {_("Appointment information")}

            {_("Products")}:
            - Test product 1 & 2
            - Test product 3

            {_("Location")}:
            Test location
            1234ab Teststad

            {_("Date and time")}:
            1 januari 2021, 12:00 - 12:15

            {_("Remarks")}:
            Remarks

            Some:
            Data

            Als u uw afspraak wilt annuleren kunt u dat hieronder doen.
            {_("Cancel appointment")}: #URL#
            {_("Change appointment")}: #URL#

            {_("Payment information")}

            {pay_line}
            {_("Go to the payment page")}: #URL#

            Met vriendelijke groet,

            Open Formulieren
            """
            ).lstrip()

            # process to keep tests sane (random tokens)
            text = message.body.rstrip()
            text = re.sub(url_exp, "#URL#", text)
            self.assertEquals(expected_text, text)
            self.assertNotIn("<a ", text)
            self.assertNotIn("<td ", text)
            self.assertNotIn("<p ", text)
            self.assertNotIn("<br ", text)

        with self.subTest("html"):
            # html alternative
            self.assertEqual(len(message.alternatives), 1)

            message_html = message.alternatives[0][0]

            self.assertTagWithTextIn("td", "Name", message_html)
            self.assertTagWithTextIn("td", "Foo", message_html)
            self.assertIn('<a href="http://gemeente.nl">', message_html)


class UtilsTest(TestCase):
    def test_unwrap_anchors(self):
        input = '<p>foo <a href="http://example.com/">text</a> bar</p>'
        actual = unwrap_anchors(input)
        # expected = "foo text(http://example.com/) bar"
        expected = '<p>foo <a href="http://example.com/">text (http://example.com/)</a> bar</p>'

        self.assertEqual(expected, actual)
