from unittest.mock import patch

from django.test import TestCase

from O365 import Account
from O365.drive import Folder
from privates.test import temp_private_root

from openforms.contrib.microsoft.tests.factories import MSGraphServiceFactory
from openforms.registrations.contrib.microsoft_graph.models import (
    MSGraphRegistrationConfig,
)
from openforms.registrations.contrib.microsoft_graph.plugin import MSGraphRegistration
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
    SubmissionStepFactory,
)


@temp_private_root()
class MSGraphRegistrationBackendTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        config = MSGraphRegistrationConfig.get_solo()
        config.service = MSGraphServiceFactory.create()
        config.save()

    @patch.object(Folder, "upload_file", return_value=None)
    def test_submission(self, upload_mock):
        data = {"foo": "bar", "some_list": ["value1", "value2"]}

        submission = SubmissionFactory.create(
            form__name="MyName",
            form__internal_name="MyInternalName",
            form__registration_backend="microsoft-graph",
        )
        submission_step = SubmissionStepFactory.create(submission=submission, data=data)
        # submission.completed_on = timezone.make_aware(datetime(2021, 1, 1, 12, 0, 0))
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
        with patch.object(Account, "is_authenticated", True):
            graph_submission = MSGraphRegistration("microsoft-graph")
            graph_submission.register_submission(submission, None)

        upload_mock.assert_called()
