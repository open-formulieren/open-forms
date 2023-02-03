import inspect
import re
from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal
from unittest import skipIf
from unittest.mock import patch

from django.core import mail
from django.core.exceptions import ValidationError
from django.template import TemplateSyntaxError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext as _

from openforms.appointments.base import (
    AppointmentDetails,
    AppointmentLocation,
    AppointmentProduct,
    BasePlugin,
)
from openforms.appointments.constants import AppointmentDetailsStatus
from openforms.appointments.contrib.demo.plugin import DemoAppointment
from openforms.appointments.tests.factories import AppointmentInfoFactory
from openforms.config.models import GlobalConfiguration
from openforms.forms.tests.factories import FormStepFactory
from openforms.payments.constants import PaymentStatus
from openforms.payments.tests.factories import SubmissionPaymentFactory
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionStepFactory,
)
from openforms.submissions.utils import send_confirmation_email
from openforms.tests.utils import NOOP_CACHES, can_connect
from openforms.utils.tests.html_assert import HTMLAssertMixin, strip_all_attributes
from openforms.utils.urls import build_absolute_uri

from ..confirmation_emails import get_confirmation_email_context_data
from ..models import ConfirmationEmailTemplate
from ..utils import render_email_template
from .factories import ConfirmationEmailTemplateFactory

NESTED_COMPONENT_CONF = {
    "display": "form",
    "components": [
        {
            "id": "e4jv16",
            "key": "fieldset",
            "type": "fieldset",
            "label": "A fieldset",
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
                {
                    "key": "hiddenInput",
                    "type": "textfield",
                    "label": "Hidden input",
                    "hidden": True,
                    "showInEmail": True,
                },
            ],
        },
        {
            "key": "fieldset2",
            "type": "fieldset",
            "label": "A fieldset with hidden children",
            "components": [
                {
                    "key": "hiddenInput2",
                    "type": "textfield",
                    "label": "Hidden input 2",
                    "hidden": True,
                    "showInEmail": True,
                },
            ],
        },
    ],
}


