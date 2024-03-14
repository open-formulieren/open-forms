import textwrap
from datetime import date
from unittest.mock import patch

from django.test import TestCase, override_settings

import requests_mock
from zgw_consumers.constants import APITypes
from zgw_consumers.test import generate_oas_component
from zgw_consumers.test.factories import ServiceFactory

from openforms.payments.constants import PaymentStatus
from openforms.payments.tests.factories import SubmissionPaymentFactory
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
)

from ....constants import RegistrationAttribute
from ..models import ObjectsAPIConfig
from ..plugin import PLUGIN_IDENTIFIER, ObjectsAPIRegistration


def get_create_json(req, ctx):
    request_body = req.json()
    return {
        "url": "https://objecten.nl/api/v1/objects/1",
        "uuid": "095be615-a8ad-4c33-8e9c-c7612fbf6c9f",
        "type": request_body["type"],
        "record": {
            "index": 0,
            **request_body["record"],  # typeVersion, data and startAt keys
            "endAt": None,  # see https://github.com/maykinmedia/objects-api/issues/349
            "registrationAt": date.today().isoformat(),
            "correctionFor": 0,
            "correctedBy": "",
        },
    }


@requests_mock.Mocker()
class ObjectsAPIBackendV1Tests(TestCase):
    maxDiff = None

    def setUp(self):
        super().setUp()

        config = ObjectsAPIConfig(
            objects_service=ServiceFactory.build(
                api_root="https://objecten.nl/api/v1/",
                api_type=APITypes.orc,
            ),
            drc_service=ServiceFactory.build(
                api_root="https://documenten.nl/api/v1/",
                api_type=APITypes.drc,
            ),
            objecttype="https://objecttypen.nl/api/v1/objecttypes/1",
            objecttype_version=1,
            productaanvraag_type="terugbelnotitie",
            informatieobjecttype_submission_report="https://catalogi.nl/api/v1/informatieobjecttypen/1",
            informatieobjecttype_submission_csv="https://catalogi.nl/api/v1/informatieobjecttypen/4",
            informatieobjecttype_attachment="https://catalogi.nl/api/v1/informatieobjecttypen/3",
            organisatie_rsin="000000000",
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
                    "pdf": "{{ submission.pdf_url }}",
                    "csv": "{{ submission.csv_url }}",
                    "bijlagen": {% uploaded_attachment_urls %},
                    "payment": {
                        "completed": {% if payment.completed %}true{% else %}false{% endif %},
                        "amount": {{ payment.amount }},
                        "public_order_ids": {{ payment.public_order_ids }}
                    }
                }"""
            ),
        )

        config_patcher = patch(
            "openforms.registrations.contrib.objects_api.models.ObjectsAPIConfig.get_solo",
            return_value=config,
        )
        self.mock_get_config = config_patcher.start()
        self.addCleanup(config_patcher.stop)

    def test_submission_with_objects_api_backend_override_defaults(self, m):
        submission = SubmissionFactory.from_components(
            [
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
                "geboortedatum": "2000-12-31",
                "coordinaat": [52.36673378967122, 4.893164274470299],
            },
            language_code="en",
        )
        submission_step = submission.steps[0]
        assert submission_step.form_step
        step_slug = submission_step.form_step.slug

        objects_form_options = dict(
            objecttype="https://objecttypen.nl/api/v1/objecttypes/2",
            objecttype_version=2,
            productaanvraag_type="testproduct",
            informatieobjecttype_submission_report="https://catalogi.nl/api/v1/informatieobjecttypen/2",
            upload_submission_csv=True,
            informatieobjecttype_submission_csv="https://catalogi.nl/api/v1/informatieobjecttypen/5",
            organisatie_rsin="123456782",
            zaak_vertrouwelijkheidaanduiding="geheim",
            doc_vertrouwelijkheidaanduiding="geheim",
        )

        # Set up API mocks
        expected_document_result = generate_oas_component(
            "documenten",
            "schemas/EnkelvoudigInformatieObject",
            url="https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
        )
        expected_csv_document_result = generate_oas_component(
            "documenten",
            "schemas/EnkelvoudigInformatieObject",
            url="https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/2",
        )
        m.post(
            "https://objecten.nl/api/v1/objects",
            status_code=201,
            json=get_create_json,
        )
        m.post(
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            status_code=201,
            json=expected_document_result,
        )
        m.post(
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            status_code=201,
            json=expected_csv_document_result,
            additional_matcher=lambda req: "csv" in req.json()["bestandsnaam"],
        )
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        # Run the registration
        result = plugin.register_submission(submission, objects_form_options)

        # check the requests made
        self.assertEqual(len(m.request_history), 3)
        document_create, csv_document_create, object_create = m.request_history

        with self.subTest("object create call and registration result"):
            submitted_object_data = object_create.json()
            expected_object_body = {
                "type": "https://objecttypen.nl/api/v1/objecttypes/2",
                "record": {
                    "typeVersion": 2,
                    "data": {
                        "bron": {
                            "naam": "Open Formulieren",
                            "kenmerk": str(submission.uuid),
                        },
                        "type": "testproduct",
                        "aanvraaggegevens": {
                            step_slug: {
                                "voornaam": "Foo",
                                "achternaam": "Bar",
                                "tussenvoegsel": "de",
                                "geboortedatum": "2000-12-31",
                                "coordinaat": [52.36673378967122, 4.893164274470299],
                            }
                        },
                        "taal": "en",
                        "betrokkenen": [
                            {"inpBsn": "", "rolOmschrijvingGeneriek": "initiator"}
                        ],
                        "pdf": expected_document_result["url"],
                        "csv": expected_csv_document_result["url"],
                        "bijlagen": [],
                        "payment": {
                            "completed": False,
                            "amount": 0,
                            "public_order_ids": [],
                        },
                    },
                    "startAt": date.today().isoformat(),
                    "geometry": {
                        "type": "Point",
                        "coordinates": [52.36673378967122, 4.893164274470299],
                    },
                },
            }
            self.assertEqual(object_create.method, "POST")
            self.assertEqual(object_create.url, "https://objecten.nl/api/v1/objects")
            self.assertEqual(submitted_object_data, expected_object_body)

            # NOTE: the backend adds additional metadata that is not in the request body.
            expected_result = {
                "url": "https://objecten.nl/api/v1/objects/1",
                "uuid": "095be615-a8ad-4c33-8e9c-c7612fbf6c9f",
                "type": objects_form_options["objecttype"],
                "record": {
                    "index": 0,
                    "typeVersion": objects_form_options["objecttype_version"],
                    "data": submitted_object_data["record"]["data"],
                    "geometry": {
                        "type": "Point",
                        "coordinates": [52.36673378967122, 4.893164274470299],
                    },
                    "startAt": date.today().isoformat(),
                    "endAt": None,
                    "registrationAt": date.today().isoformat(),
                    "correctionFor": 0,
                    "correctedBy": "",
                },
            }
            # Result is simply the created object
            self.assertEqual(result, expected_result)

        with self.subTest("Document create (PDF summary)"):
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

        with self.subTest("Document create (CSV export)"):
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
        objects_form_options = dict(
            objecttype="https://objecttypen.nl/api/v1/objecttypes/2",
            objecttype_version=2,
            productaanvraag_type="testproduct",
            informatieobjecttype_submission_report="https://catalogi.nl/api/v1/informatieobjecttypen/2",
            upload_submission_csv=True,
            organisatie_rsin="123456782",
            zaak_vertrouwelijkheidaanduiding="geheim",
            doc_vertrouwelijkheidaanduiding="geheim",
        )

        # Set up API mocks
        expected_document_result = generate_oas_component(
            "documenten",
            "schemas/EnkelvoudigInformatieObject",
            url="https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
        )
        expected_csv_document_result = generate_oas_component(
            "documenten",
            "schemas/EnkelvoudigInformatieObject",
            url="https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/2",
        )
        m.post(
            "https://objecten.nl/api/v1/objects",
            status_code=201,
            json=get_create_json,
        )
        m.post(
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            status_code=201,
            json=expected_document_result,
        )
        m.post(
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            status_code=201,
            json=expected_csv_document_result,
            additional_matcher=lambda req: "csv" in req.json()["bestandsnaam"],
        )
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        # Run the registration
        plugin.register_submission(submission, objects_form_options)

        # check the requests made
        self.assertEqual(len(m.request_history), 3)
        document_create, csv_document_create, object_create = m.request_history

        with self.subTest("object create call and registration result"):
            submitted_object_data = object_create.json()

            self.assertEqual(
                submitted_object_data["type"],
                "https://objecttypen.nl/api/v1/objecttypes/2",
            )
            self.assertEqual(submitted_object_data["record"]["typeVersion"], 2)
            self.assertEqual(
                submitted_object_data["record"]["data"]["type"], "testproduct"
            )

        with self.subTest("Document create (PDF summary)"):
            document_create_body = document_create.json()

            self.assertEqual(document_create_body["bronorganisatie"], "123456782")
            self.assertEqual(
                document_create_body["informatieobjecttype"],
                "https://catalogi.nl/api/v1/informatieobjecttypen/2",
            )
            self.assertEqual(
                document_create_body["vertrouwelijkheidaanduiding"],
                "geheim",
            )

        with self.subTest("Document create (CSV export)"):
            csv_document_create_body = csv_document_create.json()

            self.assertEqual(
                csv_document_create.url,
                "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            )
            # Default informatieobjecttype used
            self.assertEqual(
                csv_document_create_body["informatieobjecttype"],
                "https://catalogi.nl/api/v1/informatieobjecttypen/4",
            )

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
        # Set up API mocks
        expected_document_result = generate_oas_component(
            "documenten",
            "schemas/EnkelvoudigInformatieObject",
            url="https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
        )
        m.post(
            "https://objecten.nl/api/v1/objects",
            status_code=201,
            json=get_create_json,
        )
        m.post(
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            status_code=201,
            json=expected_document_result,
        )
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        # Run the registration
        plugin.register_submission(submission, {"upload_submission_csv": False})

        # check the requests made
        self.assertEqual(len(m.request_history), 2)
        object_create = m.last_request

        with self.subTest("object create call and registration result"):
            submitted_object_data = object_create.json()

            self.assertEqual(submitted_object_data["record"]["data"]["csv"], "")
            self.assertEqual(
                submitted_object_data["record"]["data"]["pdf"],
                expected_document_result["url"],
            )

    def test_submission_with_objects_api_backend_missing_csv_iotype(self, m):
        submission = SubmissionFactory.create(with_report=True, completed=True)
        # Set up API mocks
        expected_document_result = generate_oas_component(
            "documenten",
            "schemas/EnkelvoudigInformatieObject",
            url="https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
        )
        m.post(
            "https://objecten.nl/api/v1/objects",
            status_code=201,
            json=get_create_json,
        )
        m.post(
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            status_code=201,
            json=expected_document_result,
        )
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        # Run the registration
        plugin.register_submission(
            submission,
            {
                "upload_submission_csv": True,
                "informatieobjecttype_submission_csv": "",
            },
        )

        # check the requests made
        self.assertEqual(len(m.request_history), 2)
        object_create = m.last_request

        with self.subTest("object create call and registration result"):
            submitted_object_data = object_create.json()

            self.assertEqual(submitted_object_data["record"]["data"]["csv"], "")
            self.assertEqual(
                submitted_object_data["record"]["data"]["pdf"],
                expected_document_result["url"],
            )

    def test_submission_with_objects_api_backend_override_content_json(self, m):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "voornaam",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_voornamen,
                    },
                },
            ],
            submitted_data={"voornaam": "Foo"},
            language_code="en",
        )
        submission_step = submission.steps[0]
        assert submission_step.form_step
        step_slug = submission_step.form_step.slug
        objects_form_options = dict(
            upload_submission_csv=False,
            content_json=textwrap.dedent(
                """
                {
                    "bron": {
                        "naam": "Open Formulieren",
                        "kenmerk": "{{ submission.kenmerk }}"
                    },
                    "type": "{{ productaanvraag_type }}",
                    "aanvraaggegevens": {% json_summary %},
                    "taal": "{{ submission.language_code  }}"
                }
            """
            ),
        )
        # Set up API mocks
        expected_document_result = generate_oas_component(
            "documenten",
            "schemas/EnkelvoudigInformatieObject",
            url="https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
        )
        m.post(
            "https://objecten.nl/api/v1/objects",
            status_code=201,
            json=get_create_json,
        )
        m.post(
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            status_code=201,
            json=expected_document_result,
        )
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        # Run the registration
        plugin.register_submission(submission, objects_form_options)

        # check the requests made
        self.assertEqual(len(m.request_history), 2)

        with self.subTest("object create call"):
            object_create = m.last_request
            expected_record_data = {
                "bron": {
                    "naam": "Open Formulieren",
                    "kenmerk": str(submission.uuid),
                },
                "type": "terugbelnotitie",
                "aanvraaggegevens": {step_slug: {"voornaam": "Foo"}},
                "taal": "en",
            }

            self.assertEqual(object_create.url, "https://objecten.nl/api/v1/objects")
            object_create_body = object_create.json()
            self.assertEqual(object_create_body["record"]["data"], expected_record_data)

    def test_submission_with_objects_api_backend_use_config_defaults(self, m):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "voornaam",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_voornamen,
                    },
                }
            ],
            submitted_data={"voornaam": "Foo"},
            language_code="en",
        )
        submission_step = submission.steps[0]
        assert submission_step.form_step
        step_slug = submission_step.form_step.slug

        # Set up API mocks
        expected_document_result = generate_oas_component(
            "documenten",
            "schemas/EnkelvoudigInformatieObject",
            url="https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
        )
        expected_csv_document_result = generate_oas_component(
            "documenten",
            "schemas/EnkelvoudigInformatieObject",
            url="https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/2",
        )
        m.post(
            "https://objecten.nl/api/v1/objects",
            status_code=201,
            json=get_create_json,
        )
        m.post(
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            status_code=201,
            json=expected_document_result,
        )
        m.post(
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            status_code=201,
            json=expected_csv_document_result,
            additional_matcher=lambda req: "csv" in req.json()["bestandsnaam"],
        )
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        # Run the registration, applying default options from the config
        plugin.register_submission(submission, {})

        # check the requests made
        self.assertEqual(len(m.request_history), 2)
        document_create, object_create = m.request_history

        with self.subTest("Document create (PDF summary)"):
            document_create_body = document_create.json()

            self.assertEqual(
                document_create.url,
                "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            )
            self.assertEqual(document_create_body["taal"], "eng")
            self.assertEqual(document_create_body["bronorganisatie"], "000000000")
            self.assertEqual(
                document_create_body["informatieobjecttype"],
                "https://catalogi.nl/api/v1/informatieobjecttypen/1",
            )
            self.assertNotIn("vertrouwelijkheidaanduiding", document_create_body)

        with self.subTest("object create call"):
            object_create_body = object_create.json()

            expected_record_data = {
                "typeVersion": 1,
                "data": {
                    "aanvraaggegevens": {step_slug: {"voornaam": "Foo"}},
                    "betrokkenen": [
                        {"inpBsn": "", "rolOmschrijvingGeneriek": "initiator"}
                    ],
                    "bijlagen": [],
                    "bron": {
                        "kenmerk": str(submission.uuid),
                        "naam": "Open Formulieren",
                    },
                    "csv": "",
                    "pdf": expected_document_result["url"],
                    "taal": "en",
                    "type": "terugbelnotitie",
                    "payment": {
                        "completed": False,
                        "amount": 0,
                        "public_order_ids": [],
                    },
                },
                "startAt": date.today().isoformat(),
            }
            self.assertEqual(object_create.url, "https://objecten.nl/api/v1/objects")
            self.assertEqual(object_create_body["record"], expected_record_data)

    def test_submission_with_objects_api_backend_attachments(self, m):
        # Form.io configuration is irrelevant for this test, but normally you'd have
        # set up some file upload components.
        submission = SubmissionFactory.from_components(
            [],
            submitted_data={},
            language_code="en",
            completed=True,
        )
        submission_step = submission.steps[0]
        # Set up two attachments to upload to the documents API
        SubmissionFileAttachmentFactory.create(
            submission_step=submission_step, file_name="attachment1.jpg"
        )
        SubmissionFileAttachmentFactory.create(
            submission_step=submission_step, file_name="attachment2.jpg"
        )

        # Set up API mocks
        pdf, attachment1, attachment2 = [
            generate_oas_component(
                "documenten",
                "schemas/EnkelvoudigInformatieObject",
                url="https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
            ),
            generate_oas_component(
                "documenten",
                "schemas/EnkelvoudigInformatieObject",
                url="https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/2",
            ),
            generate_oas_component(
                "documenten",
                "schemas/EnkelvoudigInformatieObject",
                url="https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/3",
            ),
        ]
        m.post(
            "https://objecten.nl/api/v1/objects",
            status_code=201,
            json=get_create_json,
        )
        m.post(
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            status_code=201,
            json=pdf,
            additional_matcher=lambda req: req.json()["bestandsnaam"].endswith(".pdf"),
        )
        m.post(
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            status_code=201,
            json=attachment1,
            additional_matcher=lambda req: req.json()["bestandsnaam"]
            == "attachment1.jpg",
        )
        m.post(
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            status_code=201,
            json=attachment2,
            additional_matcher=lambda req: req.json()["bestandsnaam"]
            == "attachment2.jpg",
        )
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        # Run the registration
        plugin.register_submission(submission, {})

        # check the requests made
        self.assertEqual(len(m.request_history), 4)
        (
            pdf_create,
            attachment1_create,
            attachment2_create,
            object_create,
        ) = m.request_history

        with self.subTest("object create call"):
            record_data = object_create.json()["record"]["data"]

            self.assertEqual(object_create.url, "https://objecten.nl/api/v1/objects")
            self.assertEqual(
                record_data["pdf"],
                "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
            )
            self.assertEqual(
                record_data["bijlagen"],
                [
                    "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/2",
                    "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/3",
                ],
            )

        with self.subTest("Document create (PDF summary)"):
            pdf_create_data = pdf_create.json()

            self.assertEqual(
                pdf_create.url,
                "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            )
            self.assertEqual(pdf_create_data["bronorganisatie"], "000000000")
            self.assertEqual(
                pdf_create_data["informatieobjecttype"],
                "https://catalogi.nl/api/v1/informatieobjecttypen/1",
            )
            self.assertNotIn("vertrouwelijkheidaanduiding", pdf_create_data)

        with self.subTest("Document create (attachment 1)"):
            attachment1_create_data = attachment1_create.json()

            self.assertEqual(
                attachment1_create.url,
                "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            )
            self.assertEqual(attachment1_create_data["bronorganisatie"], "000000000")
            self.assertEqual(attachment1_create_data["taal"], "eng")
            self.assertEqual(
                attachment1_create_data["informatieobjecttype"],
                "https://catalogi.nl/api/v1/informatieobjecttypen/3",
            )
            self.assertNotIn("vertrouwelijkheidaanduiding", attachment1_create_data)

        with self.subTest("Document create (attachment 2)"):
            attachment2_create_data = attachment2_create.json()

            self.assertEqual(
                attachment1_create.url,
                "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            )
            self.assertEqual(attachment2_create_data["bronorganisatie"], "000000000")
            self.assertEqual(attachment2_create_data["taal"], "eng")
            self.assertEqual(
                attachment2_create_data["informatieobjecttype"],
                "https://catalogi.nl/api/v1/informatieobjecttypen/3",
            )
            self.assertNotIn("vertrouwelijkheidaanduiding", attachment2_create_data)

    def test_submission_with_objects_api_backend_attachments_specific_iotypen(self, m):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "field1",
                    "type": "file",
                    "registration": {
                        "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/10",
                    },
                },
                {
                    "key": "field2",
                    "type": "file",
                    "registration": {
                        "informatieobjecttype": "",
                    },
                },
            ],
            language_code="en",
        )
        submission_step = submission.steps[0]
        SubmissionFileAttachmentFactory.create(
            submission_step=submission_step,
            file_name="attachment1.jpg",
            form_key="field1",
            _component_configuration_path="components.0",
        )
        SubmissionFileAttachmentFactory.create(
            submission_step=submission_step,
            file_name="attachment2.jpg",
            form_key="field2",
            _component_configuration_path="component.1",
        )

        # Set up API mocks
        pdf, attachment1, attachment2 = [
            generate_oas_component(
                "documenten",
                "schemas/EnkelvoudigInformatieObject",
                url="https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
            ),
            generate_oas_component(
                "documenten",
                "schemas/EnkelvoudigInformatieObject",
                url="https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/2",
            ),
            generate_oas_component(
                "documenten",
                "schemas/EnkelvoudigInformatieObject",
                url="https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/3",
            ),
        ]
        m.post(
            "https://objecten.nl/api/v1/objects",
            status_code=201,
            json=get_create_json,
        )
        m.post(
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            status_code=201,
            json=pdf,
            additional_matcher=lambda req: req.json()["bestandsnaam"].endswith(".pdf"),
        )
        m.post(
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            status_code=201,
            json=attachment1,
            additional_matcher=lambda req: req.json()["bestandsnaam"]
            == "attachment1.jpg",
        )
        m.post(
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            status_code=201,
            json=attachment2,
            additional_matcher=lambda req: req.json()["bestandsnaam"]
            == "attachment2.jpg",
        )
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        # Run the registration
        plugin.register_submission(submission, {})

        # check the requests made
        self.assertEqual(len(m.request_history), 4)
        attachment1_create = m.request_history[1]
        attachment2_create = m.request_history[2]

        with self.subTest("Document create (attachment 1)"):
            attachment1_create_data = attachment1_create.json()

            self.assertEqual(
                attachment1_create.url,
                "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            )
            self.assertEqual(attachment1_create_data["bronorganisatie"], "000000000")
            self.assertEqual(attachment1_create_data["taal"], "eng")
            # Use override IOType
            self.assertEqual(
                attachment1_create_data["informatieobjecttype"],
                "https://catalogi.nl/api/v1/informatieobjecttypen/10",
            )
            self.assertNotIn("vertrouwelijkheidaanduiding", attachment1_create_data)

        with self.subTest("Document create (attachment 2)"):
            attachment2_create_data = attachment2_create.json()

            self.assertEqual(
                attachment1_create.url,
                "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            )
            self.assertEqual(attachment2_create_data["bronorganisatie"], "000000000")
            self.assertEqual(attachment2_create_data["taal"], "eng")
            # Fallback to default IOType
            self.assertEqual(
                attachment2_create_data["informatieobjecttype"],
                "https://catalogi.nl/api/v1/informatieobjecttypen/3",
            )
            self.assertNotIn("vertrouwelijkheidaanduiding", attachment2_create_data)

    def test_submission_with_objects_api_backend_attachments_component_overwrites(
        self, m
    ):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "fileUpload",
                    "type": "file",
                    "registration": {
                        "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/10",
                        "bronorganisatie": "123123123",
                        "docVertrouwelijkheidaanduiding": "geheim",
                        "titel": "A Custom Title",
                    },
                },
            ],
            submitted_data={
                "fileUpload": [
                    {
                        "url": "http://server/api/v2/submissions/files/62f2ec22-da7d-4385-b719-b8637c1cd483",
                        "data": {
                            "url": "http://server/api/v2/submissions/files/62f2ec22-da7d-4385-b719-b8637c1cd483",
                            "form": "",
                            "name": "some-attachment.jpg",
                            "size": 46114,
                            "baseUrl": "http://server/form",
                            "project": "",
                        },
                        "name": "my-image-12305610-2da4-4694-a341-ccb919c3d543.jpg",
                        "size": 46114,
                        "type": "image/jpg",
                        "storage": "url",
                        "originalName": "some-attachment.jpg",
                    }
                ],
            },
            language_code="en",
        )
        submission_step = submission.steps[0]
        SubmissionFileAttachmentFactory.create(
            submission_step=submission_step,
            file_name="some-attachment.jpg",
            form_key="fileUpload",
            _component_configuration_path="components.0",
        )

        # Set up API mocks
        pdf, attachment = [
            generate_oas_component(
                "documenten",
                "schemas/EnkelvoudigInformatieObject",
                url="https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
            ),
            generate_oas_component(
                "documenten",
                "schemas/EnkelvoudigInformatieObject",
                url="https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/2",
            ),
        ]
        m.post(
            "https://objecten.nl/api/v1/objects",
            status_code=201,
            json=get_create_json,
        )
        m.post(
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            status_code=201,
            json=pdf,
            additional_matcher=lambda req: req.json()["bestandsnaam"].endswith(".pdf"),
        )
        m.post(
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            status_code=201,
            json=attachment,
            additional_matcher=lambda req: req.json()["bestandsnaam"]
            == "some-attachment.jpg",
        )
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        # Run the registration
        plugin.register_submission(submission, {})

        # check the requests made
        self.assertEqual(len(m.request_history), 3)
        document_create_attachment = m.request_history[1]

        document_create_attachment_body = document_create_attachment.json()
        self.assertEqual(document_create_attachment.method, "POST")
        self.assertEqual(
            document_create_attachment.url,
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
        )
        # Check use of override settings
        self.assertEqual(
            document_create_attachment_body["informatieobjecttype"],
            "https://catalogi.nl/api/v1/informatieobjecttypen/10",
        )
        self.assertEqual(
            document_create_attachment_body["bronorganisatie"], "123123123"
        )
        self.assertEqual(
            document_create_attachment_body["vertrouwelijkheidaanduiding"], "geheim"
        )
        self.assertEqual(document_create_attachment_body["titel"], "A Custom Title")

    def test_submission_with_objects_api_backend_attachments_component_inside_fieldset_overwrites(
        self, m
    ):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "fieldset",
                    "type": "fieldset",
                    "label": "A fieldset",
                    "components": [
                        {
                            "key": "fileUpload",
                            "type": "file",
                            "registration": {
                                "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/10",
                                "bronorganisatie": "123123123",
                                "docVertrouwelijkheidaanduiding": "geheim",
                                "titel": "A Custom Title",
                            },
                        },
                    ],
                },
            ],
            submitted_data={
                "fileUpload": [
                    {
                        "url": "http://server/api/v2/submissions/files/62f2ec22-da7d-4385-b719-b8637c1cd483",
                        "data": {
                            "url": "http://server/api/v2/submissions/files/62f2ec22-da7d-4385-b719-b8637c1cd483",
                            "form": "",
                            "name": "some-attachment.jpg",
                            "size": 46114,
                            "baseUrl": "http://server/form",
                            "project": "",
                        },
                        "name": "my-image-12305610-2da4-4694-a341-ccb919c3d543.jpg",
                        "size": 46114,
                        "type": "image/jpg",
                        "storage": "url",
                        "originalName": "some-attachment.jpg",
                    }
                ],
            },
            language_code="en",
        )
        submission_step = submission.steps[0]
        SubmissionFileAttachmentFactory.create(
            submission_step=submission_step,
            file_name="some-attachment.jpg",
            form_key="fileUpload",
            _component_configuration_path="components.0.components.0",
        )
        # Set up API mocks
        pdf, attachment = [
            generate_oas_component(
                "documenten",
                "schemas/EnkelvoudigInformatieObject",
                url="https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
            ),
            generate_oas_component(
                "documenten",
                "schemas/EnkelvoudigInformatieObject",
                url="https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/2",
            ),
        ]
        m.post(
            "https://objecten.nl/api/v1/objects",
            status_code=201,
            json=get_create_json,
        )
        m.post(
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            status_code=201,
            json=pdf,
            additional_matcher=lambda req: req.json()["bestandsnaam"].endswith(".pdf"),
        )
        m.post(
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            status_code=201,
            json=attachment,
            additional_matcher=lambda req: req.json()["bestandsnaam"]
            == "some-attachment.jpg",
        )
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        # Run the registration
        plugin.register_submission(submission, {})

        # check the requests made
        self.assertEqual(len(m.request_history), 3)
        document_create_attachment = m.request_history[1]

        document_create_attachment_body = document_create_attachment.json()
        self.assertEqual(document_create_attachment.method, "POST")
        self.assertEqual(
            document_create_attachment.url,
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
        )
        # Check use of override settings
        self.assertEqual(
            document_create_attachment_body["informatieobjecttype"],
            "https://catalogi.nl/api/v1/informatieobjecttypen/10",
        )
        self.assertEqual(
            document_create_attachment_body["bronorganisatie"], "123123123"
        )
        self.assertEqual(
            document_create_attachment_body["vertrouwelijkheidaanduiding"], "geheim"
        )
        self.assertEqual(document_create_attachment_body["titel"], "A Custom Title")

    @override_settings(ESCAPE_REGISTRATION_OUTPUT=True)
    def test_submission_with_objects_api_escapes_html(self, m):
        content_template = textwrap.dedent(
            """
            {
                "summary": {% json_summary %},
                "manual_variable": "{{ variables.voornaam }}"
            }
            """
        )
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "voornaam",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_voornamen,
                    },
                },
            ],
            submitted_data={"voornaam": "<script>alert();</script>"},
            language_code="en",
        )

        submission_step = submission.steps[0]
        assert submission_step.form_step
        step_slug = submission_step.form_step.slug
        # Set up API mocks
        expected_document_result = generate_oas_component(
            "documenten",
            "schemas/EnkelvoudigInformatieObject",
            url="https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
        )
        m.post(
            "https://objecten.nl/api/v1/objects",
            status_code=201,
            json=get_create_json,
        )
        m.post(
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            status_code=201,
            json=expected_document_result,
        )
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        # Run the registration
        plugin.register_submission(
            submission,
            {
                "content_json": content_template,
                "upload_submission_csv": False,
            },
        )

        self.assertEqual(len(m.request_history), 2)

        object_create = m.last_request
        expected_record_data = {
            "summary": {
                step_slug: {
                    "voornaam": "&lt;script&gt;alert();&lt;/script&gt;",
                },
            },
            "manual_variable": "&lt;script&gt;alert();&lt;/script&gt;",
        }
        object_create_body = object_create.json()
        posted_record_data = object_create_body["record"]["data"]
        self.assertEqual(object_create.method, "POST")
        self.assertEqual(object_create.url, "https://objecten.nl/api/v1/objects")
        self.assertEqual(posted_record_data, expected_record_data)

    def test_submission_with_payment(self, m):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "test",
                    "type": "textfield",
                },
            ],
            registration_success=True,
            submitted_data={"test": "some test data"},
            language_code="en",
            registration_result={
                "url": "https://objecten.nl/api/v1/objects/111-222-333"
            },
        )
        SubmissionPaymentFactory.create(
            submission=submission,
            status=PaymentStatus.started,
            amount=10,
            public_order_id="",
        )

        m.post(
            "https://objecten.nl/api/v1/objects",
            status_code=201,
            json=get_create_json,
        )
        m.post(
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            status_code=201,
            json=generate_oas_component(
                "documenten",
                "schemas/EnkelvoudigInformatieObject",
                url="https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
            ),
        )

        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)
        plugin.register_submission(
            submission,
            {},
        )

        self.assertEqual(len(m.request_history), 2)

        object_create = m.last_request
        body = object_create.json()

        self.assertEqual(
            body["record"]["data"]["payment"],
            {
                "completed": False,
                "amount": 10.00,
                "public_order_ids": [],
            },
        )
