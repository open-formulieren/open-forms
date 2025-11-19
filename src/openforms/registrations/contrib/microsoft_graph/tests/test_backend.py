import json
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.utils.translation import gettext as _

from freezegun import freeze_time
from O365 import Account
from O365.drive import Drive
from privates.test import temp_private_root

from openforms.contrib.microsoft.tests.factories import MSGraphServiceFactory
from openforms.payments.constants import PaymentStatus
from openforms.payments.tests.factories import SubmissionPaymentFactory
from openforms.registrations.exceptions import RegistrationFailed
from openforms.submissions.public_references import set_submission_reference
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
    SubmissionReportFactory,
    SubmissionStepFactory,
)
from openforms.utils.tests.cache import clear_caches

from ..config import MicrosoftGraphOptions
from ..models import (
    MSGraphRegistrationConfig,
)
from ..plugin import MSGraphRegistration


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
        cls.msgraph_config_patcher = patch(
            "openforms.registrations.contrib.microsoft_graph.models.MSGraphRegistrationConfig.get_solo",
            return_value=MSGraphRegistrationConfig(
                service=MSGraphServiceFactory.build()
            ),
        )

    def setUp(self):
        super().setUp()

        self.msgraph_config_patcher.start()
        self.addCleanup(self.msgraph_config_patcher.stop)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.addClassCleanup(clear_caches)

    @patch.object(MockFolder, "upload_file", return_value=None)
    def test_submission(self, upload_mock):
        data = {"foo": "bar", "some_list": ["value1", "value2"]}

        components = [
            {
                "key": "foo",
                "type": "textfield",
            },
            {
                "key": "some_list",
                "type": "textfield",
                "multiple": True,
            },
        ]
        submission = SubmissionFactory.from_components(
            components,
            data,
            completed=True,
            with_report=True,
            form__name="MyName",
            form__internal_name="MyInternalName: with (extra)",
            form__registration_backend="microsoft-graph",
            form__product__price=Decimal("11.35"),
            form__payment_backend="demo",
        )
        submission_step = submission.steps[0]
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

        set_submission_reference(submission)

        options: MicrosoftGraphOptions = {
            "folder_path": "/open-forms/",
            "drive_id": "",
        }
        with (
            patch.object(Account, "is_authenticated", True),
            patch.object(Drive, "get_root_folder", return_value=MockFolder()),
        ):
            graph_submission = MSGraphRegistration("microsoft-graph")
            graph_submission.register_submission(submission, options)

        # made the calls
        self.assertEqual(upload_mock.call_count, 5)

        folder = f"/open-forms/myinternalname-with-extra/{submission.public_registration_reference}"
        calls = upload_mock.call_args_list

        with self.subTest("report"):
            call = calls[0]
            path = f"{folder}/report.pdf"
            self.assertEqual(call.args[1], path)

        with self.subTest("data"):
            call = calls[1]
            path = f"{folder}/data.json"
            self.assertEqual(call.args[1], path)

        with self.subTest("data contains submission language code"):
            call = calls[1]
            data = json.load(call[1]["stream"])

            self.assertEqual(
                data["__metadata__"]["submission_language"], submission.language_code
            )

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
        submission = SubmissionFactory.from_components(
            components_list=[
                {"type": "textfield", "key": "foo", "label": "Foo"},
                {
                    "type": "textfield",
                    "key": "some_list",
                    "label": "Some list",
                    "multiple": True,
                },
            ],
            submitted_data={
                "foo": "bar",
                "some_list": ["value1", "value2"],
            },
            form__name="MyName",
            form__internal_name="MyInternalName",
            form__registration_backend="microsoft-graph",
            form__product__price=Decimal("11.35"),
            form__payment_backend="demo",
            public_registration_reference="abc123",
            registration_success=True,
        )
        SubmissionPaymentFactory.for_submission(
            submission, status=PaymentStatus.completed
        )

        options: MicrosoftGraphOptions = {
            "folder_path": "/open-forms/",
            "drive_id": "",
        }
        with (
            patch.object(Account, "is_authenticated", True),
            patch.object(Drive, "get_root_folder", return_value=MockFolder()),
        ):
            graph_submission = MSGraphRegistration("microsoft-graph")
            graph_submission.update_payment_status(submission, options)

        # got the reference
        self.assertNotEqual(submission.public_registration_reference, "")

        # made the calls
        self.assertEqual(upload_mock.call_count, 1)

        folder = (
            f"/open-forms/myinternalname/{submission.public_registration_reference}"
        )
        calls = upload_mock.call_args_list

        with self.subTest("payment status"):
            call = calls[0]
            path = f"{folder}/payment_status.txt"
            self.assertEqual(call.args[1], path)
            content = call.kwargs["stream"].read().decode("utf8")
            self.assertEqual(content, f"{_('payment received')}: € 11.35")

    def test_with_date_related_values(self):
        """Ensure that date-related values are properly serialized to JSON."""
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "date",
                    "type": "date",
                    "label": "Date",
                    "multiple": True,
                },
                {
                    "key": "time",
                    "type": "time",
                    "label": "Time",
                },
                {
                    "key": "datetime",
                    "type": "datetime",
                    "label": "Datetime",
                },
            ],
            submitted_data={
                "date": ["2025-11-19", "2025-11-20"],
                "time": "12:34:56",
                "datetime": "2025-11-19T12:34:56+01:00",
            },
            completed=True,
            with_report=True,
            form__name="MyName",
            form__internal_name="MyInternalName: with (extra)",
            form__registration_backend="microsoft-graph",
        )
        set_submission_reference(submission)

        options: MicrosoftGraphOptions = {
            "folder_path": "/open-forms/",
            "drive_id": "",
        }
        graph_submission = MSGraphRegistration("microsoft-graph")

        with (
            patch.object(Account, "is_authenticated", True),
            patch.object(Drive, "get_root_folder", return_value=MockFolder()),
        ):
            try:
                graph_submission.register_submission(submission, options)
            except TypeError as e:
                raise self.failureException("Registration failed unexpectedly") from e


