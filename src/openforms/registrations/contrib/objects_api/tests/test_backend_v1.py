import textwrap
from pathlib import Path
from unittest.mock import patch
from uuid import UUID

from django.test import TestCase, override_settings, tag
from django.utils import timezone

from openforms.authentication.service import AuthAttribute
from openforms.contrib.objects_api.clients import get_documents_client
from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory
from openforms.payments.constants import PaymentStatus
from openforms.payments.tests.factories import SubmissionPaymentFactory
from openforms.submissions.constants import PostSubmissionEvents
from openforms.submissions.tasks import pre_registration
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
)
from openforms.utils.tests.vcr import OFVCRMixin

from ....constants import RegistrationAttribute
from ..models import (
    ObjectsAPIConfig,
    ObjectsAPIRegistrationData,
    ObjectsAPISubmissionAttachment,
)
from ..plugin import PLUGIN_IDENTIFIER, ObjectsAPIRegistration
from ..submission_registration import ObjectsAPIV1Handler
from ..typing import RegistrationOptionsV1

TEST_FILES = Path(__file__).parent / "files"
FIXED_SUBMISSION_UUID = UUID(hex="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")


class ObjectsAPIBackendV1Tests(OFVCRMixin, TestCase):
    maxDiff = None
    VCR_TEST_FILES = TEST_FILES

    def setUp(self):
        super().setUp()

        config = ObjectsAPIConfig(
            productaanvraag_type="terugbelnotitie",
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
                            "inpBsn": "{{ variables.auth_bsn }}",
                            "rolOmschrijvingGeneriek": "initiator"
                        }
                    ],
                    "pdf": "{{ submission.pdf_url }}",
                    "csv": "{{ submission.csv_url }}",
                    "bijlagen": {% uploaded_attachment_urls %},
                    "payment": {
                        "completed": {% if payment.completed %}true{% else %}false{% endif %},
                        "amount": {{ payment.amount }},
                        "public_order_ids": [{% for public_order_id in payment.public_order_ids%}"{{ public_order_id|escapejs }}"{% if not forloop.last %},{% endif %}{% endfor %}],
                        "payment_ids": [{% for payment_id in payment.provider_payment_ids%}"{{ payment_id|escapejs }}"{% if not forloop.last %},{% endif %}{% endfor %}]
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

        self.objects_api_group = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True,
            informatieobjecttype_submission_report="http://localhost:8003/catalogi/api/v1/informatieobjecttypen/7a474713-0833-402a-8441-e467c08ac55b",
            informatieobjecttype_submission_csv="http://localhost:8003/catalogi/api/v1/informatieobjecttypen/b2d83b94-9b9b-4e80-a82f-73ff993c62f3",
            informatieobjecttype_attachment="http://localhost:8003/catalogi/api/v1/informatieobjecttypen/531f6c1a-97f7-478c-85f0-67d2f23661c7",
            organisatie_rsin="000000000",
        )

    def test_submission_with_objects_api_backend_override_defaults(self):
        """Test that the configured IOTs are used instead of the global defaults on the Objects API group."""

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
                "coordinaat": {
                    "type": "Point",
                    "coordinates": [4.893164274470299, 52.36673378967122],
                },
            },
            language_code="en",
            uuid=FIXED_SUBMISSION_UUID,
        )
        submission_step = submission.steps[0]
        assert submission_step.form_step
        submission_step.form_step.slug = "test-slug"
        submission_step.form_step.save()

        objects_form_options = {
            "version": 1,
            "objects_api_group": self.objects_api_group,
            "objecttype": UUID("8faed0fa-7864-4409-aa6d-533a37616a9e"),
            "objecttype_version": 1,
            "productaanvraag_type": "testproduct",
            "update_existing_object": False,
            "auth_attribute_path": [],
            # `omschrijving` "PDF Informatieobjecttype other catalog":
            "informatieobjecttype_submission_report": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/f2908f6f-aa07-42ef-8760-74c5234f2d25",
            "upload_submission_csv": True,
            # `omschrijving` "CSV Informatieobjecttype other catalog":
            "informatieobjecttype_submission_csv": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/d1cfb1d8-8593-4814-919d-72e38e80388f",
            "organisatie_rsin": "123456782",
            "zaak_vertrouwelijkheidaanduiding": "geheim",
            "doc_vertrouwelijkheidaanduiding": "geheim",
        }

        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        # Run the registration
        result = plugin.register_submission(submission, objects_form_options)

        registration_data = ObjectsAPIRegistrationData.objects.get(
            submission=submission
        )

        self.assertEqual(
            result["type"],
            "http://objecttypes-web:8000/api/v2/objecttypes/8faed0fa-7864-4409-aa6d-533a37616a9e",
        )
        self.assertEqual(result["record"]["typeVersion"], 1)
        self.assertEqual(
            result["record"]["data"],
            {
                "bron": {
                    "naam": "Open Formulieren",
                    "kenmerk": str(FIXED_SUBMISSION_UUID),
                },
                "type": "testproduct",
                "aanvraaggegevens": {
                    "test-slug": {
                        "voornaam": "Foo",
                        "achternaam": "Bar",
                        "tussenvoegsel": "de",
                        "geboortedatum": "2000-12-31",
                        "coordinaat": {
                            "type": "Point",
                            "coordinates": [4.893164274470299, 52.36673378967122],
                        },
                    }
                },
                "taal": "en",
                "betrokkenen": [{"inpBsn": "", "rolOmschrijvingGeneriek": "initiator"}],
                "pdf": registration_data.pdf_url,
                "csv": registration_data.csv_url,
                "bijlagen": [],
                "payment": {
                    "completed": False,
                    "amount": 0,
                    "public_order_ids": [],
                    "payment_ids": [],
                },
            },
        )

        # Assert that it used the IOTs in the config, not the defaults in the config group:
        with get_documents_client(self.objects_api_group) as documents_client:
            csv_document = documents_client.get(registration_data.csv_url).json()
            pdf_document = documents_client.get(registration_data.pdf_url).json()

        self.assertEqual(
            csv_document["informatieobjecttype"],
            "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/d1cfb1d8-8593-4814-919d-72e38e80388f",
        )

        self.assertEqual(
            pdf_document["informatieobjecttype"],
            "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/f2908f6f-aa07-42ef-8760-74c5234f2d25",
        )

    def test_submission_with_objects_api_backend_override_defaults_upload_csv_default_type(
        self,
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
        objects_form_options = {
            "version": 1,
            "objects_api_group": self.objects_api_group,
            "objecttype": UUID("8faed0fa-7864-4409-aa6d-533a37616a9e"),
            "objecttype_version": 1,
            "productaanvraag_type": "testproduct",
            "informatieobjecttype_submission_report": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/f2908f6f-aa07-42ef-8760-74c5234f2d25",
            "upload_submission_csv": True,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "organisatie_rsin": "123456782",
            "zaak_vertrouwelijkheidaanduiding": "geheim",
            "doc_vertrouwelijkheidaanduiding": "geheim",
        }

        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        # Run the registration
        plugin.register_submission(submission, objects_form_options)

        registration_data = ObjectsAPIRegistrationData.objects.get(
            submission=submission
        )

        with get_documents_client(self.objects_api_group) as documents_client:
            csv_document = documents_client.get(registration_data.csv_url).json()
            pdf_document = documents_client.get(registration_data.pdf_url).json()

        self.assertEqual(
            csv_document["informatieobjecttype"],
            "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/b2d83b94-9b9b-4e80-a82f-73ff993c62f3",
            "should have used the default IOT in the config group",
        )

        self.assertEqual(
            pdf_document["informatieobjecttype"],
            "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/f2908f6f-aa07-42ef-8760-74c5234f2d25",
            "should have used the IOT in the config",
        )

    def test_submission_with_objects_api_backend_override_defaults_do_not_upload_csv(
        self,
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

        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        # Run the registration
        result = plugin.register_submission(
            submission,
            {
                "version": 1,
                "objecttype": UUID("8faed0fa-7864-4409-aa6d-533a37616a9e"),
                "objecttype_version": 1,
                "objects_api_group": self.objects_api_group,
                "upload_submission_csv": False,
                "update_existing_object": False,
                "auth_attribute_path": [],
            },
        )

        registration_data = ObjectsAPIRegistrationData.objects.get(
            submission=submission
        )

        self.assertEqual(result["record"]["data"]["csv"], "")

        with get_documents_client(self.objects_api_group) as documents_client:
            pdf_document = documents_client.get(registration_data.pdf_url).json()

        self.assertEqual(
            pdf_document["informatieobjecttype"],
            "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/7a474713-0833-402a-8441-e467c08ac55b",
        )

    def test_submission_with_objects_api_backend_missing_csv_iotype(self):
        submission = SubmissionFactory.create(with_report=True, completed=True)

        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        # Run the registration
        result = plugin.register_submission(
            submission,
            {
                "version": 1,
                "objecttype": UUID("8faed0fa-7864-4409-aa6d-533a37616a9e"),
                "objecttype_version": 1,
                "objects_api_group": self.objects_api_group,
                "upload_submission_csv": True,
                "update_existing_object": False,
                "auth_attribute_path": [],
                "informatieobjecttype_submission_csv": "",
            },
        )

        registration_data = ObjectsAPIRegistrationData.objects.get(
            submission=submission
        )

        self.assertEqual(result["record"]["data"]["csv"], "")

        with get_documents_client(self.objects_api_group) as documents_client:
            pdf_document = documents_client.get(registration_data.pdf_url).json()

        self.assertEqual(
            pdf_document["informatieobjecttype"],
            "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/7a474713-0833-402a-8441-e467c08ac55b",
        )

    def test_submission_with_objects_api_backend_override_content_json(self):
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
            uuid=FIXED_SUBMISSION_UUID,
        )
        submission_step = submission.steps[0]
        assert submission_step.form_step
        submission_step.form_step.slug = "test-slug"
        submission_step.form_step.save()

        objects_form_options = {
            "version": 1,
            "objecttype": UUID("8faed0fa-7864-4409-aa6d-533a37616a9e"),
            "objecttype_version": 1,
            "objects_api_group": self.objects_api_group,
            "upload_submission_csv": False,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "content_json": textwrap.dedent(
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
        }

        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        # Run the registration
        result = plugin.register_submission(submission, objects_form_options)

        self.assertEqual(
            result["record"]["data"],
            {
                "bron": {
                    "naam": "Open Formulieren",
                    "kenmerk": str(FIXED_SUBMISSION_UUID),
                },
                "type": "terugbelnotitie",
                "aanvraaggegevens": {"test-slug": {"voornaam": "Foo"}},
                "taal": "en",
            },
        )

    def test_submission_with_objects_api_backend_use_config_defaults(self):
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
            uuid=FIXED_SUBMISSION_UUID,
        )
        submission_step = submission.steps[0]
        assert submission_step.form_step
        submission_step.form_step.slug = "test-slug"
        submission_step.form_step.save()

        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        # Run the registration, applying default options from the config
        # (while still specifying the required fields):
        result = plugin.register_submission(
            submission,
            {
                "version": 1,
                "objects_api_group": self.objects_api_group,
                "objecttype": UUID("8faed0fa-7864-4409-aa6d-533a37616a9e"),
                "objecttype_version": 1,
                "update_existing_object": False,
                "auth_attribute_path": [],
            },
        )

        registration_data = ObjectsAPIRegistrationData.objects.get(
            submission=submission
        )

        with get_documents_client(self.objects_api_group) as documents_client:
            pdf_document = documents_client.get(registration_data.pdf_url).json()

        with self.subTest("Document creation (PDF summary)"):
            self.assertEqual(pdf_document["taal"], "eng")
            self.assertEqual(pdf_document["bronorganisatie"], "000000000")
            self.assertEqual(
                pdf_document["informatieobjecttype"],
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/7a474713-0833-402a-8441-e467c08ac55b",
            )
            self.assertEqual(pdf_document["vertrouwelijkheidaanduiding"], "openbaar")

        with self.subTest("Object creation"):
            self.assertEqual(result["record"]["typeVersion"], 1)
            self.assertEqual(
                result["record"]["data"],
                {
                    "aanvraaggegevens": {"test-slug": {"voornaam": "Foo"}},
                    "betrokkenen": [
                        {"inpBsn": "", "rolOmschrijvingGeneriek": "initiator"}
                    ],
                    "bijlagen": [],
                    "bron": {
                        "kenmerk": str(FIXED_SUBMISSION_UUID),
                        "naam": "Open Formulieren",
                    },
                    "csv": "",
                    "pdf": registration_data.pdf_url,
                    "taal": "en",
                    "type": "terugbelnotitie",
                    "payment": {
                        "completed": False,
                        "amount": 0,
                        "public_order_ids": [],
                        "payment_ids": [],
                    },
                },
            )

    def test_submission_with_objects_api_backend_attachments(self):
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
        file_attachment_1 = SubmissionFileAttachmentFactory.create(
            submission_step=submission_step, file_name="attachment1.jpg"
        )
        file_attachment_2 = SubmissionFileAttachmentFactory.create(
            submission_step=submission_step, file_name="attachment2.jpg"
        )

        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        # Run the registration
        result = plugin.register_submission(
            submission,
            {
                "version": 1,
                "objects_api_group": self.objects_api_group,
                "objecttype": UUID("8faed0fa-7864-4409-aa6d-533a37616a9e"),
                "objecttype_version": 1,
                "update_existing_object": False,
                "auth_attribute_path": [],
            },
        )

        registration_data = ObjectsAPIRegistrationData.objects.get(
            submission=submission
        )

        with get_documents_client(self.objects_api_group) as documents_client:
            pdf_document = documents_client.get(registration_data.pdf_url).json()
            attachment_document_1 = documents_client.get(
                ObjectsAPISubmissionAttachment.objects.get(
                    submission_file_attachment=file_attachment_1
                ).document_url
            ).json()
            attachment_document_2 = documents_client.get(
                ObjectsAPISubmissionAttachment.objects.get(
                    submission_file_attachment=file_attachment_2
                ).document_url
            ).json()

        with self.subTest("object creation"):
            record_data = result["record"]["data"]

            self.assertEqual(record_data["pdf"], registration_data.pdf_url)
            self.assertCountEqual(
                record_data["bijlagen"],
                ObjectsAPISubmissionAttachment.objects.values_list(
                    "document_url", flat=True
                ),
            )

        with self.subTest("Document creation (PDF summary)"):
            self.assertEqual(pdf_document["bronorganisatie"], "000000000")
            self.assertEqual(
                pdf_document["informatieobjecttype"],
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/7a474713-0833-402a-8441-e467c08ac55b",
            )
            self.assertEqual(pdf_document["vertrouwelijkheidaanduiding"], "openbaar")

        with self.subTest("Document creation (attachment 1)"):
            self.assertEqual(attachment_document_1["bronorganisatie"], "000000000")
            self.assertEqual(attachment_document_1["taal"], "eng")
            self.assertEqual(
                attachment_document_1["informatieobjecttype"],
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/531f6c1a-97f7-478c-85f0-67d2f23661c7",
            )
            self.assertEqual(
                attachment_document_1["vertrouwelijkheidaanduiding"], "openbaar"
            )
            self.assertIsNotNone(attachment_document_1["ontvangstdatum"])

        with self.subTest("Document create (attachment 2)"):
            self.assertEqual(attachment_document_2["bronorganisatie"], "000000000")
            self.assertEqual(attachment_document_2["taal"], "eng")
            self.assertEqual(
                attachment_document_2["informatieobjecttype"],
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/531f6c1a-97f7-478c-85f0-67d2f23661c7",
            )
            self.assertEqual(
                attachment_document_2["vertrouwelijkheidaanduiding"], "openbaar"
            )
            self.assertIsNotNone(attachment_document_2["ontvangstdatum"])

    def test_submission_with_objects_api_backend_attachments_specific_iotypen(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "field1",
                    "type": "file",
                    "registration": {
                        # `omschrijving` "Attachment Informatieobjecttype other catalog":
                        "informatieobjecttype": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/cd6aeaf2-ca37-416f-b78c-1cc302f81a81",
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
            completed=True,
        )
        submission_step = submission.steps[0]
        file_attachment_1 = SubmissionFileAttachmentFactory.create(
            submission_step=submission_step,
            file_name="attachment1.jpg",
            form_key="field1",
            _component_configuration_path="components.0",
        )
        file_attachment_2 = SubmissionFileAttachmentFactory.create(
            submission_step=submission_step,
            file_name="attachment2.jpg",
            form_key="field2",
            _component_configuration_path="component.1",
        )

        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        # Run the registration
        plugin.register_submission(
            submission,
            {
                "version": 1,
                "objects_api_group": self.objects_api_group,
                "objecttype": UUID("8faed0fa-7864-4409-aa6d-533a37616a9e"),
                "objecttype_version": 1,
                "update_existing_object": False,
                "auth_attribute_path": [],
            },
        )

        with get_documents_client(self.objects_api_group) as documents_client:
            attachment_document_1 = documents_client.get(
                ObjectsAPISubmissionAttachment.objects.get(
                    submission_file_attachment=file_attachment_1
                ).document_url
            ).json()
            attachment_document_2 = documents_client.get(
                ObjectsAPISubmissionAttachment.objects.get(
                    submission_file_attachment=file_attachment_2
                ).document_url
            ).json()

        with self.subTest("Document creation (attachment 1)"):
            self.assertEqual(attachment_document_1["bronorganisatie"], "000000000")
            self.assertEqual(attachment_document_1["taal"], "eng")
            # Use overridden IOType:
            self.assertEqual(
                attachment_document_1["informatieobjecttype"],
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/cd6aeaf2-ca37-416f-b78c-1cc302f81a81",
            )
            self.assertEqual(
                attachment_document_1["vertrouwelijkheidaanduiding"], "openbaar"
            )

        with self.subTest("Document creation (attachment 2)"):
            self.assertEqual(attachment_document_2["bronorganisatie"], "000000000")
            self.assertEqual(attachment_document_2["taal"], "eng")
            # Fallback to default IOType
            self.assertEqual(
                attachment_document_2["informatieobjecttype"],
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/531f6c1a-97f7-478c-85f0-67d2f23661c7",
            )
            self.assertEqual(
                attachment_document_2["vertrouwelijkheidaanduiding"], "openbaar"
            )

    def test_submission_with_objects_api_backend_attachments_component_overwrites(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "fileUpload",
                    "type": "file",
                    "registration": {
                        # `omschrijving` "Attachment Informatieobjecttype other catalog":
                        "informatieobjecttype": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/cd6aeaf2-ca37-416f-b78c-1cc302f81a81",
                        "bronorganisatie": "111222333",
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
            completed=True,
        )
        submission_step = submission.steps[0]
        SubmissionFileAttachmentFactory.create(
            submission_step=submission_step,
            file_name="some-attachment.jpg",
            form_key="fileUpload",
            _component_configuration_path="components.0",
        )

        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        # Run the registration
        plugin.register_submission(
            submission,
            {
                "version": 1,
                "objects_api_group": self.objects_api_group,
                "objecttype": UUID("8faed0fa-7864-4409-aa6d-533a37616a9e"),
                "objecttype_version": 1,
                "update_existing_object": False,
                "auth_attribute_path": [],
            },
        )

        with get_documents_client(self.objects_api_group) as documents_client:
            attachment_document = documents_client.get(
                ObjectsAPISubmissionAttachment.objects.get().document_url
            ).json()

        # Check use of overridden settings
        self.assertEqual(
            attachment_document["informatieobjecttype"],
            "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/cd6aeaf2-ca37-416f-b78c-1cc302f81a81",
        )
        self.assertEqual(attachment_document["bronorganisatie"], "111222333")
        self.assertEqual(attachment_document["vertrouwelijkheidaanduiding"], "geheim")
        self.assertEqual(attachment_document["titel"], "A Custom Title")

    def test_submission_with_objects_api_backend_attachments_component_inside_fieldset_overwrites(
        self,
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
                                # `omschrijving` "Attachment Informatieobjecttype other catalog":
                                "informatieobjecttype": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/cd6aeaf2-ca37-416f-b78c-1cc302f81a81",
                                "bronorganisatie": "111222333",
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
            completed=True,
        )
        submission_step = submission.steps[0]
        SubmissionFileAttachmentFactory.create(
            submission_step=submission_step,
            file_name="some-attachment.jpg",
            form_key="fileUpload",
            _component_configuration_path="components.0.components.0",
        )

        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        # Run the registration
        plugin.register_submission(
            submission,
            {
                "version": 1,
                "objects_api_group": self.objects_api_group,
                "objecttype": UUID("8faed0fa-7864-4409-aa6d-533a37616a9e"),
                "objecttype_version": 1,
                "update_existing_object": False,
                "auth_attribute_path": [],
            },
        )

        with get_documents_client(self.objects_api_group) as documents_client:
            attachment_document = documents_client.get(
                ObjectsAPISubmissionAttachment.objects.get().document_url
            ).json()

        # Check use of overridden settings
        self.assertEqual(
            attachment_document["informatieobjecttype"],
            "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/cd6aeaf2-ca37-416f-b78c-1cc302f81a81",
        )
        self.assertEqual(attachment_document["bronorganisatie"], "111222333")
        self.assertEqual(attachment_document["vertrouwelijkheidaanduiding"], "geheim")
        self.assertEqual(attachment_document["titel"], "A Custom Title")

    @override_settings(ESCAPE_REGISTRATION_OUTPUT=True)
    def test_submission_with_objects_api_escapes_html(self):
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
        submission_step.form_step.slug = "test-slug"
        submission_step.form_step.save()

        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        # Run the registration
        result = plugin.register_submission(
            submission,
            {
                "version": 1,
                "objects_api_group": self.objects_api_group,
                "objecttype": UUID("8faed0fa-7864-4409-aa6d-533a37616a9e"),
                "objecttype_version": 1,
                "content_json": content_template,
                "upload_submission_csv": False,
                "update_existing_object": False,
                "auth_attribute_path": [],
            },
        )

        self.assertEqual(
            result["record"]["data"],
            {
                "summary": {
                    "test-slug": {
                        "voornaam": "&lt;script&gt;alert();&lt;/script&gt;",
                    },
                },
                "manual_variable": "&lt;script&gt;alert();&lt;/script&gt;",
            },
        )

    def test_submission_with_payment(self):
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
            form__payment_backend="demo",
            form__product__price=10,
        )
        SubmissionPaymentFactory.for_submission(
            submission=submission,
            status=PaymentStatus.completed,
            public_order_id="",
            provider_payment_id="123456",
        )

        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)
        result = plugin.register_submission(
            submission,
            {
                "version": 1,
                "objects_api_group": self.objects_api_group,
                "objecttype": UUID("8faed0fa-7864-4409-aa6d-533a37616a9e"),
                "objecttype_version": 1,
                "update_existing_object": False,
                "auth_attribute_path": [],
            },
        )

        self.assertEqual(
            result["record"]["data"]["payment"],
            {
                "completed": True,
                "amount": 10.00,
                "public_order_ids": [""],
                "payment_ids": ["123456"],
            },
        )

    def test_submission_with_auth_context_data(self):
        # skip document uploads
        self.objects_api_group.informatieobjecttype_submission_report = ""
        self.objects_api_group.save()
        submission = SubmissionFactory.create(
            completed=True,
            form__generate_minimal_setup=True,
            # simulate eherkenning bewindvoering, as that is most complex
            form__authentication_backend="demo",
            auth_info__plugin="demo",
            auth_info__is_eh_bewindvoering=True,
        )

        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)
        result = plugin.register_submission(
            submission,
            {
                "version": 1,
                "objects_api_group": self.objects_api_group,
                "objecttype": UUID("8faed0fa-7864-4409-aa6d-533a37616a9e"),
                "objecttype_version": 1,
                "informatieobjecttype_submission_report": "",
                "upload_submission_csv": False,
                "update_existing_object": False,
                "auth_attribute_path": [],
                "content_json": r"""{"auth": {% as_json variables.auth_context %}}""",
            },
        )

        # for the values, see openforms.authentication.tests.factories.AuthInfoFactory
        expected = {
            "source": "eherkenning",
            # from auth info factory
            "levelOfAssurance": "urn:etoegang:core:assurance-class:loa3",
            "representee": {
                "identifierType": "bsn",
                "identifier": "999991607",
            },
            "authorizee": {
                "legalSubject": {
                    "identifierType": "kvkNummer",
                    "identifier": "90002768",
                },
                "actingSubject": {
                    "identifierType": "opaque",
                    "identifier": (
                        "4B75A0EA107B3D36C82FD675B5B78CC2F181B22E33D85F2D4A5DA6345"
                        "2EE3018@2D8FF1EF10279BC2643F376D89835151"
                    ),
                },
            },
            "mandate": {
                "role": "bewindvoerder",
                "services": [
                    {
                        "id": "urn:etoegang:DV:00000001002308836000:services:9113",
                        "uuid": "34085d78-21aa-4481-a219-b28d7f3282fc",
                    }
                ],
            },
        }
        self.assertEqual(result["record"]["data"]["auth"], expected)

    def test_submission_with_auth_context_data_not_authenticated(self):
        # skip document uploads
        self.objects_api_group.informatieobjecttype_submission_report = ""
        self.objects_api_group.save()
        submission = SubmissionFactory.create(
            completed=True,
            form__generate_minimal_setup=True,
        )
        assert not submission.is_authenticated

        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        result = plugin.register_submission(
            submission,
            {
                "version": 1,
                "objects_api_group": self.objects_api_group,
                "objecttype": UUID("8faed0fa-7864-4409-aa6d-533a37616a9e"),
                "objecttype_version": 1,
                "informatieobjecttype_submission_report": "",
                "upload_submission_csv": False,
                "update_existing_object": False,
                "auth_attribute_path": [],
                "content_json": r"""{"auth": {% as_json variables.auth_context %}}""",
            },
        )

        self.assertEqual(result["record"]["data"]["auth"], None)

    @tag("gh-5034")
    def test_object_ownership_not_validated_if_new_object(self):
        submission = SubmissionFactory.from_components(
            [{"key": "textfield", "type": "textfield"}],
            completed_not_preregistered=True,
            form__registration_backend=PLUGIN_IDENTIFIER,
            form__registration_backend_options={
                "objects_api_group": self.objects_api_group.identifier,
                "version": 1,
                "objecttype": "8faed0fa-7864-4409-aa6d-533a37616a9e",
                "objecttype_version": 1,
                "update_existing_object": False,
                "auth_attribute_path": [],
            },
            submitted_data={"textfield": "test"},
            initial_data_reference="some ref",
        )

        try:
            pre_registration(submission.pk, PostSubmissionEvents.on_retry)
        except AssertionError:
            self.fail("Assertion should have passed.")


