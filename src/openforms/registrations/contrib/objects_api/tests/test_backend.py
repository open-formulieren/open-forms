from datetime import date

from django.test import TestCase

import requests_mock
from zds_client.oas import schema_fetcher
from zgw_consumers.test import generate_oas_component
from zgw_consumers.test.schema_mock import mock_service_oas_get

from openforms.registrations.constants import RegistrationAttribute
from openforms.registrations.contrib.objects_api.plugin import ObjectsAPIRegistration
from openforms.submissions.tests.factories import SubmissionFactory

from ...zgw_apis.tests.factories import ZgwConfigFactory
from ..models import ObjectsAPIConfig
from .factories import ObjectsAPIConfigFactory


@requests_mock.Mocker()
class ObjectsAPIBackendTests(TestCase):
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        ObjectsAPIConfigFactory.create(
            objects_service__api_root="https://objecten.nl/api/v1/",
            objecttype="https://objecttypen.nl/api/v1/objecttypes/1",
            objecttype_version=1,
            productaanvraag_type="terugbelnotitie",
        )
        ZgwConfigFactory.create(
            zrc_service__api_root="https://zaken.nl/api/v1/",
            drc_service__api_root="https://documenten.nl/api/v1/",
            ztc_service__api_root="https://catalogi.nl/api/v1/",
            informatieobjecttype="https://catalogi.nl/api/v1/informatieobjecttypen/1",
            organisatie_rsin="000000000",
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

        mock_service_oas_get(m, "https://objecten.nl/api/v1/", "objecten")
        mock_service_oas_get(m, "https://documenten.nl/api/v1/", "documenten")

        objects_form_options = dict(
            objecttype="https://objecttypen.nl/api/v1/objecttypes/2",
            objecttype_version=2,
            productaanvraag_type="testproduct",
            informatieobjecttype="https://catalogi.nl/api/v1/informatieobjecttypen/2",
            organisatie_rsin="123456782",
            vertrouwelijkheidaanduiding="geheim",
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
        expected_document_result = generate_oas_component(
            "documenten",
            "schemas/EnkelvoudigInformatieObject",
            url="https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
        )

        m.post(
            "https://objecten.nl/api/v1/objects",
            status_code=201,
            json=expected_result,
        )
        m.post(
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            status_code=201,
            json=expected_document_result,
        )

        plugin = ObjectsAPIRegistration("objects_api")
        result = plugin.register_submission(submission, objects_form_options)

        # Result is simply the created object
        self.assertEqual(result, expected_result)

        self.assertEqual(len(m.request_history), 4)

        (
            documenten_oas_get,
            document_create,
            objecten_oas_get,
            object_create,
        ) = m.request_history

        self.assertEqual(documenten_oas_get.method, "GET")
        self.assertEqual(
            documenten_oas_get.url,
            "https://documenten.nl/api/v1/schema/openapi.yaml?v=3",
        )

        document_create_body = document_create.json()
        self.assertEqual(document_create.method, "POST")
        self.assertEqual(
            document_create.url,
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
        )
        self.assertEqual(document_create_body["bronorganisatie"], "123456782")
        self.assertEqual(
            document_create_body["informatieobjecttype"],
            "https://catalogi.nl/api/v1/informatieobjecttypen/2",
        )
        self.assertEqual(
            document_create_body["vertrouwelijkheidaanduiding"],
            "geheim",
        )

        self.assertEqual(objecten_oas_get.method, "GET")
        self.assertEqual(
            objecten_oas_get.url, "https://objecten.nl/api/v1/schema/openapi.yaml?v=3"
        )

        expected_object_body = {
            "type": "https://objecttypen.nl/api/v1/objecttypes/2",
            "record": {
                "typeVersion": 2,
                "data": {
                    "data": submission.get_merged_data(),
                    "type": "testproduct",
                    "submission_id": str(submission.uuid),
                    "pdf_url": expected_document_result["url"],
                },
                "startAt": date.today().isoformat(),
            },
        }

        object_create_body = object_create.json()
        self.assertEqual(object_create.method, "POST")
        self.assertEqual(object_create.url, "https://objecten.nl/api/v1/objects")
        self.assertDictEqual(object_create_body, expected_object_body)

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

        mock_service_oas_get(m, "https://objecten.nl/api/v1/", "objecten")
        mock_service_oas_get(m, "https://documenten.nl/api/v1/", "documenten")

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
        expected_document_result = generate_oas_component(
            "documenten",
            "schemas/EnkelvoudigInformatieObject",
            url="https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
        )

        m.post(
            "https://objecten.nl/api/v1/objects",
            status_code=201,
            json=expected_result,
        )
        m.post(
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            status_code=201,
            json=expected_document_result,
        )

        plugin = ObjectsAPIRegistration("objects_api")
        result = plugin.register_submission(submission, {})

        # Result is simply the created object
        self.assertEqual(result, expected_result)

        self.assertEqual(len(m.request_history), 4)

        (
            documenten_oas_get,
            document_create,
            objecten_oas_get,
            object_create,
        ) = m.request_history

        self.assertEqual(documenten_oas_get.method, "GET")
        self.assertEqual(
            documenten_oas_get.url,
            "https://documenten.nl/api/v1/schema/openapi.yaml?v=3",
        )

        document_create_body = document_create.json()
        self.assertEqual(document_create.method, "POST")
        self.assertEqual(
            document_create.url,
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
        )
        self.assertEqual(document_create_body["bronorganisatie"], "000000000")
        self.assertEqual(
            document_create_body["informatieobjecttype"],
            "https://catalogi.nl/api/v1/informatieobjecttypen/1",
        )
        self.assertNotIn("vertrouwelijkheidaanduiding", document_create_body)

        self.assertEqual(objecten_oas_get.method, "GET")
        self.assertEqual(
            objecten_oas_get.url, "https://objecten.nl/api/v1/schema/openapi.yaml?v=3"
        )

        expected_object_body = {
            "type": "https://objecttypen.nl/api/v1/objecttypes/1",
            "record": {
                "typeVersion": 1,
                "data": {
                    "data": submission.get_merged_data(),
                    "type": "terugbelnotitie",
                    "submission_id": str(submission.uuid),
                    "pdf_url": expected_document_result["url"],
                },
                "startAt": date.today().isoformat(),
            },
        }

        object_create_body = object_create.json()
        self.assertEqual(object_create.method, "POST")
        self.assertEqual(object_create.url, "https://objecten.nl/api/v1/objects")
        self.assertDictEqual(object_create_body, expected_object_body)
