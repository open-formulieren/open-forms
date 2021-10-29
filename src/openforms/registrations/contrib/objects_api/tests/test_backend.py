from datetime import date

from django.test import TestCase

import requests_mock
from zds_client.oas import schema_fetcher
from zgw_consumers.test import generate_oas_component
from zgw_consumers.test.schema_mock import mock_service_oas_get

from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
)

from ....constants import RegistrationAttribute
from ....service import NoSubmissionReference, extract_submission_reference
from ..plugin import ObjectsAPIRegistration
from .factories import ObjectsAPIConfigFactory


@requests_mock.Mocker()
class ObjectsAPIBackendTests(TestCase):
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        ObjectsAPIConfigFactory.create(
            objects_service__api_root="https://objecten.nl/api/v1/",
            drc_service__api_root="https://documenten.nl/api/v1/",
            objecttype="https://objecttypen.nl/api/v1/objecttypes/1",
            objecttype_version=1,
            productaanvraag_type="terugbelnotitie",
            informatieobjecttype_submission_report="https://catalogi.nl/api/v1/informatieobjecttypen/1",
            informatieobjecttype_submission_csv="https://catalogi.nl/api/v1/informatieobjecttypen/4",
            informatieobjecttype_attachment="https://catalogi.nl/api/v1/informatieobjecttypen/3",
            organisatie_rsin="000000000",
        )

    def setUp(self):
        super().setUp()

        # ensure the schema cache is cleared before and after each test
        schema_fetcher.cache.clear()
        self.addCleanup(schema_fetcher.cache.clear)

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
                {
                    "key": "coordinaat",
                    "registration": {
                        "attribute": RegistrationAttribute.locatie_coordinaat,
                    },
                },
            ],
            submitted_data={
                "voornaam": "Foo",
                "achternaam": "Bar",
                "tussenvoegsel": "de",
                "geboortedatum": "2000-12-31",
                "coordinaat": [52.36673378967122, 4.893164274470299],
            },
        )

        mock_service_oas_get(m, "https://objecten.nl/api/v1/", "objecten")
        mock_service_oas_get(m, "https://documenten.nl/api/v1/", "documenten")

        objects_form_options = dict(
            objecttype="https://objecttypen.nl/api/v1/objecttypes/2",
            objecttype_version=2,
            productaanvraag_type="testproduct",
            informatieobjecttype_submission_report="https://catalogi.nl/api/v1/informatieobjecttypen/2",
            upload_submission_csv=True,
            informatieobjecttype_submission_csv="https://catalogi.nl/api/v1/informatieobjecttypen/5",
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
                    "attachments": [],
                    "pdf_url": "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [52.36673378967122, 4.893164274470299],
                },
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

        def match_csv(request):
            if "csv" in request.json()["bestandsnaam"]:
                return True
            return False

        expected_csv_document_result = generate_oas_component(
            "documenten",
            "schemas/EnkelvoudigInformatieObject",
            url="https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/2",
        )

        m.post(
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            status_code=201,
            json=expected_csv_document_result,
            additional_matcher=match_csv,
        )

        plugin = ObjectsAPIRegistration("objects_api")
        result = plugin.register_submission(submission, objects_form_options)

        # Result is simply the created object
        self.assertEqual(result, expected_result)

        self.assertEqual(len(m.request_history), 5)

        (
            documenten_oas_get,
            document_create,
            csv_document_create,
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

        csv_document_create_body = csv_document_create.json()
        self.assertEqual(csv_document_create.method, "POST")
        self.assertEqual(
            csv_document_create.url,
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
        )
        # Overridden informatieobjecttype used
        self.assertEqual(
            csv_document_create_body["informatieobjecttype"],
            "https://catalogi.nl/api/v1/informatieobjecttypen/5",
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
                    "attachments": [],
                    "pdf_url": expected_document_result["url"],
                    "csv_url": expected_csv_document_result["url"],
                },
                "startAt": date.today().isoformat(),
                "geometry": {
                    "type": "Point",
                    "coordinates": [52.36673378967122, 4.893164274470299],
                },
            },
        }

        object_create_body = object_create.json()
        self.assertEqual(object_create.method, "POST")
        self.assertEqual(object_create.url, "https://objecten.nl/api/v1/objects")
        self.assertDictEqual(object_create_body, expected_object_body)

    def test_submission_with_objects_api_backend_override_defaults_upload_csv_default_type(
        self, m
    ):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "voornaam",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_voornamen,
                    },
                },
            ],
            submitted_data={"voornaam": "Foo"},
        )

        mock_service_oas_get(m, "https://objecten.nl/api/v1/", "objecten")
        mock_service_oas_get(m, "https://documenten.nl/api/v1/", "documenten")

        objects_form_options = dict(
            objecttype="https://objecttypen.nl/api/v1/objecttypes/2",
            objecttype_version=2,
            productaanvraag_type="testproduct",
            informatieobjecttype_submission_report="https://catalogi.nl/api/v1/informatieobjecttypen/2",
            upload_submission_csv=True,
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
                    "attachments": [],
                    "pdf_url": "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
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

        def match_csv(request):
            if "csv" in request.json()["bestandsnaam"]:
                return True
            return False

        expected_csv_document_result = generate_oas_component(
            "documenten",
            "schemas/EnkelvoudigInformatieObject",
            url="https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/2",
        )

        m.post(
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            status_code=201,
            json=expected_csv_document_result,
            additional_matcher=match_csv,
        )

        plugin = ObjectsAPIRegistration("objects_api")
        result = plugin.register_submission(submission, objects_form_options)

        # Result is simply the created object
        self.assertEqual(result, expected_result)

        self.assertEqual(len(m.request_history), 5)

        (
            documenten_oas_get,
            document_create,
            csv_document_create,
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

        csv_document_create_body = csv_document_create.json()
        self.assertEqual(csv_document_create.method, "POST")
        self.assertEqual(
            csv_document_create.url,
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
        )
        # Default informatieobjecttype used
        self.assertEqual(
            csv_document_create_body["informatieobjecttype"],
            "https://catalogi.nl/api/v1/informatieobjecttypen/4",
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
                    "attachments": [],
                    "pdf_url": expected_document_result["url"],
                    "csv_url": expected_csv_document_result["url"],
                },
                "startAt": date.today().isoformat(),
            },
        }

        object_create_body = object_create.json()
        self.assertEqual(object_create.method, "POST")
        self.assertEqual(object_create.url, "https://objecten.nl/api/v1/objects")
        self.assertDictEqual(object_create_body, expected_object_body)

    def test_submission_with_objects_api_backend_override_defaults_do_not_upload_csv(
        self, m
    ):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "voornaam",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_voornamen,
                    },
                },
            ],
            submitted_data={"voornaam": "Foo"},
        )

        mock_service_oas_get(m, "https://objecten.nl/api/v1/", "objecten")
        mock_service_oas_get(m, "https://documenten.nl/api/v1/", "documenten")

        objects_form_options = dict(
            objecttype="https://objecttypen.nl/api/v1/objecttypes/2",
            objecttype_version=2,
            productaanvraag_type="testproduct",
            informatieobjecttype_submission_report="https://catalogi.nl/api/v1/informatieobjecttypen/2",
            upload_submission_csv=False,
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
                    "attachments": [],
                    "pdf_url": "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
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
                    "attachments": [],
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
                    "attachments": [],
                    "pdf_url": "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
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
                    "attachments": [],
                    "pdf_url": expected_document_result["url"],
                },
                "startAt": date.today().isoformat(),
            },
        }

        object_create_body = object_create.json()
        self.assertEqual(object_create.method, "POST")
        self.assertEqual(object_create.url, "https://objecten.nl/api/v1/objects")
        self.assertDictEqual(object_create_body, expected_object_body)

    def test_submission_with_objects_api_backend_bsn(self, m):
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
                    "attachments": [],
                    "bsn": "111222333",
                    "pdf_url": "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
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
                    "attachments": [],
                    "bsn": "111222333",
                    "pdf_url": expected_document_result["url"],
                },
                "startAt": date.today().isoformat(),
            },
        }

        object_create_body = object_create.json()
        self.assertEqual(object_create.method, "POST")
        self.assertEqual(object_create.url, "https://objecten.nl/api/v1/objects")
        self.assertDictEqual(object_create_body, expected_object_body)

    def test_submission_with_objects_api_backend_kvk(self, m):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "voornaam",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_voornamen,
                    },
                },
            ],
            submitted_data={"voornaam": "Foo"},
            kvk="11122233",
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
                    "attachments": [],
                    "kvk": "11122233",
                    "pdf_url": "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
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
                    "attachments": [],
                    "kvk": "11122233",
                    "pdf_url": expected_document_result["url"],
                },
                "startAt": date.today().isoformat(),
            },
        }

        object_create_body = object_create.json()
        self.assertEqual(object_create.method, "POST")
        self.assertEqual(object_create.url, "https://objecten.nl/api/v1/objects")
        self.assertDictEqual(object_create_body, expected_object_body)

    def test_submission_with_objects_api_backend_attachments(self, m):
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
        )

        attachment1 = SubmissionFileAttachmentFactory.create(
            submission_step__submission=submission, file_name="attachment1.jpg"
        )
        attachment2 = SubmissionFileAttachmentFactory.create(
            submission_step__submission=submission, file_name="attachment2.jpg"
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
                    "attachments": [
                        "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/2",
                        "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/3",
                    ],
                    "pdf_url": "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
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

        def match_pdf_document(request):
            if request.json()["bestandsnaam"].endswith(".pdf"):
                return True
            return False

        expected_attachment_result1 = generate_oas_component(
            "documenten",
            "schemas/EnkelvoudigInformatieObject",
            url="https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/2",
        )

        def match_attachment1(request):
            if request.json()["bestandsnaam"] == "attachment1.jpg":
                return True
            return False

        expected_attachment_result2 = generate_oas_component(
            "documenten",
            "schemas/EnkelvoudigInformatieObject",
            url="https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/3",
        )

        def match_attachment2(request):
            if request.json()["bestandsnaam"] == "attachment2.jpg":
                return True
            return False

        m.post(
            "https://objecten.nl/api/v1/objects",
            status_code=201,
            json=expected_result,
        )

        m.post(
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            status_code=201,
            json=expected_document_result,
            additional_matcher=match_pdf_document,
        )
        m.post(
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            status_code=201,
            json=expected_attachment_result1,
            additional_matcher=match_attachment1,
        )
        m.post(
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            status_code=201,
            json=expected_attachment_result2,
            additional_matcher=match_attachment2,
        )

        plugin = ObjectsAPIRegistration("objects_api")
        result = plugin.register_submission(submission, {})

        # Result is simply the created object
        self.assertEqual(result, expected_result)

        self.assertEqual(len(m.request_history), 6)

        (
            documenten_oas_get,
            document_create_pdf,
            document_create_attachment1,
            document_create_attachment2,
            objecten_oas_get,
            object_create,
        ) = m.request_history

        self.assertEqual(documenten_oas_get.method, "GET")
        self.assertEqual(
            documenten_oas_get.url,
            "https://documenten.nl/api/v1/schema/openapi.yaml?v=3",
        )

        document_create_pdf_body = document_create_pdf.json()
        self.assertEqual(document_create_pdf.method, "POST")
        self.assertEqual(
            document_create_pdf.url,
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
        )
        self.assertEqual(document_create_pdf_body["bronorganisatie"], "000000000")
        self.assertEqual(
            document_create_pdf_body["informatieobjecttype"],
            "https://catalogi.nl/api/v1/informatieobjecttypen/1",
        )
        self.assertNotIn("vertrouwelijkheidaanduiding", document_create_pdf_body)

        self.assertEqual(objecten_oas_get.method, "GET")
        self.assertEqual(
            objecten_oas_get.url, "https://objecten.nl/api/v1/schema/openapi.yaml?v=3"
        )

        # Verify attachments
        document_create_attachment1_body = document_create_attachment1.json()
        self.assertEqual(document_create_attachment1.method, "POST")
        self.assertEqual(
            document_create_attachment1.url,
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
        )
        self.assertEqual(
            document_create_attachment1_body["bronorganisatie"], "000000000"
        )
        self.assertEqual(
            document_create_attachment1_body["informatieobjecttype"],
            "https://catalogi.nl/api/v1/informatieobjecttypen/3",
        )
        self.assertNotIn(
            "vertrouwelijkheidaanduiding", document_create_attachment1_body
        )

        document_create_attachment2_body = document_create_attachment2.json()
        self.assertEqual(document_create_attachment2.method, "POST")
        self.assertEqual(
            document_create_attachment2.url,
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
        )
        self.assertEqual(
            document_create_attachment2_body["bronorganisatie"], "000000000"
        )
        self.assertEqual(
            document_create_attachment2_body["informatieobjecttype"],
            "https://catalogi.nl/api/v1/informatieobjecttypen/3",
        )
        self.assertNotIn(
            "vertrouwelijkheidaanduiding", document_create_attachment2_body
        )

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
                    "attachments": [
                        "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/2",
                        "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/3",
                    ],
                    "pdf_url": expected_document_result["url"],
                },
                "startAt": date.today().isoformat(),
            },
        }

        object_create_body = object_create.json()
        self.assertEqual(object_create.method, "POST")
        self.assertEqual(object_create.url, "https://objecten.nl/api/v1/objects")
        self.assertDictEqual(object_create_body, expected_object_body)

    def test_no_reference_can_be_extracted(self, m):
        submission = SubmissionFactory.create(
            form__registration_backend="objects_api",
            completed=True,
            registration_success=True,
            registration_result="irrelevant",
        )

        with self.assertRaises(NoSubmissionReference):
            extract_submission_reference(submission)
