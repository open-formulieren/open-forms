from datetime import date

from django.test import TestCase

import requests_mock
from zds_client.oas import schema_fetcher
from zgw_consumers.test.schema_mock import mock_service_oas_get

from openforms.registrations.constants import RegistrationAttribute
from openforms.registrations.contrib.objects_api.plugin import ObjectsAPIRegistration
from openforms.submissions.tests.factories import SubmissionFactory

from ..models import ObjectsAPIConfig
from .factories import ObjectsAPIConfigFactory


@requests_mock.Mocker()
class ObjectsAPIBackendTests(TestCase):
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        ObjectsAPIConfigFactory.create(
            objects_service__api_root="https://objecten.nl/api/v2/",
            objecttype="https://objecttypen.nl/api/v1/objecttypes/1",
            objecttype_version=1,
            productaanvraag_type="terugbelnotitie",
        )

    def tearDown(self):
        super().tearDown()

        # Reset the schema fetcher cache, to verify that
        # the OAS is being retrieved on every submission
        schema_fetcher.cache = {}

    def test_submission_with_objects_api_backend_override_defaults(self, m):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "voornaam",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_voornamen,
                    },
                },
                {
                    "key": "achternaam",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_geslachtsnaam,
                    },
                },
                {
                    "key": "tussenvoegsel",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_tussenvoegsel,
                    },
                },
                {
                    "key": "geboortedatum",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_geboortedatum,
                    },
                },
            ],
            submitted_data={
                "voornaam": "Foo",
                "achternaam": "Bar",
                "tussenvoegsel": "de",
                "geboortedatum": "2000-12-31",
            },
            bsn="111222333",
        )

        mock_service_oas_get(m, "https://objecten.nl/api/v2/", "objecten")

        objects_form_options = dict(
            objecttype="https://objecttypen.nl/api/v1/objecttypes/2",
            objecttype_version=2,
            productaanvraag_type="testproduct",
        )

        expected_result = {
            "url": "https://objecten.nl/api/v1/objects/1",
            "uuid": "095be615-a8ad-4c33-8e9c-c7612fbf6c9f",
            "type": objects_form_options["objecttype"],
            "record": {
                "index": 0,
                "typeVersion": objects_form_options["objecttype_version"],
                "data": {
                    "data": submission.get_merged_data(),
                    "type": objects_form_options["productaanvraag_type"],
                    "submission_id": str(submission.uuid),
                },
                "geometry": {"type": "Point", "coordinates": [0, 0]},
                "startAt": date.today().isoformat(),
                "endAt": date.today().isoformat(),
                "registrationAt": date.today().isoformat(),
                "correctionFor": 0,
                "correctedBy": "",
            },
        }

        m.post(
            # FIXME zgw-consumers seems to duplicate /api/v2
            "https://objecten.nl/api/v2/api/v2/objects",
            status_code=201,
            json=expected_result,
        )

        plugin = ObjectsAPIRegistration("objects_api")
        result = plugin.register_submission(submission, objects_form_options)

        # Result is simply the created object
        self.assertEqual(result, expected_result)

        self.assertEqual(len(m.request_history), 2)

        oas_get = m.request_history[0]
        self.assertEqual(oas_get.method, "GET")
        self.assertEqual(
            oas_get.url, "https://objecten.nl/api/v2/schema/openapi.yaml?v=3"
        )

        expected_body = {
            "type": "https://objecttypen.nl/api/v1/objecttypes/2",
            "record": {
                "typeVersion": 2,
                "data": {
                    "data": submission.get_merged_data(),
                    "type": "testproduct",
                    "submission_id": str(submission.uuid),
                },
                "startAt": date.today().isoformat(),
            },
        }

        create_object = m.request_history[-1]
        create_object_body = create_object.json()
        self.assertEqual(create_object.method, "POST")
        self.assertEqual(create_object.url, "https://objecten.nl/api/v2/api/v2/objects")
        self.assertDictEqual(create_object_body, expected_body)

    def test_submission_with_objects_api_backend_use_config_defaults(self, m):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "voornaam",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_voornamen,
                    },
                },
                {
                    "key": "achternaam",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_geslachtsnaam,
                    },
                },
                {
                    "key": "tussenvoegsel",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_tussenvoegsel,
                    },
                },
                {
                    "key": "geboortedatum",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_geboortedatum,
                    },
                },
            ],
            submitted_data={
                "voornaam": "Foo",
                "achternaam": "Bar",
                "tussenvoegsel": "de",
                "geboortedatum": "2000-12-31",
            },
            bsn="111222333",
        )

        mock_service_oas_get(m, "https://objecten.nl/api/v2/", "objecten")

        expected_result = {
            "url": "https://objecten.nl/api/v1/objects/1",
            "uuid": "095be615-a8ad-4c33-8e9c-c7612fbf6c9f",
            "type": "https://objecttypen.nl/api/v1/objecttypes/1",
            "record": {
                "index": 0,
                "typeVersion": 1,
                "data": {
                    "data": submission.get_merged_data(),
                    "type": "terugbelnotitie",
                    "submission_id": str(submission.uuid),
                },
                "geometry": {"type": "Point", "coordinates": [0, 0]},
                "startAt": date.today().isoformat(),
                "endAt": date.today().isoformat(),
                "registrationAt": date.today().isoformat(),
                "correctionFor": 0,
                "correctedBy": "",
            },
        }

        m.post(
            # FIXME zgw-consumers seems to duplicate /api/v2
            "https://objecten.nl/api/v2/api/v2/objects",
            status_code=201,
            json=expected_result,
        )

        plugin = ObjectsAPIRegistration("objects_api")
        result = plugin.register_submission(submission, {})

        # Result is simply the created object
        self.assertEqual(result, expected_result)

        self.assertEqual(len(m.request_history), 2)

        oas_get = m.request_history[0]
        self.assertEqual(oas_get.method, "GET")
        self.assertEqual(
            oas_get.url, "https://objecten.nl/api/v2/schema/openapi.yaml?v=3"
        )

        expected_body = {
            "type": "https://objecttypen.nl/api/v1/objecttypes/1",
            "record": {
                "typeVersion": 1,
                "data": {
                    "data": submission.get_merged_data(),
                    "type": "terugbelnotitie",
                    "submission_id": str(submission.uuid),
                },
                "startAt": date.today().isoformat(),
            },
        }

        create_object = m.request_history[-1]
        create_object_body = create_object.json()
        self.assertEqual(create_object.method, "POST")
        self.assertEqual(create_object.url, "https://objecten.nl/api/v2/api/v2/objects")
        self.assertDictEqual(create_object_body, expected_body)
