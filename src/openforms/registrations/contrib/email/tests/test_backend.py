from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

from django.core import mail
from django.test import TestCase, override_settings, tag
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _

import tablib
from furl import furl

from openforms.config.models import GlobalConfiguration
from openforms.emails.constants import (
    X_OF_CONTENT_TYPE_HEADER,
    X_OF_CONTENT_UUID_HEADER,
    X_OF_EVENT_HEADER,
    EmailContentTypeChoices,
    EmailEventChoices,
)
from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
)
from openforms.payments.constants import PaymentStatus
from openforms.payments.tests.factories import SubmissionPaymentFactory
from openforms.submissions.attachments import attach_uploads_to_submission_step
from openforms.submissions.exports import create_submission_export
from openforms.submissions.models import Submission
from openforms.submissions.public_references import set_submission_reference
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
    SubmissionReportFactory,
    SubmissionStepFactory,
    SubmissionValueVariableFactory,
    TemporaryFileUploadFactory,
)
from openforms.utils.tests.html_assert import HTMLAssertMixin
from openforms.variables.constants import FormVariableSources

from ....service import NoSubmissionReference, extract_submission_reference
from ..constants import AttachmentFormat
from ..models import EmailConfig
from ..plugin import EmailOptions, EmailRegistration

TEST_TEMPLATE_NL = """
{% if payment_received %}

Betaling ontvangen voor {{ form_name }} (ingezonden op {{ completed_on }})
Betalings-order ID: {{ payment_order_id }}

{% else %}

Inzendingdetails van {{ form_name }} (verzonden op {{ completed_on }})

{% endif %}

Onze referentie: {{ public_reference }}

Inzendingstaal: {{ submission_language }}

{% registration_summary %}

{% if co_signer %}
Mede-ondertekend door: {{ co_signer }}
{% endif %}
"""