class FixedCancelAndChangeLinkPlugin(DemoAppointment):
    def get_cancel_link(self, submission) -> str:
        return "http://fake.nl/api/v2/submission-uuid/token/verify/"

    def get_change_link(self, submission) -> str:
        return "http://fake.nl/api/v2/submission-uuid/token/change/"


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

    @skipIf(
        not can_connect("https://publicsuffix.org/list/public_suffix_list.dat"),
        "URL sanitation test require the download of the Public Suffix list",
    )
    def test_validate_content_netloc_sanitation_validation(self):
        config = GlobalConfiguration.get_solo()
        config.email_template_netloc_allowlist = ["good.net"]
        config.save()

        with self.subTest("valid"):
            email = ConfirmationEmailTemplate(
                subject="foo",
                content="bla bla http://good.net/bla?x=1 {% appointment_information %} {% payment_information %}",
            )

            email.full_clean()

        with self.subTest("invalid"):
            email = ConfirmationEmailTemplate(
                subject="foo",
                content="bla bla http://bad.net/bla?x=1 {% appointment_information %} {% payment_information %}",
            )
            with self.assertRaisesMessage(
                ValidationError,
                _("This domain is not in the global netloc allowlist: {netloc}").format(
                    netloc="bad.net"
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
            render_email_template(email.content, context)

        submission.refresh_from_db()
        self.assertIsNotNone(submission.pk)

    def test_nested_components(self):
        submission = SubmissionFactory.from_components(
            components_list=NESTED_COMPONENT_CONF["components"],
            submitted_data={
                "name": "Jane",
                "lastName": "Doe",
                "email": "test@example.com",
            },
        )
        email = ConfirmationEmailTemplate(content="{% summary %}")
        context = get_confirmation_email_context_data(submission)
        rendered_content = render_email_template(email.content, context)

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
        submission = SubmissionFactory.from_components(
            components_list=conf["components"],
            submitted_data={
                "name": "Jane",
                "lastName": "Doe",
                "email": "test@example.com",
                "file": [
                    {
                        "url": "http://server/api/v2/submissions/files/62f2ec22-da7d-4385-b719-b8637c1cd483",
                        "data": {
                            "url": "http://server/api/v2/submissions/files/62f2ec22-da7d-4385-b719-b8637c1cd483",
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
        )
        context = get_confirmation_email_context_data(submission)
        rendered_content = render_email_template("{% summary %}", context)

        self.assertTagWithTextIn("td", "Name", rendered_content)
        self.assertTagWithTextIn("td", "Jane", rendered_content)
        self.assertTagWithTextIn("td", "Last name", rendered_content)
        self.assertTagWithTextIn("td", "Doe", rendered_content)
        self.assertTagWithTextIn("td", "File", rendered_content)
        self.assertTagWithTextIn(
            "td", _("attachment: %s") % "my-image.jpg", rendered_content
        )

    @patch(
        "openforms.emails.templatetags.appointments.get_plugin",
        return_value=FixedCancelAndChangeLinkPlugin("email"),
    )
    def test_appointment_information(self, get_plugin_mock):
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
        rendered_content = render_email_template(email.content, context)

        self.assertIn("Test product 1", rendered_content)
        self.assertIn("Test product 2", rendered_content)
        self.assertIn("Test location", rendered_content)
        self.assertIn("1 januari 2021, 12:00 - 12:15", rendered_content)
        self.assertIn("Remarks", rendered_content)
        self.assertIn("Some", rendered_content)
        self.assertIn("&lt;h1&gt;Data&lt;/h1&gt;", rendered_content)

        self.assertInHTML(
            '<a href="http://fake.nl/api/v2/submission-uuid/token/verify/" rel="nofollow">'
            + _("Cancel appointment")
            + "</a>",
            rendered_content,
        )

        self.assertInHTML(
            '<a href="http://fake.nl/api/v2/submission-uuid/token/change/" rel="nofollow">'
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
        rendered_content = render_email_template(email.content, context)
        empty_rendered_content = render_email_template(empty_email.content, context)

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
        rendered_content = render_email_template("{% summary %}", context)

        self.assertIn("Value 1; Value 2", rendered_content)


@override_settings(
    CACHES=NOOP_CACHES,
)
class PaymentConfirmationEmailTests(TestCase):
    def test_email_payment_not_required(self):
        email = ConfirmationEmailTemplate(content="test {% payment_information %}")
        submission = SubmissionFactory.create(completed=True, price=Decimal("10.00"))
        self.assertFalse(submission.payment_required)
        self.assertFalse(submission.payment_user_has_paid)

        context = get_confirmation_email_context_data(submission)
        rendered_content = render_email_template(email.content, context)

        literals = [
            _("Payment of &euro; %(payment_price)s received."),
            _("Payment of &euro; %(payment_price)s is required."),
        ]
        for literal in literals:
            with self.subTest(literal=literal):
                self.assertNotIn(
                    literal % {"payment_price": Decimal("10.00")},
                    rendered_content,
                )

    def test_email_payment_incomplete(self):
        email = ConfirmationEmailTemplate(content="test {% payment_information %}")
        submission = SubmissionFactory.create(
            completed=True,
            form__product__price=Decimal("12.34"),
            form__payment_backend="test",
        )
        self.assertTrue(submission.payment_required)
        self.assertFalse(submission.payment_user_has_paid)

        context = get_confirmation_email_context_data(submission)
        rendered_content = render_email_template(email.content, context)

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
            completed=True,
            form__product__price=Decimal("12.34"),
            form__payment_backend="test",
        )
        SubmissionPaymentFactory.for_submission(
            submission, status=PaymentStatus.completed
        )

        self.assertTrue(submission.payment_required)
        self.assertTrue(submission.payment_user_has_paid)

        context = get_confirmation_email_context_data(submission)
        rendered_content = render_email_template(email.content, context)

        # still show amount
        literal = _("Payment of &euro; %(payment_price)s received.") % {
            "payment_price": "12,34"
        }
        self.assertIn(literal, rendered_content)

        # no payment link
        url = reverse("payments:link", kwargs={"uuid": submission.uuid})
        self.assertNotIn(url, rendered_content)


class TestAppointmentPlugin(BasePlugin):
    def get_available_products(self, current_products=None):
        return [
            AppointmentProduct(identifier="1", name="Test product 1"),
            AppointmentProduct(identifier="2", name="Test product 2"),
        ]

    def get_locations(self, products):
        return [AppointmentLocation(identifier="1", name="Test location")]

    def get_dates(self, products, location, start_at=None, end_at=None):
        return [date(2021, 1, 1)]

    def get_times(self, products, location, day):
        return [datetime(2021, 1, 1, 12, 0)]

    def create_appointment(self, products, location, start_at, client, remarks=None):
        return "1"

    def delete_appointment(self, identifier: str) -> None:
        return

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

    {% product_information %}

    {% payment_information %}

    <p>Met vriendelijke groet,</p>

    <p>Open Formulieren</p>
    """
    maxDiff = None

    @patch(
        "openforms.emails.templatetags.appointments.get_plugin",
        return_value=TestAppointmentPlugin("test"),
    )
    def test_send_confirmation_mail_text_kitchensink(self, appointment_plugin_mock):
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
                        "url": "http://server/api/v2/submissions/files/62f2ec22-da7d-4385-b719-b8637c1cd483",
                        "data": {
                            "url": "http://server/api/v2/submissions/files/62f2ec22-da7d-4385-b719-b8637c1cd483",
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
            form__product__information="<p>info line 1</p>\r\n<p>info line 2</p>\r\n<p>info line 3</p>",
            form__payment_backend="test",
            form_url="http://server/form",
            co_sign_data={
                "plugin": "digid",
                "identifier": "123456782",
                "fields": {
                    "voornaam": "Tina",
                    "geslachtsnaam": "Shikari",
                },
                "representation": "T. Shikari",
            },
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
        first_step_name = submission.submissionstep_set.all()[
            0
        ].form_step.form_definition.name

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

            {first_step_name}

            - A fieldset
             - Name: Foo
             - Last name: de Bar & de Baas
            - File: {_("attachment: %s") % "my-image.jpg"}
            - {_("Co-signed by")}: T. Shikari

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

            {_("If you want to cancel or change your appointment, you can do so below.")}
            {_("Cancel appointment")}: #URL#
            {_("Change appointment")}: #URL#

            info line 1
            info line 2
            info line 3

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

            message_html_only_tags = strip_all_attributes(message_html)
            # check co-sign data presence
            self.assertInHTML(
                format_html(
                    "<tr> <td>{label}</td> <td>T. Shikari</td> </tr>",
                    label=_("Co-signed by"),
                ),
                message_html_only_tags,
            )

            # fieldset and step containers should be visible
            self.assertInHTML(
                format_html("<h3>{}</h3>", first_step_name),
                message_html_only_tags,
            )

            # renderer should ignore hidden inputs
            self.assertNotIn("Hidden input", message_html_only_tags)
            self.assertNotIn("A fieldset with hidden children", message_html_only_tags)
            self.assertNotIn("Hidden input 2", message_html_only_tags)

        with self.subTest("attachments"):
            # file uploads may not be added as attachments, see #1193
            self.assertEqual(message.attachments, [])

    @patch(
        "openforms.emails.templatetags.appointments.get_plugin",
        return_value=TestAppointmentPlugin("test"),
    )
    def test_html_in_subject(self, appointment_plugin_mock):
        """Assert that HTML is not escaped in Email subjects"""

        conf = deepcopy(NESTED_COMPONENT_CONF)

        submission = SubmissionFactory.from_components(
            conf["components"],
            {
                "name": "John",
                "lastName": "Doe",
                "email": "foo@bar.baz",
            },
            registration_success=True,
        )
        submission.form.name = "Foo's bar"

        template = inspect.cleandoc(self.template)

        ConfirmationEmailTemplateFactory.create(
            form=submission.form, subject="Subject: {{ form_name }}", content=template
        )

        send_confirmation_email(submission)

        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]
        self.assertEqual(message.subject, "Subject: Foo's bar")
