import textwrap
from unittest.mock import patch
from uuid import UUID

from django.core.exceptions import SuspiciousOperation
from django.test import TestCase, override_settings, tag

import requests_mock
import tablib
from freezegun import freeze_time

from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory
from openforms.formio.constants import DataSrcOptions
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
)
from openforms.submissions.tests.mixins import SubmissionsMixin

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
            completed=True,
        )
        SubmissionFileAttachmentFactory.create(submission_step=submission.steps[0])
        config = ObjectsAPIConfig(
            productaanvraag_type="terugbelnotitie",
        )
        config_group = ObjectsAPIGroupConfigFactory.create(
            objecttypes_service__api_root="https://objecttypen.nl/api/v1/",
            objects_service__api_root="https://objecten.nl/api/v1/",
            drc_service__api_root="https://documenten.nl/api/v1/",
        )
        m.post("https://objecten.nl/api/v1/objects", status_code=201, json={})
        m.get(
            "https://objecttypen.nl/api/v1/objecttypes/f3f1b370-97ed-4730-bc7e-ebb20c230377",
            json={
                "url": "https://objecttypen.nl/api/v1/objecttypes/f3f1b370-97ed-4730-bc7e-ebb20c230377"
            },
            status_code=200,
        )
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)
        with (
            patch(
                "openforms.registrations.contrib.objects_api.models.ObjectsAPIConfig.get_solo",
                return_value=config,
            ),
            patch(
                "openforms.registrations.contrib.objects_api.submission_registration.create_report_document",
                return_value={"url": "http://oz.nl/pdf-report"},
            ),
            patch(
                "openforms.registrations.contrib.objects_api.submission_registration.create_attachment_document",
                return_value={"url": "http://oz.nl/attachment-url"},
            ),
        ):
            plugin.register_submission(
                submission,
                {
                    "version": 1,
                    "objects_api_group": config_group,
                    "objecttype": UUID("f3f1b370-97ed-4730-bc7e-ebb20c230377"),
                    "objecttype_version": 300,
                    "informatieobjecttype_submission_report": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
                    "informatieobjecttype_attachment": "https://catalogi.nl/api/v1/informatieobjecttypen/2",
                    "update_existing_object": False,
                },
            )

        posted_object = m.last_request.json()
        self.assertEqual(
            posted_object,
            {
                "type": "https://objecttypen.nl/api/v1/objecttypes/f3f1b370-97ed-4730-bc7e-ebb20c230377",
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
                            "amount": 0,
                            "public_order_ids": [],
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
        config_group = ObjectsAPIGroupConfigFactory.create(
            objecttypes_service__api_root="https://objecttypen.nl/api/v1/",
            objects_service__api_root="https://objecten.nl/api/v1/",
            drc_service__api_root="https://documenten.nl/api/v1/",
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
        )
        SubmissionFileAttachmentFactory.create(submission_step=submission.steps[0])
        m.post("https://objecten.nl/api/v1/objects", status_code=201, json={})
        m.get(
            "https://objecttypen.nl/api/v1/objecttypes/f3f1b370-97ed-4730-bc7e-ebb20c230377",
            json={
                "url": "https://objecttypen.nl/api/v1/objecttypes/f3f1b370-97ed-4730-bc7e-ebb20c230377"
            },
            status_code=200,
        )
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)
        with (
            patch(
                "openforms.registrations.contrib.objects_api.models.ObjectsAPIConfig.get_solo",
                return_value=config,
            ),
            patch(
                "openforms.registrations.contrib.objects_api.submission_registration.create_report_document",
                return_value={"url": "http://oz.nl/pdf-report"},
            ),
            patch(
                "openforms.registrations.contrib.objects_api.submission_registration.create_attachment_document",
                return_value={"url": "http://oz.nl/attachment-url"},
            ),
            patch(
                "openforms.registrations.contrib.objects_api.submission_registration.create_submission_export",
                return_value=tablib.Dataset(),
            ),
            patch(
                "openforms.registrations.contrib.objects_api.submission_registration.create_csv_document",
                return_value={"url": "http://oz.nl/csv-report"},
            ),
        ):
            plugin.register_submission(
                submission,
                {
                    "version": 1,
                    "objects_api_group": config_group,
                    "objecttype": UUID("f3f1b370-97ed-4730-bc7e-ebb20c230377"),
                    "objecttype_version": 300,
                    "productaanvraag_type": "tralala-type",
                    "upload_submission_csv": True,
                    "update_existing_object": False,
                    "informatieobjecttype_submission_csv": "http://oz.nl/informatieobjecttype/1",
                    "informatieobjecttype_submission_report": "http://oz.nl/informatieobjecttype/2",
                    "informatieobjecttype_attachment": "http://oz.nl/informatieobjecttype/3",
                },
            )

        posted_object = m.last_request.json()
        self.assertEqual(
            posted_object,
            {
                "type": "https://objecttypen.nl/api/v1/objecttypes/f3f1b370-97ed-4730-bc7e-ebb20c230377",
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

        config_group = ObjectsAPIGroupConfigFactory.create(
            objecttypes_service__api_root="https://objecttypen.nl/api/v1/",
            objects_service__api_root="https://objecten.nl/api/v1/",
            drc_service__api_root="https://documenten.nl/api/v1/",
        )

        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)
        with (
            patch(
                "openforms.registrations.contrib.objects_api.models.ObjectsAPIConfig.get_solo",
                return_value=config,
            ),
            patch(
                "openforms.registrations.contrib.objects_api.submission_registration.create_report_document",
                return_value={"url": "http://of.nl/pdf-report"},
            ),
        ):
            with self.assertRaises(
                SuspiciousOperation,
                msg="Templated out content JSON exceeds the maximum size 10\xa0bytes (it is 398\xa0bytes).",
            ):
                plugin.register_submission(
                    submission,
                    {
                        "version": 1,
                        "objects_api_group": config_group,
                        "objecttype": UUID("f3f1b370-97ed-4730-bc7e-ebb20c230377"),
                        "objecttype_version": 300,
                    },
                )

    def test_submission_with_objects_api_content_json_not_valid_json(self):
        submission = SubmissionFactory.create(with_report=True)
        config = ObjectsAPIConfig(
            content_json='{"key": "value",}',  # Invalid JSON,
        )
        config_group = ObjectsAPIGroupConfigFactory.create(
            objecttypes_service__api_root="https://objecttypen.nl/api/v1/",
            objects_service__api_root="https://objecten.nl/api/v1/",
            drc_service__api_root="https://documenten.nl/api/v1/",
        )
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        with (
            patch(
                "openforms.registrations.contrib.objects_api.models.ObjectsAPIConfig.get_solo",
                return_value=config,
            ),
            patch(
                "openforms.registrations.contrib.objects_api.submission_registration.create_report_document",
                return_value={"url": "http://of.nl/pdf-report"},
            ),
        ):
            with self.assertRaises(RuntimeError):
                plugin.register_submission(
                    submission,
                    {
                        "version": 1,
                        "objects_api_group": config_group,
                        "objecttype": UUID("f3f1b370-97ed-4730-bc7e-ebb20c230377"),
                        "objecttype_version": 300,
                    },
                )


class JSONTemplatingRegressionTests(SubmissionsMixin, TestCase):
    @tag("dh-673")
    @requests_mock.Mocker()
    def test_object_nulls_regression(self, m):
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
        config = ObjectsAPIConfig(
            content_json="{% json_summary %}",
        )
        config_group = ObjectsAPIGroupConfigFactory.create(
            objecttypes_service__api_root="https://objecttypen.nl/api/v1/",
        )
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)
        prefix = "openforms.registrations.contrib.objects_api"

        m.get(
            "https://objecttypen.nl/api/v1/objecttypes/f3f1b370-97ed-4730-bc7e-ebb20c230377",
            json={
                "url": "https://objecttypen.nl/api/v1/objecttypes/f3f1b370-97ed-4730-bc7e-ebb20c230377"
            },
            status_code=200,
        )

        with (
            patch(
                f"{prefix}.models.ObjectsAPIConfig.get_solo",
                return_value=config,
            ),
            patch(f"{prefix}.plugin.get_objects_client") as mock_objects_client,
        ):
            _objects_client = mock_objects_client.return_value.__enter__.return_value
            _objects_client.create_object.return_value = {"dummy": "response"}

            plugin.register_submission(
                submission,
                {
                    "version": 1,
                    "objects_api_group": config_group,
                    "objecttype": UUID("f3f1b370-97ed-4730-bc7e-ebb20c230377"),
                    "objecttype_version": 300,
                    # skip document uploads
                    "informatieobjecttype_submission_report": "",
                    "upload_submission_csv": False,
                    "update_existing_object": False,
                    "informatieobjecttype_attachment": "",
                },
            )

        _objects_client.create_object.mock_assert_called_once()
        record_data = _objects_client.create_object.call_args[1]["record_data"]["data"]
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
    @requests_mock.Mocker()
    def test_opt_out_of_sending_hidden_fields(self, m):
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
        config = ObjectsAPIGroupConfigFactory.create(
            objecttypes_service__api_root="https://objecttypen.nl/api/v1/",
        )
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        m.get(
            "https://objecttypen.nl/api/v1/objecttypes/f3f1b370-97ed-4730-bc7e-ebb20c230377",
            json={
                "url": "https://objecttypen.nl/api/v1/objecttypes/f3f1b370-97ed-4730-bc7e-ebb20c230377"
            },
            status_code=200,
        )

        with (
            patch(
                "openforms.registrations.contrib.objects_api.plugin.get_objects_client"
            ) as mock_objects_client,
        ):
            _objects_client = mock_objects_client.return_value.__enter__.return_value
            _objects_client.create_object.return_value = {"dummy": "response"}

            plugin.register_submission(
                submission,
                {
                    "objects_api_group": config,
                    "version": 1,
                    "objecttype": UUID("f3f1b370-97ed-4730-bc7e-ebb20c230377"),
                    "objecttype_version": 300,
                    # skip document uploads
                    "informatieobjecttype_submission_report": "",
                    "upload_submission_csv": False,
                    "update_existing_object": False,
                    "informatieobjecttype_attachment": "",
                    "content_json": "{% json_summary %}",
                },
            )

        _objects_client.create_object.mock_assert_called_once()
        record_data = _objects_client.create_object.call_args[1]["record_data"]["data"]
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