class V1HandlerTests(TestCase):
    """
    Test V1 registration backend without actual HTTP calls.

    Test the behaviour of the V1 registration handler for producing record data to send
    to the Objects API.
    """

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        cls.group = ObjectsAPIGroupConfigFactory(
            objecttypes_service__api_root="https://objecttypen.nl/api/v2/",
        )

    def test_cosign_info_available(self):
        now = timezone.now().isoformat()

        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "cosign",
                    "type": "cosign",
                    "validate": {"required": False},
                },
            ],
            completed=True,
            submitted_data={
                "cosign": "example@localhost",
            },
            cosign_complete=True,
            co_sign_data={
                "version": "v2",
                "plugin": "demo",
                "attribute": AuthAttribute.bsn,
                "value": "123456789",
                "cosign_date": now,
            },
        )

        ObjectsAPIRegistrationData.objects.create(submission=submission)
        v1_options: RegistrationOptionsV1 = {
            "objects_api_group": self.group,
            "version": 1,
            "objecttype": UUID("f3f1b370-97ed-4730-bc7e-ebb20c230377"),
            "objecttype_version": 1,
            "productaanvraag_type": "-dummy-",
            "update_existing_object": False,
            "auth_attribute_path": [],
            "content_json": textwrap.dedent(
                """
                {
                    "cosign_date": "{{ cosign_data.date.isoformat }}",
                    "cosign_bsn": "{{ cosign_data.bsn }}",
                    "cosign_kvk": "{{ cosign_data.kvk }}",
                    "cosign_pseudo": "{{ cosign_data.pseudo }}"
                }
                """
            ),
        }
        handler = ObjectsAPIV1Handler()

        record_data = handler.get_record_data(submission=submission, options=v1_options)

        data = record_data["data"]

        self.assertEqual(data["cosign_date"], now)
        self.assertEqual(data["cosign_bsn"], "123456789")
        self.assertEqual(data["cosign_kvk"], "")
        self.assertEqual(data["cosign_pseudo"], "")

    def test_cosign_info_not_available(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "cosign",
                    "type": "cosign",
                    "validate": {"required": False},
                },
            ],
            completed=True,
            submitted_data={
                "cosign": "example@localhost",
            },
            cosign_complete=False,
        )

        ObjectsAPIRegistrationData.objects.create(submission=submission)
        v1_options: RegistrationOptionsV1 = {
            "objects_api_group": self.group,
            "version": 1,
            "objecttype": UUID("f3f1b370-97ed-4730-bc7e-ebb20c230377"),
            "objecttype_version": 1,
            "productaanvraag_type": "-dummy-",
            "update_existing_object": False,
            "auth_attribute_path": [],
            "content_json": textwrap.dedent(
                """
                {
                    {% if cosign_data %}
                    "cosign_date": "{{ cosign_data.date }}",
                    "cosign_bsn": "{{ cosign_data.bsn }}",
                    "cosign_kvk": "{{ cosign_data.kvk }}",
                    "cosign_pseudo": "{{ cosign_data.pseudo }}"
                    {% endif %}
                }
                """
            ),
        }
        handler = ObjectsAPIV1Handler()

        record_data = handler.get_record_data(submission=submission, options=v1_options)

        self.assertEqual(record_data["data"], {})

    def test_cosign_info_no_cosign_date(self):
        """The cosign date might not be available on existing submissions."""

        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "cosign",
                    "type": "cosign",
                    "validate": {"required": False},
                },
            ],
            completed=True,
            submitted_data={
                "cosign": "example@localhost",
            },
            cosign_complete=True,
            co_sign_data={
                "version": "v2",
                "plugin": "demo",
                "attribute": AuthAttribute.bsn,
                "value": "123456789",
            },
        )

        ObjectsAPIRegistrationData.objects.create(submission=submission)
        v1_options: RegistrationOptionsV1 = {
            "objects_api_group": self.group,
            "version": 1,
            "objecttype": UUID("f3f1b370-97ed-4730-bc7e-ebb20c230377"),
            "objecttype_version": 1,
            "productaanvraag_type": "-dummy-",
            "update_existing_object": False,
            "auth_attribute_path": [],
            "content_json": textwrap.dedent(
                """
                {
                    "cosign_date": "{{ cosign_data.date }}"
                }
                """
            ),
        }
        handler = ObjectsAPIV1Handler()

        record_data = handler.get_record_data(submission=submission, options=v1_options)
        data = record_data["data"]

        self.assertEqual(data["cosign_date"], "")

    @tag("utrecht-243", "gh-4425")
    def test_payment_context_without_any_payment_attempts(self):
        submission = SubmissionFactory.create(
            completed=True,
            form__payment_backend="demo",
            form__product__price=10,
        )
        assert not submission.payments.exists()
        assert submission.price == 10
        ObjectsAPIRegistrationData.objects.create(submission=submission)
        options: RegistrationOptionsV1 = {
            "objects_api_group": self.group,
            "version": 1,
            "objecttype": UUID("f3f1b370-97ed-4730-bc7e-ebb20c230377"),
            "objecttype_version": 1,
            "productaanvraag_type": "-dummy-",
            "update_existing_object": False,
            "auth_attribute_path": [],
            "content_json": """{"amount": {{ payment.amount }}}""",
        }
        handler = ObjectsAPIV1Handler()

        record_data = handler.get_record_data(submission=submission, options=options)

        self.assertEqual(record_data["data"]["amount"], 10)