@temp_private_root()
@patch.object(MockFolder, "upload_file", return_value=None)
class MSGraphRegistrationOptionsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.msgraph_config_patcher = patch(
            "openforms.registrations.contrib.microsoft_graph.models.MSGraphRegistrationConfig.get_solo",
            return_value=MSGraphRegistrationConfig(
                service=MSGraphServiceFactory.build()
            ),
        )

    def setUp(self):
        super().setUp()

        self.msgraph_config_patcher.start()
        self.addCleanup(self.msgraph_config_patcher.stop)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.addClassCleanup(clear_caches)

    def test_folder_path(self, upload_mock):
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "foo",
                    "type": "textfield",
                }
            ],
            submitted_data={"foo": "bar"},
            completed=True,
            with_report=True,
            form__name="Test Form",
            form__internal_name="Internal Test Form (with extra)",
            form__registration_backend="microsoft-graph",
        )
        registration_options: MicrosoftGraphOptions = {
            "folder_path": "/sites/my-site/open-forms/",
            "drive_id": "",
        }

        set_submission_reference(submission)

        with (
            patch.object(Account, "is_authenticated", True),
            patch.object(Drive, "get_root_folder", return_value=MockFolder()),
        ):
            graph_submission = MSGraphRegistration("microsoft-graph")
            graph_submission.register_submission(submission, registration_options)

        # made the calls
        self.assertEqual(upload_mock.call_count, 2)

        folder = f"/sites/my-site/open-forms/internal-test-form-with-extra/{submission.public_registration_reference}"
        calls = upload_mock.call_args_list

        with self.subTest("report"):
            call = calls[0]
            path = f"{folder}/report.pdf"
            self.assertEqual(call.args[1], path)

        with self.subTest("data"):
            call = calls[1]
            path = f"{folder}/data.json"
            self.assertEqual(call.args[1], path)

    def test_folder_path_with_date(self, upload_mock):
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "foo",
                    "type": "textfield",
                }
            ],
            submitted_data={"foo": "bar"},
            completed=True,
            with_report=True,
            form__name="Test Form",
            form__internal_name="Internal Test Form (with extra)",
            form__registration_backend="microsoft-graph",
        )
        SubmissionFileAttachmentFactory.create(
            submission_step=submission.steps[0],
            file_name="my-foo.bin",
            content_type="application/foo",
        )
        registration_options: MicrosoftGraphOptions = {
            "folder_path": "/open-forms/{{ year }}-{{ month }}-{{ day }}",
            "drive_id": "",
        }

        set_submission_reference(submission)

        with freeze_time("2021-07-16"):
            with (
                patch.object(Account, "is_authenticated", True),
                patch.object(Drive, "get_root_folder", return_value=MockFolder()),
            ):
                graph_submission = MSGraphRegistration("microsoft-graph")
                graph_submission.register_submission(submission, registration_options)

        # made the calls
        self.assertEqual(upload_mock.call_count, 3)

        folder = f"/open-forms/2021-07-16/internal-test-form-with-extra/{submission.public_registration_reference}"
        calls = upload_mock.call_args_list

        with self.subTest("report"):
            call = calls[0]
            path = f"{folder}/report.pdf"
            self.assertEqual(call.args[1], path)

        with self.subTest("data"):
            call = calls[1]
            path = f"{folder}/data.json"
            self.assertEqual(call.args[1], path)

        with self.subTest("attachment"):
            call = calls[2]
            path = f"{folder}/attachments/my-foo.bin"
            self.assertEqual(call.args[1], path)


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

        options: MicrosoftGraphOptions = {
            "folder_path": "/open-forms/",
            "drive_id": "",
        }
        with self.assertRaises(RegistrationFailed):
            with (
                patch.object(Account, "is_authenticated", True),
                patch.object(Drive, "get_root_folder", return_value=MockFolder()),
            ):
                graph_submission = MSGraphRegistration("microsoft-graph")
                graph_submission.register_submission(submission, options)
