from django.test import TestCase

from openforms.appointments.contrib.qmatic.tests.factories import ServiceFactory
from openforms.submissions.public_references import set_submission_reference
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
)

from ..plugin import JSONRegistration


class JSONBackendTests(TestCase):
    # VCR_TEST_FILES = VCR_TEST_FILES

    def test_submission_with_json_backend(self):
        submission = SubmissionFactory.from_components(
            [
                {"key": "firstName", "type": "textField"},
                {"key": "lastName", "type": "textfield"},
                {"key": "file", "type": "file"},
            ],
            completed=True,
            submitted_data={
                "firstName": "We Are",
                "lastName": "Checking",
                "file": [
                    {
                        "url": "some://url",
                        "name": "my-foo.bin",
                        "type": "application/foo",
                        "originalName": "my-foo.bin",
                    }
                ],
            },
            bsn="123456789",
        )

        submission_file_attachment = SubmissionFileAttachmentFactory.create(
            form_key="file",
            submission_step=submission.submissionstep_set.get(),
            file_name="test_file.txt",
            content_type="application/text",
            content__data=b"This is example content.",
            _component_configuration_path="components.2",
            _component_data_path="file",
        )

        json_form_options = dict(
            service=ServiceFactory(),
            relative_api_endpoint="test",
            form_variables=["firstName", "lastName", "file", "auth_bsn"],
        )
        email_submission = JSONRegistration("json_plugin")

        set_submission_reference(submission)

        data_to_be_sent = email_submission.register_submission(submission, json_form_options)

        expected_data_to_be_sent = {
            "values": {
                "firstName": "We Are",
                "lastName": "Checking",
                "file": b"This is example content.",
                "auth_bsn": "123456789",
            }
        }
        self.assertEqual(data_to_be_sent, expected_data_to_be_sent)

    # def test_create_submission_with_digid(self):
    #     v2_options: RegistrationOptionsV2 = {
    #         "objects_api_group": self.group,
    #         "version": 2,
    #         "objecttype": UUID("f3f1b370-97ed-4730-bc7e-ebb20c230377"),
    #         "objecttype_version": 1,
    #         "update_existing_object": False,
    #         "auth_attribute_path": [],
    #         "variables_mapping": [
    #             {
    #                 "variable_key": "auth_context",
    #                 "target_path": ["auth_context"],
    #             },
    #         ],
    #         "iot_attachment": "",
    #         "iot_submission_csv": "",
    #         "iot_submission_report": "",
    #     }
    #
    #
    #     submission = SubmissionFactory.from_components(
    #         [
    #             # fmt: off
    #             {
    #                 "key": "firstName",
    #                 "type": "textField"
    #             },
    #             {
    #                 "key": "lastName",
    #                 "type": "textfield",
    #             },
    #             # fmt: on
    #         ],
    #         completed=True,
    #         submitted_data={
    #             "firstName": "We Are",
    #             "lastName": "Checking",
    #         },
    #         with_public_registration_reference=True,
    #         auth_info__is_digid=True,
    #     )
    #     expected = {
    #         "middel": "digid",
    #         "loa": "urn:oasis:names:tc:SAML:2.0:ac:classes:MobileTwoFactorContract",
    #         "vertegenwoordigde": "",
    #         "soort_vertegenwoordigde": "",
    #         "gemachtigde": "999991607",
    #         "soort_gemachtigde": "bsn",
    #         "actor": "",
    #         "soort_actor": "",
    #     }
    #
    #     ObjectsAPIRegistrationData.objects.create(submission=submission)
    #
    #     handler = ObjectsAPIV2Handler()
    #     record_data = handler.get_record_data(
    #         submission=submission, options=v2_options
    #     )
    #
    #     data = record_data["data"]
    #     print(submission.data)
    #     self.assertEqual(data["authn"], expected)
