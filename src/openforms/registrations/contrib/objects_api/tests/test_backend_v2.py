from pathlib import Path
from unittest.mock import patch

from django.test import TestCase, tag
from django.utils import timezone

from freezegun import freeze_time
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from openforms.registrations.contrib.objects_api.models import (
    ObjectsAPIRegistrationData,
)
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
)
from openforms.utils.tests.vcr import OFVCRMixin

from ..models import ObjectsAPIConfig
from ..plugin import PLUGIN_IDENTIFIER, ObjectsAPIRegistration
from ..typing import RegistrationOptionsV2


@freeze_time("2024-03-19T13:40:34.222258+00:00")
class ObjectsAPIBackendV2Tests(OFVCRMixin, TestCase):
    """This test case requires the Objects & Objecttypes API and Open Zaak to be running.

    See the relevant Docker compose in the ``docker/`` folder.
    """

    maxDiff = None
    VCR_TEST_FILES = Path(__file__).parent / "files"

    def setUp(self):
        super().setUp()

        config = ObjectsAPIConfig(
            objects_service=ServiceFactory.build(
                api_root="http://localhost:8002/api/v2/",
                api_type=APITypes.orc,
                oas="https://example.com/",
                header_key="Authorization",
                # See the docker compose fixtures:
                header_value="Token 7657474c3d75f56ae0abd0d1bf7994b09964dca9",
                auth_type=AuthTypes.api_key,
            ),
            drc_service=ServiceFactory.build(
                api_root="http://localhost:8003/documenten/api/v1/",
                api_type=APITypes.drc,
                # See the docker compose fixtures:
                client_id="test_client_id",
                secret="test_secret_key",
                auth_type=AuthTypes.zgw,
            ),
        )

        config_patcher = patch(
            "openforms.registrations.contrib.objects_api.models.ObjectsAPIConfig.get_solo",
            return_value=config,
        )
        self.mock_get_config = config_patcher.start()
        self.addCleanup(config_patcher.stop)

    def test_submission_with_objects_api_v2(self):
        submission = SubmissionFactory.from_components(
            [
                # fmt: off
                {
                    "key": "age",
                    "type": "number"
                },
                {
                    "key": "lastname",
                    "type": "textfield",
                },
                {
                    "key": "location",
                    "type": "map",
                },
                # fmt: on
            ],
            completed=True,
            submitted_data={
                "age": 20,
                "lastname": "My last name",
                "location": [52.36673378967122, 4.893164274470299],
            },
        )

        v2_options: RegistrationOptionsV2 = {
            "version": 2,
            # See the docker compose fixtures for more info on these values:
            "objecttype": "http://objecttypes-web:8000/api/v2/objecttypes/8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
            "objecttype_version": 3,
            "upload_submission_csv": True,
            "informatieobjecttype_submission_report": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/7a474713-0833-402a-8441-e467c08ac55b",
            "informatieobjecttype_submission_csv": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/b2d83b94-9b9b-4e80-a82f-73ff993c62f3",
            "informatieobjecttype_attachment": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/531f6c1a-97f7-478c-85f0-67d2f23661c7",
            "organisatie_rsin": "000000000",
            "variables_mapping": [
                # fmt: off
                {
                    "variable_key": "age",
                    "target_path": ["age"],
                },
                {
                    "variable_key": "lastname",
                    "target_path": ["name", "last.name"]
                },
                {
                    "variable_key": "now",
                    "target_path": ["submission_date"],
                },
                {
                    "variable_key": "pdf_url",
                    "target_path": ["submission_pdf_url"],
                },
                {
                    "variable_key": "csv_url",
                    "target_path": ["submission_csv_url"],
                },
                {
                    "variable_key": "payment_completed",
                    "target_path": ["submission_payment_completed"],
                },
                {
                    "variable_key": "payment_amount",
                    "target_path": ["submission_payment_amount"],
                },
                {
                    "variable_key": "payment_public_order_ids",
                    "target_path": ["submission_payment_public_ids"],
                },
                # fmt: on
            ],
            "geometry_variable_key": "location",
        }

        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        # Run the registration
        result = plugin.register_submission(submission, v2_options)

        registration_data = ObjectsAPIRegistrationData.objects.get(
            submission=submission
        )

        self.assertEqual(result["type"], v2_options["objecttype"])
        self.assertEqual(
            result["record"]["typeVersion"], v2_options["objecttype_version"]
        )
        submission_date = timezone.now().replace(second=0, microsecond=0).isoformat()
        self.assertEqual(
            result["record"]["data"],
            {
                "age": 20,
                "name": {
                    "last.name": "My last name",
                },
                "submission_pdf_url": registration_data.pdf_url,
                "submission_csv_url": registration_data.csv_url,
                "submission_payment_completed": False,
                "submission_payment_amount": "0",
                "submission_payment_public_ids": [],
                "submission_date": submission_date,
            },
        )
        self.assertEqual(
            result["record"]["geometry"],
            {
                "type": "Point",
                "coordinates": [52.36673378967122, 4.893164274470299],
            },
        )

    def test_submission_with_file_components(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "single_file",
                    "type": "file",
                },
                {
                    "key": "multiple_files",
                    "type": "file",
                    "multiple": True,
                },
            ],
            completed=True,
        )
        submission_step = submission.steps[0]
        SubmissionFileAttachmentFactory.create(
            submission_step=submission_step,
            file_name="attachment1.jpg",
            form_key="single_file",
        )
        SubmissionFileAttachmentFactory.create(
            submission_step=submission_step,
            file_name="attachment2_1.jpg",
            form_key="multiple_files",
        )

        v2_options: RegistrationOptionsV2 = {
            "version": 2,
            # See the docker compose fixtures for more info on these values:
            "objecttype": "http://objecttypes-web:8000/api/v2/objecttypes/527b8408-7421-4808-a744-43ccb7bdaaa2",
            "objecttype_version": 1,
            "upload_submission_csv": False,
            "informatieobjecttype_attachment": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/531f6c1a-97f7-478c-85f0-67d2f23661c7",
            "organisatie_rsin": "000000000",
            "variables_mapping": [
                # fmt: off
                {
                    "variable_key": "single_file",
                    "target_path": ["single_file"],
                },
                {
                    "variable_key": "multiple_files",
                    "target_path": ["multiple_files"]
                },
                # fmt: on
            ],
        }

        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        # Run the registration
        result = plugin.register_submission(submission, v2_options)

        self.assertEqual(result["type"], v2_options["objecttype"])
        self.assertEqual(
            result["record"]["typeVersion"], v2_options["objecttype_version"]
        )

        self.assertTrue(
            result["record"]["data"]["single_file"].startswith(
                "http://localhost:8003/documenten/api/v1/enkelvoudiginformatieobjecten/"
            )
        )

        self.assertIsInstance(result["record"]["data"]["multiple_files"], list)
        self.assertEqual(len(result["record"]["data"]["multiple_files"]), 1)

    def test_submission_with_map_component_inside_data(self):
        """
        A map component can be explicitly mapped to an attribute inside the 'data' key.

        This happens when more than one map component is in the form, and only one can
        be mapped to the ``record.geometry`` path, the rest must go in ``record.data.``.
        """
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "location",
                    "type": "map",
                    "label": "Map with point coordinate",
                },
            ],
            completed=True,
            submitted_data={
                "location": [52.36673378967122, 4.893164274470299],
            },
        )
        v2_options: RegistrationOptionsV2 = {
            "version": 2,
            # See the docker compose fixtures for more info on these values:
            "objecttype": "http://objecttypes-web:8000/api/v2/objecttypes/f1dde4fe-b7f9-46dc-84ae-429ae49e3705",
            "objecttype_version": 1,
            "upload_submission_csv": False,
            "informatieobjecttype_submission_report": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/7a474713-0833-402a-8441-e467c08ac55b",
            "informatieobjecttype_attachment": "",
            "organisatie_rsin": "000000000",
            "variables_mapping": [
                # fmt: off
                {
                    "variable_key": "location",
                    "target_path": ["pointCoordinates"],
                },
                # fmt: on
            ],
        }

        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        # Run the registration
        result = plugin.register_submission(submission, v2_options)

        record_data = result["record"]["data"]
        self.assertEqual(
            record_data["pointCoordinates"],
            {
                "type": "Point",
                "coordinates": [52.36673378967122, 4.893164274470299],
            },
        )

    @tag("gh-4141")
    def test_layout_components(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "fieldset",
                    "type": "fieldset",
                    "components": [{"key": "fieldset.textfield", "type": "textfield"}],
                },
            ],
            completed=True,
            submitted_data={
                "fieldset": {
                    "textfield": "some_string",
                },
            },
        )
        v2_options: RegistrationOptionsV2 = {
            "version": 2,
            # See the docker compose fixtures for more info on these values:
            "objecttype": "http://objecttypes-web:8000/api/v2/objecttypes/644ab597-e88c-43c0-8321-f12113510b0e",
            "objecttype_version": 1,
            "upload_submission_csv": False,
            "informatieobjecttype_submission_report": "",
            "informatieobjecttype_attachment": "",
            "organisatie_rsin": "000000000",
            "variables_mapping": [
                # fmt: off
                {
                    "variable_key": "fieldset.textfield",
                    "target_path": ["textfield"],
                },
                # fmt: on
            ],
        }

        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        # Run the registration
        result = plugin.register_submission(submission, v2_options)

        record_data = result["record"]["data"]
        self.assertEqual(record_data["textfield"], "some_string")
