from datetime import datetime
from decimal import Decimal

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from furl import furl

from openforms.config.models import GlobalConfiguration
from openforms.forms.tests.factories import FormFactory
from openforms.payments.constants import PaymentStatus
from openforms.payments.tests.factories import SubmissionPaymentFactory
from openforms.submissions.exports import create_submission_export
from openforms.submissions.models import Submission
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
    SubmissionReportFactory,
    SubmissionStepFactory,
)
from openforms.utils.tests.html_assert import HTMLAssertMixin

from ....service import NoSubmissionReference, extract_submission_reference
from ..constants import AttachmentFormat
from ..plugin import EmailRegistration


@override_settings(
    DEFAULT_FROM_EMAIL="info@open-forms.nl", BASE_URL="https://example.com"
)
class EmailBackendTests(HTMLAssertMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.form = FormFactory.create(
            generate_minimal_setup=True,
            name="MyName",
            internal_name="MyInternalName",
            registration_backend="email",
        )
        cls.fs = cls.form.formstep_set.get()
        cls.fd = cls.fs.form_definition

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
        )
        submission_file_attachment_1 = SubmissionFileAttachmentFactory.create(
            form_key="file1",
            submission_step=submission.submissionstep_set.get(),
            file_name="my-foo.bin",
            content_type="application/foo",
        )
        submission_file_attachment_2 = SubmissionFileAttachmentFactory.create(
            form_key="file2",
            submission_step=submission.submissionstep_set.get(),
            file_name="my-bar.txt",
            content_type="text/bar",
        )
        email_form_options = dict(to_emails=["foo@bar.nl", "bar@foo.nl"])
        email_submission = EmailRegistration("email")

        email_submission.register_submission(submission, email_form_options)

        # Verify that email was sent
        self.assertEqual(len(mail.outbox), 1)

        # Verify we've generated a public_registration_reference
        self.assertNotEqual(submission.public_registration_reference, "")

        message = mail.outbox[0]
        self.assertEqual(
            message.subject,
            _("[Open Forms] {form_name} - submission {public_reference}").format(
                form_name=submission.form.admin_name,
                public_reference=submission.public_registration_reference,
            ),
        )
        self.assertEqual(message.from_email, "info@open-forms.nl")
        self.assertEqual(message.to, ["foo@bar.nl", "bar@foo.nl"])

        # Check that the template is used
        message_text = message.body
        message_html = message.alternatives[0][0]
        self.assertHTMLValid(message_html)
        self.assertIn("<table", message_html)
        self.assertNotIn("<table", message_text)

        detail_line = _(
            "Submission details for %(form_name)s (submitted on %(datetime)s)"
        ) % dict(
            form_name=self.form.admin_name,
            datetime="12:00:00 01-01-2021",
        )
        self.assertIn(detail_line, message_html)
        self.assertIn(detail_line, message_text)

        self.assertIn("foo: bar", message_text)
        self.assertIn("some_list: value1, value2", message_text)

        self.assertTagWithTextIn("td", "foo", message_html)
        self.assertTagWithTextIn("td", "bar", message_html)
        self.assertTagWithTextIn("td", "some_list", message_html)
        self.assertTagWithTextIn("td", "value1, value2", message_html)

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

        self.assertIn("https://allowed.com", message.body)
        self.assertIn("https://allowed.com", message_html)

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
        )

        self.assertTrue(submission.payment_required)

        email_form_options = dict(
            to_emails=["foo@bar.nl", "bar@foo.nl"],
            attachment_formats=[AttachmentFormat.pdf],
        )
        email_submission = EmailRegistration("email")
        email_submission.update_payment_status(submission, email_form_options)

        # Verify that email was sent
        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]
        self.assertEqual(
            message.subject,
            _(
                "[Open Forms] {form_name} - submission payment received {public_reference}"
            ).format(
                form_name=submission.form.admin_name,
                public_reference=submission.public_registration_reference,
            ),
        )
        self.assertEqual(message.from_email, "info@open-forms.nl")
        self.assertEqual(message.to, ["foo@bar.nl", "bar@foo.nl"])

        # Check that the template is used
        message_text = message.body
        message_html = message.alternatives[0][0]
        self.assertHTMLValid(message_html)
        self.assertIn("<table", message_html)
        self.assertNotIn("<table", message_text)

        detail_line = _(
            "Submission payment received for %(form_name)s (submitted on %(datetime)s)"
        ) % dict(
            form_name=self.form.admin_name,
            datetime="12:00:00 01-01-2021",
        )
        self.assertIn(detail_line, message_html)
        self.assertIn(detail_line, message_text)

        reference_line = _("Our reference: %(public_reference)s") % dict(
            public_reference=submission.public_registration_reference,
        )
        self.assertIn(reference_line, message_html)
        self.assertIn(reference_line, message_text)

        order_line = _("Payment order ID: %(payment_order_id)s") % dict(
            payment_order_id=payment.public_order_id,
        )
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

        data = {"foo": "bar", "some_list": ["value1", "value2"]}

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

        # No upload attachments and two export attachments
        self.assertEqual(len(message.attachments), 2)

        csv_export, xlsx_export = message.attachments

        qs = Submission.objects.filter(pk=submission.pk)
        self.assertEqual(
            csv_export[0], f"{submission.form.admin_name} - submission.csv"
        )
        self.assertEqual(csv_export[1], create_submission_export(qs).export("csv"))
        self.assertEqual(csv_export[2], "text/csv")

        self.assertEqual(
            xlsx_export[0], f"{submission.form.admin_name} - submission.xlsx"
        )
        self.assertEqual(xlsx_export[1], create_submission_export(qs).export("xlsx"))
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
        self.assertIn("Backend, Frontend", message_html)
