import inspect
from copy import deepcopy
from decimal import Decimal
from unittest.mock import patch

from django.core import mail
from django.core.exceptions import ValidationError
from django.template import TemplateSyntaxError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.translation import gettext as _

from openforms.appointments.constants import AppointmentDetailsStatus
from openforms.appointments.contrib.demo.plugin import DemoAppointment
from openforms.appointments.tests.factories import (
    AppointmentFactory,
    AppointmentInfoFactory,
)
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
    get_confirmation_email_templates,
)
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
    @staticmethod
    def get_cancel_link(submission) -> str:
        return "http://fake.nl/api/v2/submission-uuid/token/verify/"


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

    def test_validate_content_netloc_sanitation_validation(self):
        config = GlobalConfiguration.get_solo()
        config.email_template_netloc_allowlist = ["good.net"]  # pyright: ignore[reportAttributeAccessIssue]
        config.save()

        with self.subTest("valid"):
            email = ConfirmationEmailTemplate(
                subject="foo",
                content="bla bla http://good.net/bla?x=1 {% appointment_information %} {% payment_information %} {% cosign_information %}",
            )

            email.full_clean()

        with self.subTest("invalid"):
            email = ConfirmationEmailTemplate(
                subject="foo",
                content="bla bla http://bad.net/bla?x=1 {% appointment_information %} {% payment_information %} {% cosign_information %}",
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
        email = ConfirmationEmailTemplate(content="{% confirmation_summary %}")
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
        rendered_content = render_email_template("{% confirmation_summary %}", context)

        self.assertTagWithTextIn("td", "Name", rendered_content)
        self.assertTagWithTextIn("td", "Jane", rendered_content)
        self.assertTagWithTextIn("td", "Last name", rendered_content)
        self.assertTagWithTextIn("td", "Doe", rendered_content)
        self.assertTagWithTextIn("td", "File", rendered_content)
        self.assertTagWithTextIn("td", "my-image.jpg", rendered_content)

    @patch(
        "openforms.emails.templatetags.appointments.get_plugin",
        return_value=FixedCancelAndChangeLinkPlugin("email"),  # pyright: ignore[reportAbstractUsage]
    )
    def test_appointment_information(self, get_plugin_mock):
        config = GlobalConfiguration.get_solo()
        config.email_template_netloc_allowlist = ["fake.nl"]  # pyright: ignore[reportAttributeAccessIssue]
        config.save()

        appointment = AppointmentFactory.create(appointment_info__registration_ok=True)
        email = ConfirmationEmailTemplate(content="{% appointment_information %}")
        context = get_confirmation_email_context_data(appointment.submission)
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
        rendered_content = render_email_template("{% confirmation_summary %}", context)

        self.assertInHTML("<ul><li>Value 1</li><li>Value 2</li></ul>", rendered_content)

    def test_get_confirmation_email_templates(self):
        email_template1 = ConfirmationEmailTemplateFactory.create(
            form__send_confirmation_email=True,
            subject="Custom subject",
            content="Custom content {% appointment_information %} {% payment_information %} {% cosign_information %}",
        )
        email_template2 = ConfirmationEmailTemplateFactory.create(
            form__send_confirmation_email=True,
            subject="",
            content="Custom content {% appointment_information %} {% payment_information %} {% cosign_information %}",
        )
        email_template3 = ConfirmationEmailTemplateFactory.create(
            form__send_confirmation_email=True, subject="Custom subject", content=""
        )
        email_template4 = ConfirmationEmailTemplateFactory.create(
            form__send_confirmation_email=True, subject="", content=""
        )

        submission1 = SubmissionFactory.create(form=email_template1.form)
        submission2 = SubmissionFactory.create(form=email_template2.form)
        submission3 = SubmissionFactory.create(form=email_template3.form)
        submission4 = SubmissionFactory.create(form=email_template4.form)

        with patch(
            "openforms.emails.confirmation_emails.GlobalConfiguration.get_solo",
            return_value=GlobalConfiguration(
                confirmation_email_subject="Global subject",
                confirmation_email_content="Global content {% appointment_information %} {% payment_information %} {% cosign_information %}",
            ),
        ):
            with self.subTest("Custom subject + custom content"):
                subject, content = get_confirmation_email_templates(submission1)

                self.assertEqual(subject, "Custom subject")
                self.assertIn("Custom content", content)

            with self.subTest("Global subject + custom content"):
                subject, content = get_confirmation_email_templates(submission2)

                self.assertEqual(subject, "Global subject")
                self.assertIn("Custom content", content)

            with self.subTest("Custom subject + global content"):
                subject, content = get_confirmation_email_templates(submission3)

                self.assertEqual(subject, "Custom subject")
                self.assertIn("Global content", content)

            with self.subTest("Global subject + global content"):
                subject, content = get_confirmation_email_templates(submission4)

                self.assertEqual(subject, "Global subject")
                self.assertIn("Global content", content)

    def test_get_confirmation_email_templates_form_with_cosign(self):
        (
            submission1,
            submission2,
            submission3,
            submission4,
            submission5,  # no overrides
        ) = [
            SubmissionFactory.from_components(
                components_list=[{"type": "cosign", "key": "cosign"}],
                submitted_data={"cosign": "test@example.com"},
                form__send_confirmation_email=True,
                completed=True,
            )
            for _ in range(5)
        ]
        ConfirmationEmailTemplateFactory.create(
            form=submission1.form,
            cosign_subject="Custom subject",
            cosign_content="Custom content {% payment_information %} {% cosign_information %}",
        )
        ConfirmationEmailTemplateFactory.create(
            form=submission2.form,
            cosign_subject="",
            cosign_content="Custom content {% payment_information %} {% cosign_information %}",
        )
        ConfirmationEmailTemplateFactory.create(
            form=submission3.form,
            cosign_subject="Custom subject",
            cosign_content="",
        )
        ConfirmationEmailTemplateFactory.create(
            form=submission4.form,
            cosign_subject="",
            cosign_content="",
        )

        with patch(
            "openforms.emails.confirmation_emails.GlobalConfiguration.get_solo",
            return_value=GlobalConfiguration(
                cosign_confirmation_email_subject="Global subject",
                cosign_confirmation_email_content="Global content {% payment_information %} {% cosign_information %}",
            ),
        ):
            with self.subTest("Custom subject + custom content"):
                subject, content = get_confirmation_email_templates(submission1)

                self.assertEqual(subject, "Custom subject")
                self.assertIn("Custom content", content)

            with self.subTest("Global subject + custom content"):
                subject, content = get_confirmation_email_templates(submission2)

                self.assertEqual(subject, "Global subject")
                self.assertIn("Custom content", content)

            with self.subTest("Custom subject + global content"):
                subject, content = get_confirmation_email_templates(submission3)

                self.assertEqual(subject, "Custom subject")
                self.assertIn("Global content", content)

            with self.subTest("Global subject + global content"):
                subject, content = get_confirmation_email_templates(submission4)

                self.assertEqual(subject, "Global subject")
                self.assertIn("Global content", content)

            with self.subTest("no form specific templates"):
                subject, content = get_confirmation_email_templates(submission5)

                self.assertEqual(subject, "Global subject")
                self.assertIn("Global content", content)

    def test_summary_heading_behaviour(self):
        expected_heading = _("Summary")

        with self.subTest("heading present"):
            submission = SubmissionFactory.from_components(
                [
                    {
                        "type": "textfield",
                        "key": "text",
                        "label": "Visible",
                        "showInEmail": True,
                    }
                ],
                submitted_data={"text": "Snowflake text"},
                form__send_confirmation_email=True,
            )
            ConfirmationEmailTemplateFactory.create(
                form=submission.form,
                subject="Subject",
                content="{% confirmation_summary %}{% appointment_information %}",
            )
            template = get_confirmation_email_templates(submission)[1]
            context = get_confirmation_email_context_data(submission)

            result = render_email_template(template, context)

            self.assertIn("Snowflake text", result)
            self.assertIn(expected_heading, result)

        with self.subTest("heading absent"):
            submission = SubmissionFactory.from_components(
                [
                    {
                        "type": "textfield",
                        "key": "text",
                        "label": "Visible",
                        "showInEmail": False,
                    }
                ],
                submitted_data={"text": "Snowflake text"},
                form__send_confirmation_email=True,
            )
            ConfirmationEmailTemplateFactory.create(
                form=submission.form,
                subject="Subject",
                content="{% confirmation_summary %}{% appointment_information %}",
            )
            template = get_confirmation_email_templates(submission)[1]
            context = get_confirmation_email_context_data(submission)

            result = render_email_template(template, context)

            self.assertNotIn("Snowflake text", result)
            self.assertNotIn(expected_heading, result)

    def test_auth_static_variables_excluded_from_confirmation_email_context(self):
        submission = SubmissionFactory.create()
        context = get_confirmation_email_context_data(submission)

        excluded_variables = [
            "auth",
            "auth_bsn",
            "auth_kvk",
            "auth_pseudo",
            "auth_additional_claims",
            "auth_context_loa",
            "auth_context_representee_identifier_type",
            "auth_context_representee_identifier",
            "auth_context_legal_subject_identifier_type",
            "auth_context_legal_subject_identifier",
            "auth_context_branch_number",
            "auth_context_acting_subject_identifier_type",
            "auth_context_acting_subject_identifier",
        ]
        included_variables = [
            "submission_id",
            "language_code",
            "auth_type",
            "auth_context_source",
        ]
        for variable in excluded_variables:
            with self.subTest(variable):
                self.assertNotIn(variable, context)

        for variable in included_variables:
            with self.subTest(variable):
                self.assertIn(variable, context)


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
            with_public_registration_reference=True,
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


@override_settings(DEFAULT_FROM_EMAIL="foo@sender.com")
class ConfirmationEmailRenderingIntegrationTest(HTMLAssertMixin, TestCase):
    template = """
    <p>Geachte heer/mevrouw,</p>

    <p>Wij hebben uw inzending, met referentienummer {{ public_reference }}, in goede orde ontvangen.</p>

    <p>Kijk voor meer informatie op <a href="http://gemeente.nl">de homepage</a></p>

    {% confirmation_summary %}

    {% appointment_information %}

    {% product_information %}

    {% payment_information %}

    <p>Met vriendelijke groet,</p>

    <p>Open Formulieren</p>
    """
    maxDiff = None

    def test_templatetag_alias(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "test",
                    "type": "textfield",
                    "label": "Test",
                    "showInEmail": True,
                },
                {
                    "key": "email",
                    "type": "email",
                    "label": "Email",
                    "showInEmail": False,
                    "confirmationRecipient": True,
                },
            ],
            {"test": "This is a test", "email": "test@test.nl"},
            registration_success=True,
        )
        ConfirmationEmailTemplateFactory.create(
            form=submission.form,
            subject="My Subject",
            content="{% confirmation_summary %}",
        )
        first_step_name = submission.submissionstep_set.all()[  # pyright: ignore[reportAttributeAccessIssue]
            0
        ].form_step.form_definition.name

        send_confirmation_email(submission)

        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]
        # process to keep tests sane (random tokens)
        text = message.body.rstrip()
        expected_text = inspect.cleandoc(
            f"""
            {_("Summary")}

            {first_step_name}

            - Test: This is a test
            """
        ).lstrip()

        self.assertEqual(expected_text, text)

    def test_confirmation_email_cosign_required(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign",
                    "validate": {"required": True},
                },
                {
                    "key": "mainPersonEmail",
                    "type": "email",
                    "confirmationRecipient": True,
                },
            ],
            {"cosign": "cosigner@test.nl", "mainPersonEmail": "main@test.nl"},
            registration_success=True,
            completed=True,
            cosign_complete=False,
        )
        ConfirmationEmailTemplateFactory.create(
            form=submission.form,
            cosign_subject="Confirmation",
            cosign_content="{% cosign_information %}",
        )

        send_confirmation_email(submission)

        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]
        text = message.body.rstrip()
        expected_text = _(
            "This form will not be processed until it has been co-signed. A co-sign "
            "request was sent to %(cosigner_email)s."
        ) % {"cosigner_email": "cosigner@test.nl"}
        self.assertEqual(expected_text, text)

    def test_confirmation_email_cosign_not_required_but_filled_in(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign",
                    "validate": {"required": False},
                },
                {
                    "key": "mainPersonEmail",
                    "type": "email",
                    "confirmationRecipient": True,
                },
            ],
            {"cosign": "cosigner@test.nl", "mainPersonEmail": "main@test.nl"},
            registration_success=True,
            completed=True,
            cosign_complete=False,
        )
        ConfirmationEmailTemplateFactory.create(
            form=submission.form,
            cosign_subject="Confirmation",
            cosign_content="{% cosign_information %}",
        )

        send_confirmation_email(submission)

        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]
        text = message.body.rstrip()
        expected_text = _(
            "This form will not be processed until it has been co-signed. A co-sign "
            "request was sent to %(cosigner_email)s."
        ) % {"cosigner_email": "cosigner@test.nl"}
        self.assertEqual(expected_text, text)

    def test_confirmation_email_cosign_complete(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign",
                    "validate": {"required": False},
                },
                {
                    "key": "mainPersonEmail",
                    "type": "email",
                    "confirmationRecipient": True,
                },
            ],
            {"cosign": "cosigner@test.nl", "mainPersonEmail": "main@test.nl"},
            registration_success=True,
            completed=True,
            cosign_complete=True,
        )
        ConfirmationEmailTemplateFactory.create(
            form=submission.form,
            cosign_subject="Confirmation",
            cosign_content="{% cosign_information %}",
        )

        send_confirmation_email(submission)

        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]
        text = message.body.rstrip()
        expected_text = _(
            "This email is a confirmation that this form has been co-signed by "
            "%(cosigner_email)s and can now be processed."
        ) % {"cosigner_email": "cosigner@test.nl"}
        self.assertEqual(expected_text, text)

    def test_confirmation_email_cosign_not_required_and_not_filled_in(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign",
                    "validate": {"required": False},
                },
                {
                    "key": "mainPersonEmail",
                    "type": "email",
                    "confirmationRecipient": True,
                },
            ],
            {"cosign": "", "mainPersonEmail": "main@test.nl"},
            registration_success=True,
            completed=True,
            cosign_complete=False,
        )
        template = (
            "Test: {% if waiting_on_cosign %}This form will not be processed until it "
            "has been co-signed. A co-sign request was sent to {{ cosigner_email }}."
            "{% endif %}"
        )
        ConfirmationEmailTemplateFactory.create(
            form=submission.form,
            subject="Confirmation",
            content=template,
        )

        send_confirmation_email(submission)

        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]
        text = message.body.rstrip()
        self.assertEqual(text, "Test:")

    def test_confirmation_email_cosign_completed(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign",
                    "validate": {"required": True},
                },
                {
                    "key": "mainPersonEmail",
                    "type": "email",
                    "confirmationRecipient": True,
                },
            ],
            {"cosign": "cosign@test.nl", "mainPersonEmail": "main@test.nl"},
            registration_success=True,
            completed=True,
            cosign_complete=True,
        )
        template = inspect.cleandoc(
            "Test: {% if waiting_on_cosign %}This form will not be processed until it has been co-signed. A co-sign request was sent to {{ cosigner_email }}.{% endif %}"
        )
        ConfirmationEmailTemplateFactory.create(
            form=submission.form,
            cosign_subject="Confirmation",
            cosign_content=template,
        )

        send_confirmation_email(submission)

        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]
        text = message.body.rstrip()
        expected_text = inspect.cleandoc("Test:").lstrip()

        self.assertEqual(expected_text, text)
