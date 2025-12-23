import textwrap
from unittest.mock import patch
from uuid import UUID

from django.core.exceptions import SuspiciousOperation
from django.test import TestCase, override_settings, tag

from freezegun import freeze_time

from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory
from openforms.formio.constants import DataSrcOptions
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
)
from openforms.submissions.tests.mixins import SubmissionsMixin
from openforms.utils.tests.vcr import OFVCRMixin

from ..models import ObjectsAPIConfig
from ..plugin import PLUGIN_IDENTIFIER, ObjectsAPIRegistration
from ..typing import RegistrationOptionsV1


class JSONTemplatingTests(OFVCRMixin, TestCase):
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # Make sure to bring up the objects API docker compose in ``docker/``!
        cls.config_group = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True,
            organisatie_rsin="000000000",
        )

    def setUp(self):
        super().setUp()

        self.config = ObjectsAPIConfig(productaanvraag_type="terugbelnotitie")
        config_patcher = patch(
            "openforms.registrations.contrib.objects_api.models.ObjectsAPIConfig.get_solo",
            return_value=self.config,
        )
        self.mock_get_config = config_patcher.start()
        self.addCleanup(config_patcher.stop)

    @freeze_time("2022-09-12")
    def test_default_template(self):
        submission = SubmissionFactory.from_components(
            components_list=[
                {"type": "textfield", "key": "voorNaam"},
                {"type": "textfield", "key": "achterNaam"},
            ],
            with_report=True,
            submitted_data={"voorNaam": "Jane", "achterNaam": "Doe"},
            form_definition_kwargs={"slug": "test-step-tralala"},
            auth_info__value="123456789",
            completed=True,
            uuid=UUID("9b22e363-2268-4e9c-8d57-c1084d8a45a9"),
        )
        SubmissionFileAttachmentFactory.create(submission_step=submission.steps[0])
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)
        options: RegistrationOptionsV1 = {
            "version": 1,
            "objects_api_group": self.config_group,
            "objecttype": UUID("8faed0fa-7864-4409-aa6d-533a37616a9e"),
            "objecttype_version": 1,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "iot_submission_report": "",
            "informatieobjecttype_submission_report": (
                "http://localhost:8003/catalogi/api/v1/"
                "informatieobjecttypen/f2908f6f-aa07-42ef-8760-74c5234f2d25"
            ),
            "iot_attachment": "",
            "informatieobjecttype_attachment": (
                "http://localhost:8003/catalogi/api/v1/"
                "informatieobjecttypen/d1cfb1d8-8593-4814-919d-72e38e80388f"
            ),
            "iot_submission_csv": "",
        }

        result = plugin.register_submission(submission, options)

        assert result is not None

        with self.subTest("metadata"):
            self.assertEqual(
                result["type"],
                "http://objecttypes-web:8000/api/v2/objecttypes/8faed0fa-7864-4409-aa6d-533a37616a9e",
            )
            self.assertIn("uuid", result)

        with self.subTest("record data"):
            record = result["record"]
            attachments = record["data"]["attachments"]
            self.assertEqual(len(attachments), 1)
            self.assertTrue(
                attachments[0].startswith(
                    "http://localhost:8003/documenten/api/v1/enkelvoudiginformatieobjecten/"
                )
            )
            pdf_url = record["data"]["pdf_url"]
            self.assertTrue(
                pdf_url.startswith(
                    "http://localhost:8003/documenten/api/v1/enkelvoudiginformatieobjecten/"
                )
            )

            self.assertEqual(
                record,
                {
                    "typeVersion": 1,
                    "data": {
                        "attachments": attachments,
                        "bsn": "123456789",
                        "data": {
                            "test-step-tralala": {
                                "achterNaam": "Doe",
                                "voorNaam": "Jane",
                            }
                        },
                        "language_code": "nl",
                        "pdf_url": pdf_url,
                        "submission_id": "9b22e363-2268-4e9c-8d57-c1084d8a45a9",
                        "type": "terugbelnotitie",
                        "payment": {
                            "completed": False,
                            "amount": 0,
                            "public_order_ids": [],
                        },
                    },
                    "geometry": None,
                    "correctedBy": None,
                    "correctionFor": None,
                    "startAt": "2022-09-12",
                    "registrationAt": record["registrationAt"],
                    "endAt": None,
                    "index": 1,
                },
            )

    @freeze_time("2022-09-12")
    def test_custom_template(self):
        self.config.content_json = textwrap.dedent(
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
                "bijlagen": {% uploaded_attachment_urls %}
            }"""
        )

        submission = SubmissionFactory.from_components(
            components_list=[
                {"type": "textfield", "key": "voorNaam"},
                {"type": "textfield", "key": "achterNaam"},
            ],
            with_report=True,
            submitted_data={"voorNaam": "Jane", "achterNaam": "Doe"},
            form_definition_kwargs={"slug": "test-step-tralala"},
            auth_info__attribute="bsn",
            auth_info__value="123456789",
            completed=True,
            uuid=UUID("9b22e363-2268-4e9c-8d57-c1084d8a45a9"),
        )
        SubmissionFileAttachmentFactory.create(submission_step=submission.steps[0])
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)
        options: RegistrationOptionsV1 = {
            "version": 1,
            "objects_api_group": self.config_group,
            "objecttype": UUID("8faed0fa-7864-4409-aa6d-533a37616a9e"),
            "productaanvraag_type": "tralala-type",
            "objecttype_version": 1,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "iot_submission_report": "",
            "informatieobjecttype_submission_report": (
                "http://localhost:8003/catalogi/api/v1/"
                "informatieobjecttypen/f2908f6f-aa07-42ef-8760-74c5234f2d25"
            ),
            "iot_attachment": "",
            "informatieobjecttype_attachment": (
                "http://localhost:8003/catalogi/api/v1/"
                "informatieobjecttypen/d1cfb1d8-8593-4814-919d-72e38e80388f"
            ),
            "iot_submission_csv": "",
            "upload_submission_csv": True,
            "informatieobjecttype_submission_csv": (
                "http://localhost:8003/catalogi/api/v1/"
                "informatieobjecttypen/d1cfb1d8-8593-4814-919d-72e38e80388f"
            ),
        }

        result = plugin.register_submission(submission, options)

        assert result is not None

        with self.subTest("metadata"):
            self.assertEqual(
                result["type"],
                "http://objecttypes-web:8000/api/v2/objecttypes/8faed0fa-7864-4409-aa6d-533a37616a9e",
            )
            self.assertIn("uuid", result)

        with self.subTest("record data"):
            record = result["record"]
            attachments = record["data"]["bijlagen"]
            self.assertEqual(len(attachments), 1)
            self.assertTrue(
                attachments[0].startswith(
                    "http://localhost:8003/documenten/api/v1/enkelvoudiginformatieobjecten/"
                )
            )
            pdf = record["data"]["pdf"]
            self.assertTrue(
                pdf.startswith(
                    "http://localhost:8003/documenten/api/v1/enkelvoudiginformatieobjecten/"
                )
            )
            csv = record["data"]["csv"]
            self.assertTrue(
                csv.startswith(
                    "http://localhost:8003/documenten/api/v1/enkelvoudiginformatieobjecten/"
                )
            )

            self.assertEqual(
                record,
                {
                    "typeVersion": 1,
                    "data": {
                        "bron": {
                            "naam": "Open Formulieren",
                            "kenmerk": "9b22e363-2268-4e9c-8d57-c1084d8a45a9",
                        },
                        "type": "tralala-type",
                        "aanvraaggegevens": {
                            "test-step-tralala": {
                                "achterNaam": "Doe",
                                "voorNaam": "Jane",
                            }
                        },
                        "taal": "nl",
                        "betrokkenen": [
                            {
                                "inpBsn": "123456789",
                                "rolOmschrijvingGeneriek": "initiator",
                            }
                        ],
                        "pdf": pdf,
                        "csv": csv,
                        "bijlagen": attachments,
                    },
                    "geometry": None,
                    "correctedBy": None,
                    "correctionFor": None,
                    "startAt": "2022-09-12",
                    "registrationAt": record["registrationAt"],
                    "endAt": None,
                    "index": 1,
                },
            )

    @override_settings(MAX_UNTRUSTED_JSON_PARSE_SIZE=10)
    def test_submission_with_objects_api_content_json_exceed_max_file_limit(self):
        self.config.content_json = textwrap.dedent(
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
            "bijlagen": [
            {% for attachment in submission.attachments %}
            "{{ attachment }}"{% if not forloop.last %},{% endif %}
            {% endfor %}
            ]
            }"""
        )
        submission = SubmissionFactory.create(with_report=True)
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)
        options: RegistrationOptionsV1 = {
            "version": 1,
            "objects_api_group": self.config_group,
            "objecttype": UUID("8faed0fa-7864-4409-aa6d-533a37616a9e"),
            "objecttype_version": 1,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "iot_submission_report": "",
            "informatieobjecttype_submission_report": (
                "http://localhost:8003/catalogi/api/v1/"
                "informatieobjecttypen/f2908f6f-aa07-42ef-8760-74c5234f2d25"
            ),
            "iot_attachment": "",
            "informatieobjecttype_attachment": (
                "http://localhost:8003/catalogi/api/v1/"
                "informatieobjecttypen/d1cfb1d8-8593-4814-919d-72e38e80388f"
            ),
            "iot_submission_csv": "",
        }

        with self.assertRaises(
            SuspiciousOperation,
            msg="Templated out content JSON exceeds the maximum size 10\xa0bytes (it is 398\xa0bytes).",
        ):
            plugin.register_submission(submission, options)

    def test_submission_with_objects_api_content_json_not_valid_json(self):
        self.config.content_json = ('{"key": "value",}',)  # Invalid JSON,
        submission = SubmissionFactory.create(with_report=True)
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)
        options: RegistrationOptionsV1 = {
            "version": 1,
            "objects_api_group": self.config_group,
            "objecttype": UUID("8faed0fa-7864-4409-aa6d-533a37616a9e"),
            "objecttype_version": 1,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "iot_submission_report": "",
            "informatieobjecttype_submission_report": (
                "http://localhost:8003/catalogi/api/v1/"
                "informatieobjecttypen/f2908f6f-aa07-42ef-8760-74c5234f2d25"
            ),
            "iot_attachment": "",
            "informatieobjecttype_attachment": (
                "http://localhost:8003/catalogi/api/v1/"
                "informatieobjecttypen/d1cfb1d8-8593-4814-919d-72e38e80388f"
            ),
            "iot_submission_csv": "",
        }

        with self.assertRaises(RuntimeError):
            plugin.register_submission(submission, options)


