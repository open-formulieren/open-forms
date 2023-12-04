import textwrap
from unittest.mock import patch

from django.core.exceptions import SuspiciousOperation
from django.test import TestCase, override_settings

import requests_mock
import tablib
from freezegun import freeze_time
from zgw_consumers.constants import APITypes

from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
)
from zgw_consumers_ext.tests.factories import ServiceFactory

from ..models import ObjectsAPIConfig
from ..plugin import PLUGIN_IDENTIFIER, ObjectsAPIRegistration


class JSONTemplatingTests(TestCase):
    maxDiff = None

    @requests_mock.Mocker()
    @freeze_time("2022-09-12")
    def test_default_template(self, m):
        submission = SubmissionFactory.from_components(
            components_list=[
                {"type": "textfield", "key": "voorNaam"},
                {"type": "textfield", "key": "achterNaam"},
            ],
            with_report=True,
            submitted_data={"voorNaam": "Jane", "achterNaam": "Doe"},
            form_definition_kwargs={"slug": "test-step-tralala"},
            auth_info__value="123456789",
        )
        SubmissionFileAttachmentFactory.create(submission_step=submission.steps[0])
        config = ObjectsAPIConfig(
            objects_service=ServiceFactory.build(
                api_root="https://objecten.nl/api/v1/",
                api_type=APITypes.orc,
            ),
            drc_service=ServiceFactory.build(
                api_root="https://documenten.nl/api/v1/",
                api_type=APITypes.drc,
            ),
            productaanvraag_type="terugbelnotitie",
        )
        m.post("https://objecten.nl/api/v1/objects", status_code=201, json={})
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)
        with (
            patch(
                "openforms.registrations.contrib.objects_api.models.ObjectsAPIConfig.get_solo",
                return_value=config,
            ),
            patch(
                "openforms.registrations.contrib.objects_api.plugin.create_report_document",
                return_value={"url": "http://oz.nl/pdf-report"},
            ),
            patch(
                "openforms.registrations.contrib.objects_api.plugin.create_attachment_document",
                return_value={"url": "http://oz.nl/attachment-url"},
            ),
        ):
            plugin.register_submission(
                submission,
                {
                    "objecttype": "https://objecttypen.nl/api/v1/objecttypes/1",
                    "objecttype_version": 300,
                },
            )

        posted_object = m.last_request.json()
        self.assertEqual(
            posted_object,
            {
                "type": "https://objecttypen.nl/api/v1/objecttypes/1",
                "record": {
                    "typeVersion": 300,
                    "data": {
                        "attachments": ["http://oz.nl/attachment-url"],
                        "bsn": "123456789",
                        "data": {
                            "test-step-tralala": {
                                "achterNaam": "Doe",
                                "voorNaam": "Jane",
                            }
                        },
                        "language_code": "nl",
                        "pdf_url": "http://oz.nl/pdf-report",
                        "submission_id": str(submission.uuid),
                        "type": "terugbelnotitie",
                        "payment": {
                            "completed": False,
                            "amount": "0",
                            "public_order_ids": "",
                        },
                    },
                    "startAt": "2022-09-12",
                },
            },
        )

    @requests_mock.Mocker()
    @freeze_time("2022-09-12")
    def test_custom_template(self, m):
        config = ObjectsAPIConfig(
            objects_service=ServiceFactory.build(
                api_root="https://objecten.nl/api/v1/",
                api_type=APITypes.orc,
            ),
            drc_service=ServiceFactory.build(
                api_root="https://documenten.nl/api/v1/",
                api_type=APITypes.drc,
            ),
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
                    "bijlagen": {% uploaded_attachment_urls %}
                }"""
            ),
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
        )
        SubmissionFileAttachmentFactory.create(submission_step=submission.steps[0])
        m.post("https://objecten.nl/api/v1/objects", status_code=201, json={})
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)
        with (
            patch(
                "openforms.registrations.contrib.objects_api.models.ObjectsAPIConfig.get_solo",
                return_value=config,
            ),
            patch(
                "openforms.registrations.contrib.objects_api.plugin.create_report_document",
                return_value={"url": "http://oz.nl/pdf-report"},
            ),
            patch(
                "openforms.registrations.contrib.objects_api.plugin.create_attachment_document",
                return_value={"url": "http://oz.nl/attachment-url"},
            ),
            patch(
                "openforms.registrations.contrib.objects_api.plugin.create_submission_export",
                return_value=tablib.Dataset(),
            ),
            patch(
                "openforms.registrations.contrib.objects_api.plugin.create_csv_document",
                return_value={"url": "http://oz.nl/csv-report"},
            ),
        ):
            plugin.register_submission(
                submission,
                {
                    "objecttype": "https://objecttypen.nl/api/v1/objecttypes/1",
                    "objecttype_version": 300,
                    "productaanvraag_type": "tralala-type",
                    "upload_submission_csv": True,
                    "informatieobjecttype_submission_csv": "http://oz.nl/informatieobjecttype/1",
                },
            )

        posted_object = m.last_request.json()
        self.assertEqual(
            posted_object,
            {
                "type": "https://objecttypen.nl/api/v1/objecttypes/1",
                "record": {
                    "typeVersion": 300,
                    "data": {
                        "bron": {
                            "naam": "Open Formulieren",
                            "kenmerk": str(submission.uuid),
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
                        "pdf": "http://oz.nl/pdf-report",
                        "csv": "http://oz.nl/csv-report",
                        "bijlagen": ["http://oz.nl/attachment-url"],
                    },
                    "startAt": "2022-09-12",
                },
            },
        )

    @override_settings(MAX_UNTRUSTED_JSON_PARSE_SIZE=10)
    def test_submission_with_objects_api_content_json_exceed_max_file_limit(self):
        submission = SubmissionFactory.create(with_report=True)
        config = ObjectsAPIConfig(
            objects_service=ServiceFactory.build(
                api_root="https://objecten.nl/api/v1/",
                api_type=APITypes.orc,
            ),
            drc_service=ServiceFactory.build(
                api_root="https://documenten.nl/api/v1/",
                api_type=APITypes.drc,
            ),
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
                "bijlagen": [
                {% for attachment in submission.attachments %}
                "{{ attachment }}"{% if not forloop.last %},{% endif %}
                {% endfor %}
                ]
                }"""
            ),
        )

        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)
        with (
            patch(
                "openforms.registrations.contrib.objects_api.models.ObjectsAPIConfig.get_solo",
                return_value=config,
            ),
            patch(
                "openforms.registrations.contrib.objects_api.plugin.create_report_document",
                return_value={"url": "http://of.nl/pdf-report"},
            ),
        ):
            with self.assertRaises(
                SuspiciousOperation,
                msg="Templated out content JSON exceeds the maximum size 10\xa0bytes (it is 398\xa0bytes).",
            ):
                plugin.register_submission(submission, {})

    def test_submission_with_objects_api_content_json_not_valid_json(self):
        submission = SubmissionFactory.create(with_report=True)
        config = ObjectsAPIConfig(
            objects_service=ServiceFactory.build(
                api_root="https://objecten.nl/api/v1/",
                api_type=APITypes.orc,
            ),
            drc_service=ServiceFactory.build(
                api_root="https://documenten.nl/api/v1/",
                api_type=APITypes.drc,
            ),
            content_json='{"key": "value",}',  # Invalid JSON,
        )
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        with (
            patch(
                "openforms.registrations.contrib.objects_api.models.ObjectsAPIConfig.get_solo",
                return_value=config,
            ),
            patch(
                "openforms.registrations.contrib.objects_api.plugin.create_report_document",
                return_value={"url": "http://of.nl/pdf-report"},
            ),
        ):
            with self.assertRaises(RuntimeError):
                plugin.register_submission(submission, {})