@override_settings(
    DEFAULT_FROM_EMAIL="info@open-forms.nl",
    BASE_URL="https://example.com",
    LANGUAGE_CODE="nl",
)
class EmailBackendTests(HTMLAssertMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        fd = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "key": "someField",
                        "label": "Some Field",
                        "type": "textfield",
                    },
                    {
                        "key": "someList",
                        "label": "Some list",
                        "type": "textfield",
                        "multiple": True,
                    },
                ],
            }
        )
        form = FormFactory.create(
            name="MyName",
            internal_name="MyInternalName",
            registration_backend="email",
        )
        cls.fs = FormStepFactory.create(form=form, form_definition=fd)
        cls.form = form
        cls.fd = fd

    def test_submission_with_email_backend(self):
        submission = SubmissionFactory.from_components(
            completed=True,
            completed_on=timezone.make_aware(datetime(2021, 1, 1, 12, 0, 0)),
            components_list=[
                {"key": "foo", "type": "textfield", "label": "foo"},
                {
                    "key": "some_list",
                    "type": "textfield",
                    "multiple": True,
                    "label": "some_list",
                },
                {"key": "file1", "type": "file", "label": "file1"},
                {"key": "file2", "type": "file", "label": "file2"},
            ],
            submitted_data={
                "foo": "bar",
                "some_list": ["value1", "value2"],
                "file1": [
                    {  # truncated for brevity
                        "url": "some://url",
                        "name": "my-foo.bin",
                        "type": "application/foo",
                        "originalName": "my-foo.bin",
                    }
                ],
                "file2": [
                    {  # truncated for brevity
                        "url": "some://url",
                        "name": "my-bar.txt",
                        "type": "text/bar",
                        "originalName": "my-bar.txt",
                    }
                ],
            },
            form__name="MyName",
            form__internal_name="MyInternalName",
            form__registration_backend="email",
            co_sign_data={
                "plugin": "demo",
                "representation": "Demo Person",
                "identifier": "111222333",
                "fields": {},
            },
            language_code="nl",
        )
        submission_file_attachment_1 = SubmissionFileAttachmentFactory.create(
            form_key="file1",
            submission_step=submission.submissionstep_set.get(),
            file_name="my-foo.bin",
            content_type="application/foo",
            _component_configuration_path="components.2",
            _component_data_path="file1",
        )
        submission_file_attachment_2 = SubmissionFileAttachmentFactory.create(
            form_key="file2",
            submission_step=submission.submissionstep_set.get(),
            file_name="my-bar.txt",
            content_type="text/bar",
            _component_configuration_path="components.3",
            _component_data_path="file2",
        )
        email_form_options = dict(
            to_emails=["foo@bar.nl", "bar@foo.nl"],
        )
        email_submission = EmailRegistration("email")

        set_submission_reference(submission)

        with patch(
            "openforms.registrations.contrib.email.utils.EmailConfig.get_solo",
            return_value=EmailConfig(
                subject="Subject: {{ form_name }} - submission {{ public_reference }}",
                content_html=TEST_TEMPLATE_NL,
                content_text=TEST_TEMPLATE_NL,
            ),
        ):
            email_submission.register_submission(submission, email_form_options)

        # Verify that email was sent
        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]
        self.assertEqual(
            message.subject,
            f"Subject: MyName - submission {submission.public_registration_reference}",
        )
        self.assertEqual(message.from_email, "info@open-forms.nl")
        self.assertEqual(message.to, ["foo@bar.nl", "bar@foo.nl"])

        # Check that the template is used
        message_text = message.body
        message_html = message.alternatives[0][0]
        self.assertHTMLValid(message_html)
        self.assertIn("<table", message_html)
        self.assertNotIn("<table", message_text)

        detail_line = (
            f"Inzendingdetails van {self.form.name} (verzonden op 12:00:00 01-01-2021)"
        )
        self.assertIn(detail_line, message_html)
        self.assertIn(detail_line, message_text)

        self.assertIn("foo: bar", message_text)
        self.assertIn("some_list: value1; value2", message_text)

        self.assertTagWithTextIn("td", "foo", message_html)
        self.assertTagWithTextIn("td", "bar", message_html)
        self.assertTagWithTextIn("td", "some_list", message_html)
        self.assertTagWithTextIn("td", "value1; value2", message_html)

        cosigner_line = f"{_('Co-signed by')}: Demo Person"

        self.assertIn(cosigner_line, message_html)
        self.assertIn(cosigner_line, message_text)

        language_line = "Inzendingstaal: Nederlands"
        self.assertIn(language_line, message_html)
        self.assertIn(language_line, message_text)

        # files are no longer attached to the e-mail, but links are included instead
        self.assertEqual(len(message.attachments), 0)

        expected_download_path_1 = reverse(
            "submissions:attachment-download",
            kwargs={"uuid": submission_file_attachment_1.uuid},
        )
        expected_download_url_1 = furl(f"https://example.com{expected_download_path_1}")
        expected_download_url_1.args["hash"] = submission_file_attachment_1.content_hash
        expected_download_path_2 = reverse(
            "submissions:attachment-download",
            kwargs={"uuid": submission_file_attachment_2.uuid},
        )
        expected_download_url_2 = furl(f"https://example.com{expected_download_path_2}")
        expected_download_url_2.args["hash"] = submission_file_attachment_2.content_hash

        self.assertIn(f"{expected_download_url_1} (my-foo.bin)", message_text)
        self.assertIn(f"{expected_download_url_2} (my-bar.txt)", message_text)

    def test_submission_with_email_backend_strip_out_urls(self):
        config = GlobalConfiguration.get_solo()
        config.email_template_netloc_allowlist = []
        config.save()

        email_form_options = dict(
            to_emails=["foo@bar.nl", "bar@foo.nl"],
        )

        data = {
            "foo": "https://someurl.com",
        }

        submission = SubmissionFactory.create(form=self.form)
        SubmissionStepFactory.create(
            submission=submission, form_step=self.fs, data=data
        )
        submission.completed_on = timezone.make_aware(datetime(2021, 1, 1, 12, 0, 0))
        submission.save()

        email_submission = EmailRegistration("email")
        email_submission.register_submission(submission, email_form_options)

        # Verify that email was sent
        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]
        message_html = message.alternatives[0][0]

        self.assertNotIn("https://someurl.com", message.body)
        self.assertNotIn("https://someurl.com", message_html)

    def test_submission_with_email_backend_keep_allowed_urls(self):
        config = GlobalConfiguration.get_solo()
        config.email_template_netloc_allowlist = ["allowed.com"]
        config.save()

        email_form_options = dict(
            to_emails=["foo@bar.nl", "bar@foo.nl"],
        )

        data = {
            "foo": "https://allowed.com",
        }

        submission = SubmissionFactory.from_data(data, completed=True)

        email_submission = EmailRegistration("email")
        email_submission.register_submission(submission, email_form_options)

        # Verify that email was sent
        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]
        message_html = message.alternatives[0][0]

        self.assertIn("https://allowed.com", message.body)
        self.assertIn("https://allowed.com", message_html)

    def test_html_in_email_subject(self):
        """Assert that HTML is not escaped in the subject of Emails"""

        submission = SubmissionFactory.from_components(
            completed=True,
            components_list=[
                {"key": "foo", "type": "textfield", "label": "foo"},
            ],
            form__name="Foo's bar",
            public_registration_reference="XYZ",
        )
        email_form_options = dict(
            to_emails=["foo@bar.nl", "bar@foo.nl"],
        )
        email_submission = EmailRegistration("email")

        with patch(
            "openforms.registrations.contrib.email.utils.EmailConfig.get_solo",
            return_value=EmailConfig(
                subject="Subject: {{ form_name }} - submission {{ public_reference }}",
            ),
        ):
            email_submission.register_submission(submission, email_form_options)

        # Verify that email was sent
        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]

        self.assertEqual(message.subject, "Subject: Foo's bar - submission XYZ")

    def test_register_and_update_paid_product(self):
        """
        the update payment email is now based on the registration email and includes attachments
        """
        submission = SubmissionFactory.from_components(
            completed=True,
            components_list=[
                {"key": "voornaam", "type": "textfield"},
                {"key": "someFile", "type": "file"},
            ],
            submitted_data={
                "voornaam": "Foo",
                "someFile": [
                    {  # truncated for brevity
                        "url": "some://url",
                        "name": "sample.bin",
                        "type": "application/foo",
                        "originalName": "sample.bin",
                    }
                ],
            },
            form__name="MyName",
            form__internal_name="MyInternalName",
            form__product__price=Decimal("11.35"),
            form__payment_backend="demo",
            registration_success=True,
            public_registration_reference="XYZ",
        )
        submission.completed_on = timezone.make_aware(datetime(2021, 1, 1, 12, 0, 0))
        payment = SubmissionPaymentFactory.for_submission(
            submission=submission, status=PaymentStatus.completed
        )
        report = submission.report
        submission_file_attachment = SubmissionFileAttachmentFactory.create(
            submission_step=submission.steps[0],
            form_key="someFile",
            file_name="my-foo.bin",
            content_type="application/foo",
            _component_configuration_path="components.1",
            _component_data_path="someFile",
        )

        self.assertTrue(submission.payment_required)

        email_form_options = dict(
            to_emails=["foo@bar.nl", "bar@foo.nl"],
            attachment_formats=[AttachmentFormat.pdf],
        )
        email_submission = EmailRegistration("email")

        with patch(
            "openforms.registrations.contrib.email.utils.EmailConfig.get_solo",
            return_value=EmailConfig(
                payment_subject="[Open Forms] {{ form_name }} - submission payment received {{ public_reference }}",
                content_html=TEST_TEMPLATE_NL,
                content_text=TEST_TEMPLATE_NL,
            ),
        ):
            email_submission.update_payment_status(submission, email_form_options)

        # Verify that email was sent
        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]
        self.assertEqual(
            message.subject,
            "[Open Forms] MyName - submission payment received XYZ",
        )
        self.assertEqual(message.from_email, "info@open-forms.nl")
        self.assertEqual(message.to, ["foo@bar.nl", "bar@foo.nl"])

        # Check that the template is used
        message_text = message.body
        message_html = message.alternatives[0][0]
        self.assertHTMLValid(message_html)
        self.assertIn("<table", message_html)
        self.assertNotIn("<table", message_text)

        detail_line = f"Betaling ontvangen voor {self.form.name} (ingezonden op 12:00:00 01-01-2021)"
        self.assertIn(detail_line, message_html)
        self.assertIn(detail_line, message_text)

        reference_line = f"Onze referentie: {submission.public_registration_reference}"
        self.assertIn(reference_line, message_html)
        self.assertIn(reference_line, message_text)

        order_line = f"Betalings-order ID: {payment.public_order_id}"
        self.assertIn(order_line, message_html)
        self.assertIn(order_line, message_text)

        self.assertIn("Voornaam: Foo", message_text)

        self.assertTagWithTextIn("td", "Voornaam", message_html)
        self.assertTagWithTextIn("td", "Foo", message_html)

        # check that the file attachment is present with a link
        self.assertTagWithTextIn("td", "Somefile", message_html)
        expected_download_path = reverse(
            "submissions:attachment-download",
            kwargs={"uuid": submission_file_attachment.uuid},
        )
        expected_download_url = furl(f"https://example.com{expected_download_path}")
        expected_download_url.args["hash"] = submission_file_attachment.content_hash
        expected_html = f"""
            <a href="{expected_download_url}" target="_blank" rel="noopener noreferrer">my-foo.bin</a>
        """
        self.assertInHTML(expected_html, message_html)

        self.assertEqual(len(message.attachments), 1)
        pdf_export = message.attachments[0]
        self.assertEqual(pdf_export[0], f"{report.title}.pdf")
        self.assertEqual(pdf_export[1], report.content.read())
        self.assertEqual(pdf_export[2], "application/pdf")

    def test_register_and_update_paid_product_with_payment_email_recipient(self):
        submission = SubmissionFactory.from_data(
            {"voornaam": "Foo"},
            form__product__price=Decimal("11.35"),
            form__payment_backend="demo",
            registration_success=True,
            public_registration_reference="XYZ",
        )
        self.assertTrue(submission.payment_required)

        email_form_options = dict(
            to_emails=["foo@bar.nl", "bar@foo.nl"],
            # payment_emails would override to_emails
            payment_emails=["payment@bar.nl", "payment@foo.nl"],
        )
        email_submission = EmailRegistration("email")
        email_submission.update_payment_status(submission, email_form_options)

        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]
        # check we used the payment_emails
        self.assertEqual(message.to, ["payment@bar.nl", "payment@foo.nl"])

    def test_no_reference_can_be_extracted(self):
        submission = SubmissionFactory.create(
            form=self.form,
            completed=True,
            registration_success=True,
            registration_result="irrelevant",
        )

        with self.assertRaises(NoSubmissionReference):
            extract_submission_reference(submission)

    @override_settings(DEFAULT_FROM_EMAIL="info@open-forms.nl")
    def test_submission_with_email_backend_export_csv_xlsx(self):
        email_form_options = dict(
            to_emails=["foo@bar.nl", "bar@foo.nl"],
            attachment_formats=[AttachmentFormat.csv, AttachmentFormat.xlsx],
        )

        data = {"someField": "value0", "someList": ["value1", "value2"]}

        submission = SubmissionFactory.create(form=self.form)
        submission_step = SubmissionStepFactory.create(
            submission=submission, form_step=self.fs, data=data
        )
        submission.completed_on = timezone.make_aware(datetime(2021, 1, 1, 12, 0, 0))
        submission.save()

        SubmissionFileAttachmentFactory.create(
            submission_step=submission_step,
            file_name="my-foo.bin",
            content_type="application/foo",
            form_key="attachment1",
        )
        SubmissionFileAttachmentFactory.create(
            submission_step=submission_step,
            file_name="my-bar.txt",
            content_type="text/bar",
            form_key="attachment2",
        )

        email_submission = EmailRegistration("email")
        email_submission.register_submission(submission, email_form_options)

        # Verify that email was sent
        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]

        # No upload attachments and two export attachments
        self.assertEqual(len(message.attachments), 2)

        csv_export, xlsx_export = message.attachments

        qs = Submission.objects.filter(pk=submission.pk).order_by("-pk")
        self.assertEqual(
            csv_export[0], f"{submission.form.admin_name} - submission.csv"
        )
        self.assertEqual(csv_export[1], create_submission_export(qs).export("csv"))
        self.assertEqual(csv_export[2], "text/csv")

        self.assertEqual(
            xlsx_export[0], f"{submission.form.admin_name} - submission.xlsx"
        )

        data = tablib.Dataset()
        binary_excel = xlsx_export[1]
        data.load(binary_excel)

        self.assertEqual(
            data.headers,
            [
                "Formuliernaam",
                "Inzendingdatum",
                "someField",
                "someList",
                "attachment1",
                "attachment2",
            ],
        )
        self.assertEqual(
            list(data._data[0]),
            [
                "MyInternalName",
                datetime(2021, 1, 1, 12, 0),
                "value0",
                "['value1', 'value2']",
                None,
                None,
            ],
        )
        self.assertEqual(
            xlsx_export[2],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    @override_settings(DEFAULT_FROM_EMAIL="info@open-forms.nl")
    def test_submission_with_email_backend_export_pdf(self):
        email_form_options = dict(
            to_emails=["foo@bar.nl", "bar@foo.nl"],
            attachment_formats=[AttachmentFormat.pdf],
        )

        data = {"foo": "bar", "some_list": ["value1", "value2"]}

        submission = SubmissionFactory.create(form=self.form)
        submission_step = SubmissionStepFactory.create(
            submission=submission, form_step=self.fs, data=data
        )
        submission.completed_on = timezone.make_aware(datetime(2021, 1, 1, 12, 0, 0))
        submission.save()

        report = SubmissionReportFactory.create(submission=submission)

        SubmissionFileAttachmentFactory.create(
            submission_step=submission_step,
            file_name="my-foo.bin",
            content_type="application/foo",
        )
        SubmissionFileAttachmentFactory.create(
            submission_step=submission_step,
            file_name="my-bar.txt",
            content_type="text/bar",
        )

        email_submission = EmailRegistration("email")
        email_submission.register_submission(submission, email_form_options)

        # Verify that email was sent
        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]

        # No upload attachments and one export attachment
        self.assertEqual(len(message.attachments), 1)

        pdf_export = message.attachments[0]

        self.assertEqual(pdf_export[0], f"{report.title}.pdf")
        self.assertEqual(pdf_export[1], report.content.read())
        self.assertEqual(pdf_export[2], "application/pdf")

    def test_regression_nested_components_columns(self):
        """
        Assert that columns in the form definition don't lead to template engine crashes.
        """
        submission = SubmissionFactory.from_components(
            completed=True,
            components_list=[
                {
                    "data": {
                        "values": [
                            {"label": "Hallo", "value": "hallo"},
                            {"label": "is it me", "value": "isItMe"},
                            {
                                "label": "you're looking for?",
                                "value": "youreLookingFor",
                            },
                        ]
                    },
                    "dataSrc": "values",
                    "key": "dropdownMetZoekfunctie",
                    "label": "Dropdown met zoekfunctie",
                    "showInEmail": True,
                },
                {
                    "key": "wachtwoord",
                    "label": "Wachtwoord",
                    "showInEmail": True,
                    "type": "password",
                },
                {
                    "key": "favorieteComponenten",
                    "label": "Favoriete componenten?",
                    "multiple": True,
                    "showInEmail": True,
                    "type": "textfield",
                },
                {
                    "key": "tijdstip",
                    "label": "Tijdstip",
                    "showInEmail": False,
                    "type": "time",
                },
                {
                    "components": [
                        {
                            "columns": [
                                {
                                    "components": [
                                        {
                                            "key": "dev1Naam",
                                            "label": "Naam",
                                            "showInEmail": False,
                                            "type": "textfield",
                                        }
                                    ],
                                },
                                {
                                    "components": [
                                        {
                                            "key": "dev1taken",
                                            "showInEmail": False,
                                            "type": "selectboxes",
                                            "values": [
                                                {
                                                    "label": "Backend",
                                                    "value": "backend",
                                                },
                                                {
                                                    "label": "Frontend",
                                                    "value": "frontend",
                                                },
                                                {
                                                    "label": "DevOops",
                                                    "value": "devOops",
                                                },
                                            ],
                                        }
                                    ],
                                },
                            ],
                            "key": "kolommen",
                            "label": "Kolommen",
                            "type": "columns",
                        },
                        {
                            "key": "nogEenOntwikkelaarToevoegen",
                            "label": "Nog een ontwikkelaar toevoegen?",
                            "showInEmail": False,
                            "type": "radio",
                            "values": [
                                {"label": "Ja", "value": "ja"},
                                {"label": "Nee", "value": "nee"},
                            ],
                        },
                    ],
                    "key": "dev1",
                    "label": "Ontwikkelaargegevens",
                    "legend": "Ontwikkelaargegevens",
                    "type": "fieldset",
                },
                {
                    "components": [
                        {
                            "columns": [
                                {
                                    "components": [
                                        {
                                            "key": "dev2Naam",
                                            "label": "Naam",
                                            "showInEmail": False,
                                            "type": "textfield",
                                        }
                                    ],
                                },
                                {
                                    "components": [
                                        {
                                            "key": "dev2taken",
                                            "label": "Taken",
                                            "showInEmail": False,
                                            "type": "selectboxes",
                                            "values": [
                                                {
                                                    "label": "Backend",
                                                    "value": "backend",
                                                },
                                                {
                                                    "label": "Frontend",
                                                    "value": "frontend",
                                                },
                                                {
                                                    "label": "DevOops",
                                                    "value": "devOops",
                                                },
                                            ],
                                        }
                                    ],
                                },
                            ],
                            "key": "kolommen1",
                            "label": "Kolommen",
                            "type": "columns",
                        }
                    ],
                    "key": "dev2",
                    "label": "Ontwikkelaargegevens",
                    "legend": "Ontwikkelaargegevens",
                },
            ],
            submitted_data={
                "dev1Naam": "Bart",
                "dev2Naam": "Silvia",
                "tijdstip": "11:00:00",
                "dev1taken": {"backend": True, "devOops": False, "frontend": False},
                "dev2taken": {"backend": True, "devOops": False, "frontend": True},
                "wachtwoord": "sdafsdfa",
                "favorieteComponenten": ["kaart"],
                "dropdownMetZoekfunctie": "isItMe",
                "nogEenOntwikkelaarToevoegen": "ja",
                "eMailadres": "foo@bar.nl",
            },
        )
        email_form_options = dict(
            to_emails=["foo@bar.nl", "bar@foo.nl"],
        )

        email_submission = EmailRegistration("email")
        email_submission.register_submission(submission, email_form_options)

        message = mail.outbox[0]

        message_html = message.alternatives[0][0]
        self.assertIn("Backend; Frontend", message_html)

    @patch("openforms.registrations.contrib.email.plugin.EmailConfig.get_solo")
    def test_with_global_config_attach_files(self, mock_get_solo):
        # cases with global config / options override tuples
        cases = [
            (EmailConfig(attach_files_to_email=True), {"attach_files_to_email": None}),
            (EmailConfig(attach_files_to_email=False), {"attach_files_to_email": True}),
        ]
        submission = SubmissionFactory.from_components(
            completed=True,
            completed_on=timezone.make_aware(datetime(2021, 1, 1, 12, 0, 0)),
            components_list=[
                {"key": "foo", "type": "textfield", "label": "foo"},
                {
                    "key": "some_list",
                    "type": "textfield",
                    "multiple": True,
                    "label": "some_list",
                },
                {"key": "file1", "type": "file", "label": "file1"},
                {"key": "file2", "type": "file", "label": "file2"},
            ],
            submitted_data={
                "foo": "bar",
                "some_list": ["value1", "value2"],
                "file1": [
                    {  # truncated for brevity
                        "url": "some://url",
                        "name": "my-foo.bin",
                        "type": "application/foo",
                        "originalName": "my-foo.bin",
                    }
                ],
                "file2": [
                    {  # truncated for brevity
                        "url": "some://url",
                        "name": "my-bar.txt",
                        "type": "text/bar",
                        "originalName": "my-bar.txt",
                    }
                ],
            },
            form__name="MyName",
            form__internal_name="MyInternalName",
            form__registration_backend="email",
        )
        SubmissionFileAttachmentFactory.create(
            form_key="file1",
            submission_step=submission.submissionstep_set.get(),
            file_name="my-foo.bin",
            content_type="application/foo",
        )
        SubmissionFileAttachmentFactory.create(
            form_key="file2",
            submission_step=submission.submissionstep_set.get(),
            file_name="my-bar.txt",
            content_type="text/bar",
        )
        email_submission = EmailRegistration("email")

        for global_config, options_override in cases:
            with self.subTest(
                global_config_attach=global_config.attach_files_to_email,
                form_options=options_override,
            ):
                email_form_options = {
                    "to_emails": ["foo@bar.nl", "bar@foo.nl"],
                    **options_override,
                }
                mock_get_solo.return_value = global_config

                email_submission.register_submission(submission, email_form_options)

                # Verify that email was sent
                self.assertEqual(len(mail.outbox), 1)

                message = mail.outbox.pop()

                # global config file used -> uploads are attached
                self.assertEqual(len(message.attachments), 2)
                file1, file2 = message.attachments
                self.assertEqual(file1[0], "my-foo.bin")
                self.assertEqual(file1[1], b"content")  # still bytes
                self.assertEqual(file1[2], "application/foo")

                self.assertEqual(file2[0], "my-bar.txt")
                self.assertEqual(file2[1], "content")  # this is text now
                self.assertEqual(file2[2], "text/bar")

    def test_user_defined_variables_included(self):
        submission = SubmissionFactory.from_components(
            completed=True,
            completed_on=timezone.make_aware(datetime(2021, 1, 1, 12, 0, 0)),
            components_list=[],
            form__registration_backend="email",
        )
        SubmissionValueVariableFactory.create(
            form_variable__source=FormVariableSources.user_defined,
            form_variable__name="User defined var 1",
            submission=submission,
            key="user_defined_var1",
            value="test1",
        )
        SubmissionValueVariableFactory.create(
            form_variable__source=FormVariableSources.user_defined,
            form_variable__name="User defined var 2",
            submission=submission,
            key="user_defined_var2",
            value="test2",
        )

        email_form_options = dict(to_emails=["foo@bar.nl", "bar@foo.nl"])
        email_submission = EmailRegistration("email")

        email_submission.register_submission(submission, email_form_options)

        # Verify that email was sent
        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]
        message_text = message.body

        self.assertIn("User defined var 1: test1", message_text)
        self.assertIn("User defined var 2: test2", message_text)

    def test_mime_body_parts_have_content_langauge(self):
        submission = SubmissionFactory.create(
            language_code="en",
            completed=True,
            form__generate_minimal_setup=True,
            form__registration_backend="email",
        )

        email_submission = EmailRegistration("email")

        with patch(
            "openforms.registrations.contrib.email.utils.EmailConfig.get_solo",
            return_value=EmailConfig(
                content_html=TEST_TEMPLATE_NL,
                content_text=TEST_TEMPLATE_NL,
            ),
        ):
            email_submission.register_submission(
                submission, {"to_emails": ["foo@example.com"]}
            )

        message = mail.outbox[0]
        self.assertEqual(message.extra_headers["Content-Language"], "en")
        self.assertIn("Engels", message.body)
        html_message = message.alternatives[0][0]
        self.assertIn("Engels", html_message)

    @tag("gh-3144")
    def test_file_attachments_in_registration_email(self):
        submission = SubmissionFactory.create()
        attachment1 = TemporaryFileUploadFactory.create(
            file_name="normalAttachment.png"
        )
        attachment2 = TemporaryFileUploadFactory.create(
            file_name="attachmentInFieldset.png"
        )
        attachment3 = TemporaryFileUploadFactory.create(
            file_name="attachmentInRepeatingGroup.png"
        )
        submission_step = SubmissionStepFactory.create(
            submission=submission,
            form_step__form_definition__configuration={
                "components": [
                    {"key": "normalAttachment", "type": "file"},
                    {
                        "key": "repeatingGroup",
                        "type": "editgrid",
                        "components": [
                            {"key": "attachmentInRepeatingGroup", "type": "file"}
                        ],
                    },
                    {
                        "key": "fieldset",
                        "type": "fieldset",
                        "components": [{"key": "attachmentInFieldset", "type": "file"}],
                    },
                ]
            },
            data={
                "normalAttachment": [
                    {
                        "url": f"http://openforms.nl/api/v2/submissions/files/{attachment1.uuid}",
                        "data": {
                            "url": f"http://openforms.nl/api/v2/submissions/files/{attachment1.uuid}",
                            "form": "",
                            "name": "test2.pdf",
                            "size": 9324,
                            "baseUrl": "http://openforms.nl/api/v2/",
                            "project": "",
                        },
                        "name": "test2-b3909e62-983a-4027-9b5f-eca148f081d7.pdf",
                        "size": 9324,
                        "type": "application/pdf",
                        "storage": "url",
                        "originalName": "test.pdf",
                    }
                ],
                "attachmentInFieldset": [
                    {
                        "url": f"http://openforms.nl/api/v2/submissions/files/{attachment2.uuid}",
                        "data": {
                            "url": f"http://openforms.nl/api/v2/submissions/files/{attachment2.uuid}",
                            "form": "",
                            "name": "test2.pdf",
                            "size": 9324,
                            "baseUrl": "http://openforms.nl/api/v2/",
                            "project": "",
                        },
                        "name": "test2-b3909e62-983a-4027-9b5f-eca148f081d7.pdf",
                        "size": 9324,
                        "type": "application/pdf",
                        "storage": "url",
                        "originalName": "test.pdf",
                    }
                ],
                "repeatingGroup": [
                    {
                        "attachmentInRepeatingGroup": [
                            {
                                "url": f"http://openforms.nl/api/v2/submissions/files/{attachment3.uuid}",
                                "data": {
                                    "url": f"http://openforms.nl/api/v2/submissions/files/{attachment3.uuid}",
                                    "form": "",
                                    "name": "test2.pdf",
                                    "size": 9324,
                                    "baseUrl": "http://openforms.nl/api/v2/",
                                    "project": "",
                                },
                                "name": "test2-b3909e62-983a-4027-9b5f-eca148f081d7.pdf",
                                "size": 9324,
                                "type": "application/pdf",
                                "storage": "url",
                                "originalName": "test.pdf",
                            }
                        ]
                    }
                ],
            },
        )
        attach_uploads_to_submission_step(submission_step)

        subject, body_html, body_text = EmailRegistration.render_registration_email(
            submission, is_payment_update=False
        )

        with self.subTest("Normal attachment"):
            self.assertIn("normalAttachment.png", body_text)
            self.assertIn("normalAttachment.png", body_html)

        with self.subTest("Attachment in repeating group"):
            self.assertIn("attachmentInRepeatingGroup.png", body_text)
            self.assertIn("attachmentInRepeatingGroup.png", body_html)

        with self.subTest("Attachment in fieldset"):
            self.assertIn("attachmentInFieldset.png", body_text)
            self.assertIn("attachmentInFieldset.png", body_html)

    def test_extra_headers(self):
        submission = SubmissionFactory.create()
        email_form_options = dict(
            to_emails=["foo@bar.nl", "bar@foo.nl"],
        )
        email_submission = EmailRegistration("email")

        with patch(
            "openforms.registrations.contrib.email.plugin.send_mail_html"
        ) as mock_send:
            email_submission.register_submission(submission, email_form_options)

        args = mock_send.call_args.kwargs
        self.assertEqual(
            args["extra_headers"][X_OF_CONTENT_UUID_HEADER],
            str(submission.uuid),
        )
        self.assertEqual(
            args["extra_headers"][X_OF_CONTENT_TYPE_HEADER],
            EmailContentTypeChoices.submission,
        )
        self.assertEqual(
            args["extra_headers"][X_OF_EVENT_HEADER],
            EmailEventChoices.registration,
        )

    def test_with_deferred_registration(self):
        config = GlobalConfiguration.get_solo()
        config.wait_for_payment_to_register = True
        config.save()
        submission = SubmissionFactory.create(
            with_public_registration_reference=True,
            with_completed_payment=True,
        )
        assert submission.payment_required
        assert submission.payment_user_has_paid
        options: EmailOptions = {
            "to_emails": ["registration@example.com"],
            "attachment_formats": [],
            "payment_emails": ["payments@example.com"],
            "attach_files_to_email": False,
            "email_subject": None,
        }
        plugin = EmailRegistration("email")

        plugin.register_submission(submission, options)

        # Verify that email was sent
        emails = mail.outbox
        self.assertEqual(len(emails), 2)