class JSONTemplatingRegressionTests(OFVCRMixin, SubmissionsMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # Make sure to bring up the objects API docker compose in ``docker/``!
        cls.config_group = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True,
            organisatie_rsin="000000000",
        )

    def setUp(self):
        super().setUp()

        self.config = ObjectsAPIConfig()
        config_patcher = patch(
            "openforms.registrations.contrib.objects_api.models.ObjectsAPIConfig.get_solo",
            return_value=self.config,
        )
        self.mock_get_config = config_patcher.start()
        self.addCleanup(config_patcher.stop)

    @tag("dh-673")
    def test_object_nulls_regression(self):
        self.config.content_json = "{% json_summary %}"
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "type": "radio",
                    "key": "radio",
                    "label": "Radio",
                    "values": [
                        {"label": "1", "value": "1"},
                        {"label": "2", "value": "2"},
                    ],
                    "defaultValue": None,
                    "validate": {"required": True},
                    "openForms": {"dataSrc": DataSrcOptions.manual},
                },
                {
                    "type": "textfield",
                    "key": "tekstveld",
                    "label": "Tekstveld",
                    "hidden": True,
                    "validate": {"required": True},
                    "conditional": {"eq": "1", "show": True, "when": "radio"},
                    "defaultValue": None,
                    "clearOnHide": True,
                },
                {
                    "type": "currency",
                    "currency": "EUR",
                    "key": "bedrag",
                    "label": "Bedrag",
                    "hidden": True,
                    "validate": {"required": True},
                    "conditional": {"eq": "1", "show": True, "when": "radio"},
                    "defaultValue": None,
                    "clearOnHide": True,
                },
            ],
            with_report=True,
            submitted_data={"radio": "2"},
            form_definition_kwargs={"slug": "stepwithnulls"},
        )
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)
        options: RegistrationOptionsV1 = {
            "version": 1,
            "objects_api_group": self.config_group,
            "objecttype": UUID("8faed0fa-7864-4409-aa6d-533a37616a9e"),
            "objecttype_version": 1,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "iot_submission_report": "",
            "informatieobjecttype_submission_report": "",
            "iot_attachment": "",
            "informatieobjecttype_attachment": "",
            "iot_submission_csv": "",
            "upload_submission_csv": False,
        }

        result = plugin.register_submission(submission, options)

        assert result is not None
        record_data = result["record"]["data"]
        # for missing values, the empty value (depending on component type) must be used
        # Note that the input data was validated against the hidden/visible and
        # clearOnHide state - absence of the data implies that the component was not
        # visible and its data was cleared (otherwise the value *would* have been sent
        # along and be present).
        self.assertEqual(
            record_data,
            {
                "stepwithnulls": {
                    "radio": "2",
                    "tekstveld": "",
                    "bedrag": None,
                },
            },
        )

    @tag("dh-673", "gh-4140")
    @override_settings(DISABLE_SENDING_HIDDEN_FIELDS=True)
    def test_opt_out_of_sending_hidden_fields(self):
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "type": "radio",
                    "key": "radio",
                    "label": "Radio",
                    "values": [
                        {"label": "1", "value": "1"},
                        {"label": "2", "value": "2"},
                    ],
                    "defaultValue": None,
                    "validate": {"required": True},
                    "openForms": {"dataSrc": "manual"},
                },
                {
                    "type": "textfield",
                    "key": "tekstveld",
                    "label": "Tekstveld",
                    "hidden": True,
                    "validate": {"required": True},
                    "conditional": {"eq": "1", "show": True, "when": "radio"},
                    "defaultValue": None,
                    "clearOnHide": True,
                },
                {
                    "type": "currency",
                    "currency": "EUR",
                    "key": "bedrag",
                    "label": "Bedrag",
                    "hidden": True,
                    "validate": {"required": True},
                    "conditional": {"eq": "1", "show": True, "when": "radio"},
                    "defaultValue": None,
                    "clearOnHide": True,
                },
                {
                    "type": "fieldset",
                    "key": "fieldsetNoVisibleChildren",
                    "label": "A container without visible children",
                    "hidden": True,
                    "components": [
                        {
                            "type": "textfield",
                            "key": "input7",
                            "label": "Input 7",
                            "hidden": True,
                        }
                    ],
                },
            ],
            with_report=True,
            submitted_data={"radio": "2"},
            form_definition_kwargs={"slug": "stepwithnulls"},
        )
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)
        options: RegistrationOptionsV1 = {
            "version": 1,
            "objects_api_group": self.config_group,
            "objecttype": UUID("8faed0fa-7864-4409-aa6d-533a37616a9e"),
            "objecttype_version": 1,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "iot_submission_report": "",
            "informatieobjecttype_submission_report": "",
            "iot_attachment": "",
            "informatieobjecttype_attachment": "",
            "iot_submission_csv": "",
            "upload_submission_csv": False,
            "content_json": "{% json_summary %}",
        }

        result = plugin.register_submission(submission, options)

        assert result is not None
        record_data = result["record"]["data"]
        # for missing values, the empty value (depending on component type) must be used
        # Note that the input data was validated against the hidden/visible and
        # clearOnHide state - absence of the data implies that the component was not
        # visible and its data was cleared (otherwise the value *would* have been sent
        # along and be present).
        self.assertEqual(
            record_data,
            {
                "stepwithnulls": {"radio": "2"},
            },
        )
