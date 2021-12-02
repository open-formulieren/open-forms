from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.utils.translation import ugettext as _

from O365 import Account
from O365.drive import Drive
from privates.test import temp_private_root

from openforms.contrib.microsoft.tests.factories import MSGraphServiceFactory
from openforms.payments.constants import PaymentStatus
from openforms.payments.tests.factories import SubmissionPaymentFactory
from openforms.registrations.contrib.microsoft_graph.models import (
    MSGraphRegistrationConfig,
)
from openforms.registrations.contrib.microsoft_graph.plugin import MSGraphRegistration
from openforms.registrations.exceptions import RegistrationFailed
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
    SubmissionReportFactory,
    SubmissionStepFactory,
)


class MockFolder:
    # used as return value for another mock
    def get_root_folder(self):
        pass

    def upload_file(self, *args, **kwargs):
        pass


@temp_private_root()
class MSGraphRegistrationBackendTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        config = MSGraphRegistrationConfig.get_solo()
        config.service = MSGraphServiceFactory.create()
        config.save()

    @patch.object(MockFolder, "upload_file", return_value=None)
    def test_submission(self, upload_mock):
        data = {"foo": "bar", "some_list": ["value1", "value2"]}

        submission = SubmissionFactory.create(
            form__name="MyName",
            form__internal_name="MyInternalName: with (extra)",
            form__registration_backend="microsoft-graph",
            form__product__price=Decimal("11.35"),
            form__payment_backend="demo",
        )
        submission_step = SubmissionStepFactory.create(submission=submission, data=data)
        submission.save()

        SubmissionReportFactory.create(submission=submission)
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

        with patch.object(Account, "is_authenticated", True), patch.object(
            Drive, "get_root_folder", return_value=MockFolder()
        ):
            graph_submission = MSGraphRegistration("microsoft-graph")
            graph_submission.register_submission(submission, None)

        # got the reference
        self.assertNotEqual(submission.public_registration_reference, "")

        # made the calls
        self.assertEqual(upload_mock.call_count, 5)

        folder = f"open-forms/myinternalname-with-extra/{submission.public_registration_reference}"
        calls = upload_mock.call_args_list

        with self.subTest("report"):
            call = calls[0]
            path = f"{folder}/report.pdf"
            self.assertEqual(call.args[1], path)

        with self.subTest("data"):
            call = calls[1]
            path = f"{folder}/data.json"
            self.assertEqual(call.args[1], path)

        with self.subTest("attachment 1"):
            call = calls[2]
            path = f"{folder}/attachments/my-foo.bin"
            self.assertEqual(call.args[1], path)

        with self.subTest("attachment 2"):
            call = calls[3]
            path = f"{folder}/attachments/my-bar.txt"
            self.assertEqual(call.args[1], path)

        with self.subTest("payment status"):
            call = calls[4]
            path = f"{folder}/payment_status.txt"
            self.assertEqual(call.args[1], path)
            content = call.kwargs["stream"].read().decode("utf8")
            self.assertEqual(content, f"{_('payment required')}: € 11.35")

    @patch.object(MockFolder, "upload_file", return_value=None)
    def test_update_payment_status(self, upload_mock):
        data = {"foo": "bar", "some_list": ["value1", "value2"]}

        submission = SubmissionFactory.create(
            form__name="MyName",
            form__internal_name="MyInternalName",
            form__registration_backend="microsoft-graph",
            form__product__price=Decimal("11.35"),
            form__payment_backend="demo",
            public_registration_reference="abc123",
            registration_success=True,
        )
        submission_step = SubmissionStepFactory.create(submission=submission, data=data)
        submission.save()

        SubmissionPaymentFactory.for_submission(
            submission, status=PaymentStatus.completed
        )

        with patch.object(Account, "is_authenticated", True), patch.object(
            Drive, "get_root_folder", return_value=MockFolder()
        ):
            graph_submission = MSGraphRegistration("microsoft-graph")
            graph_submission.update_payment_status(submission, None)

        # got the reference
        self.assertNotEqual(submission.public_registration_reference, "")

        # made the calls
        self.assertEqual(upload_mock.call_count, 1)

        folder = f"open-forms/myinternalname/{submission.public_registration_reference}"
        calls = upload_mock.call_args_list

        with self.subTest("payment status"):
            call = calls[0]
            path = f"{folder}/payment_status.txt"
            self.assertEqual(call.args[1], path)
            content = call.kwargs["stream"].read().decode("utf8")
            self.assertEqual(content, f"{_('payment received')}: € 11.35")


class MSGraphRegistrationBackendFailureTests(TestCase):
    def test_no_service_configured_raises_registration_error(self):
        submission = SubmissionFactory.create(
            form__registration_backend="microsoft-graph",
        )
        SubmissionStepFactory.create(
            submission=submission,
            data={"foo": "bar", "some_list": ["value1", "value2"]},
        )
        SubmissionReportFactory.create(submission=submission)

        with self.assertRaises(RegistrationFailed):
            with patch.object(Account, "is_authenticated", True), patch.object(
                Drive, "get_root_folder", return_value=MockFolder()
            ):
                graph_submission = MSGraphRegistration("microsoft-graph")
                graph_submission.register_submission(submission, None)
