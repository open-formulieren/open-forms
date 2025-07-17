import textwrap
from datetime import date
from unittest.mock import patch

from django.test import TestCase, tag

import requests_mock
from glom import glom
from privates.test import temp_private_root
from zgw_consumers.test import generate_oas_component

from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory
from openforms.registrations.contrib.objects_api.models import ObjectsAPIConfig
from openforms.submissions.constants import PostSubmissionEvents, RegistrationStatuses
from openforms.submissions.tasks import pre_registration
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
)

from ....constants import RegistrationAttribute
from ....exceptions import RegistrationFailed
from ....tasks import register_submission
from .factories import ZGWApiGroupConfigFactory


@tag("gh-1183")
@temp_private_root()
class PartialRegistrationFailureTests(TestCase):
    """
    Test that partial results are stored and don't cause excessive registration calls.

    Issue #1183 -- case numbers are reserved to often, as a retry reserves a new one. It
    also happens that when certain other calls fail, a new Zaak is created which
    should not have been created again.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        zgw_api_group = ZGWApiGroupConfigFactory.create(
            zrc_service__api_root="https://zaken.nl/api/v1/",
            drc_service__api_root="https://documenten.nl/api/v1/",
            ztc_service__api_root="https://catalogus.nl/api/v1/",
        )

        # set up a simple form to track the partial result storing state
        cls.submission = SubmissionFactory.from_components(
            [
                {
                    "key": "voornaam",
                    "type": "textfield",
                },
                {
                    "key": "achternaam",
                    "type": "textfield",
                },
            ],
            form__name="my-form",
            form__registration_backend="zgw-create-zaak",
            form__registration_backend_options={
                "zgw_api_group": zgw_api_group.pk,
                "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
                "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
                "organisatie_rsin": "000000000",
                "vertrouwelijkheidaanduiding": "openbaar",
                "objects_api_group": None,
            },
            completed_not_preregistered=True,
            bsn="111222333",
            submitted_data={
                "voornaam": "Foo",
                "achternaam": "Bar",
            },
        )

    def setUp(self):
        super().setUp()

        self.requests_mock = requests_mock.Mocker()
        self.requests_mock.start()
        self.addCleanup(self.requests_mock.stop)
        self.addCleanup(self.submission.refresh_from_db)

    def test_failure_after_zaak_creation(self):
        self.requests_mock.post(
            "https://zaken.nl/api/v1/zaken",
            status_code=201,
            json=generate_oas_component(
                "zaken",
                "schemas/Zaak",
                url="https://zaken.nl/api/v1/zaken/1",
                zaaktype="https://catalogi.nl/api/v1/zaaktypen/1",
            ),
        )
        self.requests_mock.post(
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            status_code=500,
            json={"type": "Server error"},
        )

        with self.subTest("Initial document creation fails"):
            pre_registration(self.submission.id, PostSubmissionEvents.on_completion)
            register_submission(self.submission.id, PostSubmissionEvents.on_completion)

            self.submission.refresh_from_db()
            assert self.submission.registration_result
            self.assertEqual(
                self.submission.registration_status, RegistrationStatuses.failed
            )
            intermediate_results = self.submission.registration_result["intermediate"]
            self.assertEqual(
                intermediate_results["zaak"]["url"], "https://zaken.nl/api/v1/zaken/1"
            )
            self.assertIn("traceback", self.submission.registration_result)

        with self.subTest("New document creation attempt does not create zaak again"):
            with self.assertRaises(RegistrationFailed):
                register_submission(self.submission.id, PostSubmissionEvents.on_retry)

            self.submission.refresh_from_db()
            self.assertEqual(
                self.submission.registration_status, RegistrationStatuses.failed
            )
            intermediate_results = self.submission.registration_result["intermediate"]
            self.assertEqual(
                intermediate_results["zaak"]["url"], "https://zaken.nl/api/v1/zaken/1"
            )
            self.assertIn("traceback", self.submission.registration_result)

            history = self.requests_mock.request_history
            # 1. create zaak call
            # 2. create report document call (fails)
            # 3. create report document call (fails)
            self.assertEqual(len(history), 3)
            (
                create_zaak,
                create_pdf_document_attempt1,
                create_pdf_document_attempt2,
            ) = history

            self.assertEqual(create_zaak.url, "https://zaken.nl/api/v1/zaken")
            self.assertEqual(
                create_pdf_document_attempt1.url,
                "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            )
            self.assertEqual(
                create_pdf_document_attempt2.url,
                "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            )

    def test_attachment_document_create_fails(self):
        attachment = SubmissionFileAttachmentFactory.create(
            submission_step=self.submission.steps[0],
            file_name="attachment1.jpg",
            form_key="field1",
        )
        self.requests_mock.post(
            "https://zaken.nl/api/v1/zaken",
            status_code=201,
            json=generate_oas_component(
                "zaken",
                "schemas/Zaak",
                url="https://zaken.nl/api/v1/zaken/1",
                zaaktype="https://catalogi.nl/api/v1/zaaktypen/1",
            ),
        )
        self.requests_mock.post(
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            [
                # two calls on same URL: one PDF and one attachment
                {
                    "json": generate_oas_component(
                        "documenten",
                        "schemas/EnkelvoudigInformatieObject",
                        url="https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
                    ),
                    "status_code": 201,
                },
                {
                    "json": generate_oas_component(
                        "documenten",
                        "schemas/EnkelvoudigInformatieObject",
                        url="https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/2",
                    ),
                    "status_code": 201,
                },
            ],
        )
        self.requests_mock.post(
            "https://zaken.nl/api/v1/zaakinformatieobjecten",
            [
                # two calls on same URL: one PDF and one attachment
                {
                    "json": generate_oas_component(
                        "zaken",
                        "schemas/ZaakInformatieObject",
                        url="https://zaken.nl/api/v1/zaakinformatieobjecten/1",
                    ),
                    "status_code": 201,
                },
                {
                    "json": {"type": "Server error"},
                    "status_code": 500,
                },
                {
                    "json": {"type": "Server error"},
                    "status_code": 500,
                },
            ],
        )
        self.requests_mock.get(
            "https://catalogus.nl/api/v1/roltypen?zaaktype=https%3A%2F%2Fcatalogi.nl%2Fapi%2Fv1%2Fzaaktypen%2F1&omschrijvingGeneriek=initiator",
            status_code=200,
            json={
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    generate_oas_component(
                        "catalogi",
                        "schemas/RolType",
                        url="https://catalogus.nl/api/v1/roltypen/1",
                    )
                ],
            },
            headers={"API-version": "1.0.0"},
        )
        self.requests_mock.post(
            "https://zaken.nl/api/v1/rollen",
            status_code=201,
            json=generate_oas_component(
                "zaken", "schemas/Rol", url="https://zaken.nl/api/v1/rollen/1"
            ),
        )
        self.requests_mock.get(
            "https://catalogus.nl/api/v1/statustypen?zaaktype=https%3A%2F%2Fcatalogi.nl%2Fapi%2Fv1%2Fzaaktypen%2F1",
            status_code=200,
            json={
                "count": 2,
                "next": None,
                "previous": None,
                "results": [
                    generate_oas_component(
                        "catalogi",
                        "schemas/StatusType",
                        url="https://catalogus.nl/api/v1/statustypen/2",
                        volgnummer=2,
                    ),
                    generate_oas_component(
                        "catalogi",
                        "schemas/StatusType",
                        url="https://catalogus.nl/api/v1/statustypen/1",
                        volgnummer=1,
                    ),
                ],
            },
            headers={"API-version": "1.0.0"},
        )
        self.requests_mock.post(
            "https://zaken.nl/api/v1/statussen",
            status_code=201,
            json=generate_oas_component(
                "zaken", "schemas/Status", url="https://zaken.nl/api/v1/statussen/1"
            ),
        )

        with self.subTest("First try, attachment relation fails"):
            pre_registration(self.submission.id, PostSubmissionEvents.on_completion)
            register_submission(self.submission.id, PostSubmissionEvents.on_completion)

            self.submission.refresh_from_db()
            assert self.submission.registration_result
            self.assertEqual(
                self.submission.registration_status, RegistrationStatuses.failed
            )
            intermediate_results = self.submission.registration_result["intermediate"]

            zaak = glom(intermediate_results, "zaak")
            self.assertEqual(zaak["url"], "https://zaken.nl/api/v1/zaken/1")

            doc_report = glom(intermediate_results, "documents.report")
            self.assertEqual(
                doc_report["document"]["url"],
                "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
            )
            self.assertEqual(
                doc_report["relation"]["url"],
                "https://zaken.nl/api/v1/zaakinformatieobjecten/1",
            )

            doc_attachment = glom(intermediate_results, f"documents.{attachment.id}")
            self.assertEqual(
                doc_attachment["document"]["url"],
                "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/2",
            )

            initiator_rol = glom(intermediate_results, "initiator_rol")
            self.assertEqual(initiator_rol["url"], "https://zaken.nl/api/v1/rollen/1")

            status = glom(intermediate_results, "status")
            self.assertEqual(status["url"], "https://zaken.nl/api/v1/statussen/1")

            self.assertIn("traceback", self.submission.registration_result)

        with self.subTest("New attempt - ensure existing data is not created again"):
            with self.assertRaises(RegistrationFailed):
                register_submission(self.submission.id, PostSubmissionEvents.on_retry)

            self.submission.refresh_from_db()
            self.assertEqual(
                self.submission.registration_status, RegistrationStatuses.failed
            )
            intermediate_results = self.submission.registration_result["intermediate"]
            zaak = glom(intermediate_results, "zaak")
            self.assertEqual(zaak["url"], "https://zaken.nl/api/v1/zaken/1")

            doc_report = glom(intermediate_results, "documents.report")
            self.assertEqual(
                doc_report["document"]["url"],
                "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
            )
            self.assertEqual(
                doc_report["relation"]["url"],
                "https://zaken.nl/api/v1/zaakinformatieobjecten/1",
            )

            doc_attachment = glom(intermediate_results, f"documents.{attachment.id}")
            self.assertEqual(
                doc_attachment["document"]["url"],
                "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/2",
            )

            initiator_rol = glom(intermediate_results, "initiator_rol")
            self.assertEqual(initiator_rol["url"], "https://zaken.nl/api/v1/rollen/1")

            status = glom(intermediate_results, "status")
            self.assertEqual(status["url"], "https://zaken.nl/api/v1/statussen/1")

            self.assertIn("traceback", self.submission.registration_result)

            history = self.requests_mock.request_history
            # 1. create zaak call
            # 2. create report document call
            # 3. relate zaak & report document
            # 4. get roltypen
            # 5. create rol
            # 6. get statustypen
            # 7. create status
            # 8. create attachment document
            # 9. relate attachment document (fails)
            # 10. relate attachment document (still fails)
            self.assertEqual(len(history), 10)
            (
                create_zaak,
                create_pdf_document,
                relate_pdf_document,
                get_roltypen,
                create_rol,
                get_statustypen,
                create_status,
                create_attachment_document,
                relate_attachment_document_attempt1,
                relate_attachment_document_attempt2,
            ) = history

            self.assertEqual(create_zaak.url, "https://zaken.nl/api/v1/zaken")
            self.assertEqual(
                create_pdf_document.url,
                "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            )
            self.assertEqual(
                relate_pdf_document.url,
                "https://zaken.nl/api/v1/zaakinformatieobjecten",
            )
            self.assertEqual(create_rol.url, "https://zaken.nl/api/v1/rollen")
            self.assertEqual(create_status.url, "https://zaken.nl/api/v1/statussen")
            self.assertEqual(
                create_attachment_document.url,
                "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            )
            self.assertEqual(
                relate_attachment_document_attempt1.url,
                "https://zaken.nl/api/v1/zaakinformatieobjecten",
            )
            self.assertEqual(
                relate_attachment_document_attempt2.url,
                "https://zaken.nl/api/v1/zaakinformatieobjecten",
            )


@temp_private_root()
@requests_mock.Mocker()
class ObjectsAPIPartialRegistrationFailureTests(TestCase):
    @patch(
        "openforms.registrations.contrib.objects_api.models.ObjectsAPIConfig.get_solo"
    )
    def test_failure_after_object_creation(self, m, obj_api_config):
        config = ObjectsAPIConfig(
            content_json=textwrap.dedent(
                """
                {
                    "bron": {
                        "naam": "Open Formulieren",
                        "kenmerk": "{{ submission.kenmerk }}"
                    },
                    "type": "{{ productaanvraag_type }}",
                    "aanvraaggegevens": {% json_summary %},
                    "taal": "{{ submission.language_code  }}",
                    "betrokkenen": [
                        {
                            "inpBsn" : "{{ variables.auth_bsn }}",
                            "rolOmschrijvingGeneriek" : "initiator"
                        }
                    ],
                }"""
            ),
        )
        objects_api_group = ObjectsAPIGroupConfigFactory.create(
            objects_service__api_root="https://objecten.nl/api/v1/",
            organisatie_rsin="000000000",
        )

        zgw_api_group = ZGWApiGroupConfigFactory.create(
            zrc_service__api_root="https://zaken.nl/api/v1/",
            drc_service__api_root="https://documenten.nl/api/v1/",
            ztc_service__api_root="https://catalogus.nl/api/v1/",
        )
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "voorletters",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_voorletters,
                    },
                },
                {
                    "key": "voornaam",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_voornamen,
                    },
                },
                {
                    "key": "achternaam",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_geslachtsnaam,
                    },
                },
                {
                    "key": "tussenvoegsel",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_tussenvoegsel,
                    },
                },
                {
                    "key": "geboortedatum",
                    "type": "date",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_geboortedatum,
                    },
                },
                {
                    "key": "geslachtsaanduiding",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_geslachtsaanduiding,
                    },
                },
                {
                    "key": "postcode",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_postcode,
                    },
                },
                {
                    "key": "coordinaat",
                    "type": "map",
                    "registration": {
                        "attribute": RegistrationAttribute.locatie_coordinaat,
                    },
                },
            ],
            submitted_data={
                "voornaam": "Foo",
                "achternaam": "Bar",
                "tussenvoegsel": "de",
                "postcode": "1000 AA",
                "geboortedatum": "2000-12-31",
                "coordinaat": {
                    "type": "Point",
                    "coordinates": [4.893164274470299, 52.36673378967122],
                },
                "voorletters": "J.W.",
                "geslachtsaanduiding": "mannelijk",
            },
            bsn="111222333",
            language_code="en",
            completed_not_preregistered=True,
            form_definition_kwargs={"slug": "test1"},
            form__name="my-form",
            form__registration_backend="zgw-create-zaak",
            form__registration_backend_options={
                "zgw_api_group": zgw_api_group.pk,
                "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
                "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
                "organisatie_rsin": "000000000",
                "vertrouwelijkheidaanduiding": "openbaar",
                "objects_api_group": objects_api_group.pk,
                "objecttype": "https://objecttypen.nl/api/v1/objecttypes/2",
                "objecttype_version": 1,
            },
        )

        obj_api_config.return_value = config

        def get_create_json_for_object(req, ctx):
            request_body = req.json()
            return {
                "url": "https://objecten.nl/api/v1/objects/1",
                "uuid": "095be615-a8ad-4c33-8e9c-c7612fbf6c9f",
                "type": request_body["type"],
                "record": {
                    "index": 0,
                    **request_body["record"],
                    "endAt": None,
                    "registrationAt": date.today().isoformat(),
                    "correctionFor": 0,
                    "correctedBy": "",
                },
            }

        m.post(
            "https://zaken.nl/api/v1/zaken",
            status_code=201,
            json=generate_oas_component(
                "zaken",
                "schemas/Zaak",
                url="https://zaken.nl/api/v1/zaken/1",
                zaaktype="https://catalogi.nl/api/v1/zaaktypen/1",
            ),
        )
        m.post(
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            [
                # two calls on same URL: one PDF and one attachment
                {
                    "json": generate_oas_component(
                        "documenten",
                        "schemas/EnkelvoudigInformatieObject",
                        url="https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
                    ),
                    "status_code": 201,
                },
                {
                    "json": generate_oas_component(
                        "documenten",
                        "schemas/EnkelvoudigInformatieObject",
                        url="https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/2",
                    ),
                    "status_code": 201,
                },
            ],
        )
        m.post(
            "https://zaken.nl/api/v1/zaakinformatieobjecten",
            [
                # two calls on same URL: one PDF and one attachment
                {
                    "json": generate_oas_component(
                        "zaken",
                        "schemas/ZaakInformatieObject",
                        url="https://zaken.nl/api/v1/zaakinformatieobjecten/1",
                    ),
                    "status_code": 201,
                },
                {
                    "json": generate_oas_component(
                        "zaken",
                        "schemas/ZaakInformatieObject",
                        url="https://zaken.nl/api/v1/zaakinformatieobjecten/2",
                    ),
                    "status_code": 201,
                },
            ],
        )
        m.get(
            "https://catalogus.nl/api/v1/roltypen?zaaktype=https%3A%2F%2Fcatalogi.nl%2Fapi%2Fv1%2Fzaaktypen%2F1&omschrijvingGeneriek=initiator",
            status_code=200,
            json={
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    generate_oas_component(
                        "catalogi",
                        "schemas/RolType",
                        url="https://catalogus.nl/api/v1/roltypen/1",
                    )
                ],
            },
            headers={"API-version": "1.0.0"},
        )
        m.post(
            "https://zaken.nl/api/v1/rollen",
            status_code=201,
            json=generate_oas_component(
                "zaken", "schemas/Rol", url="https://zaken.nl/api/v1/rollen/1"
            ),
        )
        m.get(
            "https://catalogus.nl/api/v1/statustypen?zaaktype=https%3A%2F%2Fcatalogi.nl%2Fapi%2Fv1%2Fzaaktypen%2F1",
            status_code=200,
            json={
                "count": 2,
                "next": None,
                "previous": None,
                "results": [
                    generate_oas_component(
                        "catalogi",
                        "schemas/StatusType",
                        url="https://catalogus.nl/api/v1/statustypen/2",
                        volgnummer=2,
                    ),
                    generate_oas_component(
                        "catalogi",
                        "schemas/StatusType",
                        url="https://catalogus.nl/api/v1/statustypen/1",
                        volgnummer=1,
                    ),
                ],
            },
            headers={"API-version": "1.0.0"},
        )
        m.post(
            "https://zaken.nl/api/v1/statussen",
            status_code=201,
            json=generate_oas_component(
                "zaken", "schemas/Status", url="https://zaken.nl/api/v1/statussen/1"
            ),
        )
        m.post(
            "https://objecten.nl/api/v1/objects",
            status_code=201,
            json=get_create_json_for_object,
        )
        m.post(
            "https://zaken.nl/api/v1/zaakobjecten",
            status_code=500,
            json={"type": "Server error"},
        )

        pre_registration(submission.id, PostSubmissionEvents.on_completion)
        register_submission(submission.id, PostSubmissionEvents.on_completion)

        submission.refresh_from_db()
        assert submission.registration_result

        self.assertEqual(submission.registration_status, RegistrationStatuses.failed)

        intermediate_results = submission.registration_result["intermediate"]

        object = glom(intermediate_results, "objects_api_object")

        self.assertEqual(object["url"], "https://objecten.nl/api/v1/objects/1")
        self.assertIn("traceback", submission.registration_result)


@requests_mock.Mocker()
class EigenschappenPartialRegistrationFailureTests(TestCase):
    def test_failure_after_eigenschappen_retrieval(self, m):
        zgw_api_group = ZGWApiGroupConfigFactory.create(
            zrc_service__api_root="https://zaken.nl/api/v1/",
            drc_service__api_root="https://documenten.nl/api/v1/",
            ztc_service__api_root="https://catalogus.nl/api/v1/",
        )
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "textField1",
                    "type": "textfield1",
                },
            ],
            submitted_data={"textField1": "some data"},
            language_code="en",
            completed_not_preregistered=True,
            form_definition_kwargs={"slug": "test-eigenschappen-failure"},
            form__name="my-form",
            form__registration_backend="zgw-create-zaak",
            form__registration_backend_options={
                "zgw_api_group": zgw_api_group.pk,
                "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
                "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
                "organisatie_rsin": "000000000",
                "vertrouwelijkheidaanduiding": "openbaar",
                "objects_api_group": None,
                "property_mappings": [
                    {"component_key": "textField1", "eigenschap": "a property name"}
                ],
            },
        )

        m.post(
            "https://zaken.nl/api/v1/zaken",
            status_code=201,
            json=generate_oas_component(
                "zaken",
                "schemas/Zaak",
                url="https://zaken.nl/api/v1/zaken/1",
                zaaktype="https://catalogi.nl/api/v1/zaaktypen/1",
            ),
        )
        m.post(
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            [
                # two calls on same URL: one PDF and one attachment
                {
                    "json": generate_oas_component(
                        "documenten",
                        "schemas/EnkelvoudigInformatieObject",
                        url="https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
                    ),
                    "status_code": 201,
                },
                {
                    "json": generate_oas_component(
                        "documenten",
                        "schemas/EnkelvoudigInformatieObject",
                        url="https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/2",
                    ),
                    "status_code": 201,
                },
            ],
        )
        m.post(
            "https://zaken.nl/api/v1/zaakinformatieobjecten",
            [
                # two calls on same URL: one PDF and one attachment
                {
                    "json": generate_oas_component(
                        "zaken",
                        "schemas/ZaakInformatieObject",
                        url="https://zaken.nl/api/v1/zaakinformatieobjecten/1",
                    ),
                    "status_code": 201,
                },
                {
                    "json": generate_oas_component(
                        "zaken",
                        "schemas/ZaakInformatieObject",
                        url="https://zaken.nl/api/v1/zaakinformatieobjecten/2",
                    ),
                    "status_code": 201,
                },
            ],
        )
        m.get(
            "https://catalogus.nl/api/v1/roltypen?zaaktype=https%3A%2F%2Fcatalogi.nl%2Fapi%2Fv1%2Fzaaktypen%2F1&omschrijvingGeneriek=initiator",
            status_code=200,
            json={
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    generate_oas_component(
                        "catalogi",
                        "schemas/RolType",
                        url="https://catalogus.nl/api/v1/roltypen/1",
                    )
                ],
            },
            headers={"API-version": "1.0.0"},
        )
        m.post(
            "https://zaken.nl/api/v1/rollen",
            status_code=201,
            json=generate_oas_component(
                "zaken", "schemas/Rol", url="https://zaken.nl/api/v1/rollen/1"
            ),
        )
        m.get(
            "https://catalogus.nl/api/v1/statustypen?zaaktype=https%3A%2F%2Fcatalogi.nl%2Fapi%2Fv1%2Fzaaktypen%2F1",
            status_code=200,
            json={
                "count": 2,
                "next": None,
                "previous": None,
                "results": [
                    generate_oas_component(
                        "catalogi",
                        "schemas/StatusType",
                        url="https://catalogus.nl/api/v1/statustypen/2",
                        volgnummer=2,
                    ),
                    generate_oas_component(
                        "catalogi",
                        "schemas/StatusType",
                        url="https://catalogus.nl/api/v1/statustypen/1",
                        volgnummer=1,
                    ),
                ],
            },
            headers={"API-version": "1.0.0"},
        )
        m.post(
            "https://zaken.nl/api/v1/statussen",
            status_code=201,
            json=generate_oas_component(
                "zaken", "schemas/Status", url="https://zaken.nl/api/v1/statussen/1"
            ),
        )
        m.get(
            "https://catalogus.nl/api/v1/eigenschappen?zaaktype=https%3A%2F%2Fcatalogi.nl%2Fapi%2Fv1%2Fzaaktypen%2F1",
            status_code=200,
            json={
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    generate_oas_component(
                        "catalogi",
                        "schemas/Eigenschap",
                        url="https://test.openzaak.nl/catalogi/api/v1/eigenschappen/1",
                        naam="a property name",
                        definitie="a definition",
                        specificatie={
                            "groep": "",
                            "formaat": "tekst",
                            "lengte": "10",
                            "kardinaliteit": "1",
                            "waardenverzameling": [],
                        },
                        toelichting="",
                        zaaktype="https://zaken.nl/api/v1/zaaktypen/1",
                    ),
                ],
            },
            headers={"API-version": "1.0.0"},
        )
        m.post(
            "https://zaken.nl/api/v1/zaken/1/zaakeigenschappen",
            status_code=500,
            json={"type": "Server error"},
        )

        pre_registration(submission.id, PostSubmissionEvents.on_completion)
        register_submission(submission.id, PostSubmissionEvents.on_completion)

        submission.refresh_from_db()
        assert submission.registration_result

        self.assertEqual(submission.registration_status, RegistrationStatuses.failed)

        intermediate_results = submission.registration_result["intermediate"]

        zaakeigenschap = glom(intermediate_results, "zaaktype_eigenschappen")

        self.assertEqual(
            zaakeigenschap[0]["url"],
            "https://test.openzaak.nl/catalogi/api/v1/eigenschappen/1",
        )
        self.assertIn("traceback", submission.registration_result)
