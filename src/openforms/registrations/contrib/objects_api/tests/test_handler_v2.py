from pathlib import Path
from uuid import UUID

from django.test import TestCase, tag
from django.utils import timezone

from openforms.authentication.service import AuthAttribute
from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory
from openforms.submissions.tests.factories import (
    SubmissionFactory,
)

from ..models import ObjectsAPIRegistrationData
from ..registration_variables import PaymentAmount
from ..submission_registration import ObjectsAPIV2Handler
from ..typing import RegistrationOptionsV2

VCR_TEST_FILES = Path(__file__).parent / "files"


class V2HandlerTests(TestCase):
    """
    Test V2 registration backend without actual HTTP calls.

    Test the behaviour of the V2 registration handler for producing record data to send
    to the Objects API.
    """

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        cls.group = ObjectsAPIGroupConfigFactory(
            objecttypes_service__api_root="https://objecttypen.nl/api/v2/",
        )

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
                "location": {
                    "type": "Point",
                    "coordinates": [4.893164274470299, 52.36673378967122],
                },
            },
        )
        ObjectsAPIRegistrationData.objects.create(submission=submission)
        v2_options: RegistrationOptionsV2 = {
            "objects_api_group": self.group,
            "version": 2,
            "objecttype": UUID("f3f1b370-97ed-4730-bc7e-ebb20c230377"),
            "objecttype_version": 1,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "variables_mapping": [
                {
                    "variable_key": "location",
                    "target_path": ["pointCoordinates"],
                },
            ],
            "transform_to_list": [],
            "iot_attachment": "",
            "iot_submission_csv": "",
            "iot_submission_report": "",
        }
        handler = ObjectsAPIV2Handler()

        record_data = handler.get_record_data(submission=submission, options=v2_options)

        data = record_data["data"]
        self.assertEqual(
            data["pointCoordinates"],
            {
                "type": "Point",
                "coordinates": [4.893164274470299, 52.36673378967122],
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
        ObjectsAPIRegistrationData.objects.create(submission=submission)
        v2_options: RegistrationOptionsV2 = {
            "objects_api_group": self.group,
            "version": 2,
            "objecttype": UUID("f3f1b370-97ed-4730-bc7e-ebb20c230377"),
            "objecttype_version": 1,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "variables_mapping": [
                {
                    "variable_key": "fieldset.textfield",
                    "target_path": ["textfield"],
                },
            ],
            "transform_to_list": [],
            "iot_attachment": "",
            "iot_submission_csv": "",
            "iot_submission_report": "",
        }
        handler = ObjectsAPIV2Handler()

        record_data = handler.get_record_data(submission=submission, options=v2_options)
        data = record_data["data"]

        self.assertEqual(data["textfield"], "some_string")

    @tag("gh-4202")
    def test_hidden_component(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "textfield",
                    "type": "textfield",
                },
                {
                    "key": "hidden_number",
                    "type": "number",
                    "hidden": True,
                },
            ],
            completed=True,
            submitted_data={
                "textfield": "some_string",
            },
        )
        ObjectsAPIRegistrationData.objects.create(submission=submission)
        v2_options: RegistrationOptionsV2 = {
            "objects_api_group": self.group,
            "version": 2,
            "objecttype": UUID("f3f1b370-97ed-4730-bc7e-ebb20c230377"),
            "objecttype_version": 1,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "variables_mapping": [
                {
                    "variable_key": "textfield",
                    "target_path": ["textfield"],
                },
            ],
            "transform_to_list": [],
            "iot_attachment": "",
            "iot_submission_csv": "",
            "iot_submission_report": "",
        }
        handler = ObjectsAPIV2Handler()

        record_data = handler.get_record_data(submission=submission, options=v2_options)
        data = record_data["data"]

        self.assertEqual(data["textfield"], "some_string")

    def test_public_reference_available(self):
        submission = SubmissionFactory.create(
            with_public_registration_reference=True,
            public_registration_reference="OF-911",
            auth_info__plugin="irrelevant",
            auth_info__is_eh_bewindvoering=True,
        )
        ObjectsAPIRegistrationData.objects.create(submission=submission)
        v2_options: RegistrationOptionsV2 = {
            "objects_api_group": self.group,
            "version": 2,
            "objecttype": UUID("f3f1b370-97ed-4730-bc7e-ebb20c230377"),
            "objecttype_version": 1,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "variables_mapping": [
                {
                    "variable_key": "public_reference",
                    "target_path": ["of_nummer"],
                },
            ],
            "transform_to_list": [],
            "iot_attachment": "",
            "iot_submission_csv": "",
            "iot_submission_report": "",
        }
        handler = ObjectsAPIV2Handler()

        record_data = handler.get_record_data(submission=submission, options=v2_options)

        self.assertEqual(record_data["data"], {"of_nummer": "OF-911"})

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
        v2_options: RegistrationOptionsV2 = {
            "objects_api_group": self.group,
            "version": 2,
            "objecttype": UUID("f3f1b370-97ed-4730-bc7e-ebb20c230377"),
            "objecttype_version": 1,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "variables_mapping": [
                {
                    "variable_key": "cosign_data",
                    "target_path": ["cosign_data"],
                },
                {
                    "variable_key": "cosign_date",
                    "target_path": ["cosign_date"],
                },
                {
                    "variable_key": "cosign_bsn",
                    "target_path": ["cosign_bsn"],
                },
                {
                    "variable_key": "cosign_kvk",  # Will be empty string as bsn was used.
                    "target_path": ["cosign_kvk"],
                },
            ],
            "transform_to_list": [],
            "iot_attachment": "",
            "iot_submission_csv": "",
            "iot_submission_report": "",
        }
        handler = ObjectsAPIV2Handler()

        record_data = handler.get_record_data(submission=submission, options=v2_options)
        data = record_data["data"]

        self.assertEqual(
            data["cosign_data"],
            {
                "version": "v2",
                "plugin": "demo",
                "attribute": AuthAttribute.bsn,
                "value": "123456789",
                "cosign_date": now,
            },
        )
        self.assertEqual(data["cosign_date"], now)
        self.assertEqual(data["cosign_bsn"], "123456789")
        self.assertEqual(data["cosign_kvk"], "")

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
        v2_options: RegistrationOptionsV2 = {
            "objects_api_group": self.group,
            "version": 2,
            "objecttype": UUID("f3f1b370-97ed-4730-bc7e-ebb20c230377"),
            "objecttype_version": 1,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "variables_mapping": [
                {
                    "variable_key": "cosign_date",
                    "target_path": ["cosign_date"],
                },
                {
                    "variable_key": "cosign_bsn",
                    "target_path": ["cosign_bsn"],
                },
                {
                    "variable_key": "cosign_pseudo",  # Will be empty string as bsn was used.
                    "target_path": ["cosign_pseudo"],
                },
            ],
            "transform_to_list": [],
            "iot_attachment": "",
            "iot_submission_csv": "",
            "iot_submission_report": "",
        }
        handler = ObjectsAPIV2Handler()

        record_data = handler.get_record_data(submission=submission, options=v2_options)
        data = record_data["data"]

        self.assertEqual(data["cosign_date"], None)
        self.assertEqual(data["cosign_pseudo"], "")

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
        v2_options: RegistrationOptionsV2 = {
            "objects_api_group": self.group,
            "version": 2,
            "objecttype": UUID("f3f1b370-97ed-4730-bc7e-ebb20c230377"),
            "objecttype_version": 1,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "variables_mapping": [
                {
                    "variable_key": "cosign_date",
                    "target_path": ["cosign_date"],
                },
            ],
            "transform_to_list": [],
            "iot_attachment": "",
            "iot_submission_csv": "",
            "iot_submission_report": "",
        }
        handler = ObjectsAPIV2Handler()

        record_data = handler.get_record_data(submission=submission, options=v2_options)
        data = record_data["data"]

        self.assertEqual(data["cosign_date"], None)

    @tag("utrecht-243", "gh-4425")
    def test_payment_variable_without_any_payment_attempts(self):
        submission = SubmissionFactory.create(
            completed=True,
            form__payment_backend="demo",
            form__product__price=10,
        )
        assert not submission.payments.exists()
        assert submission.price == 10
        variable = PaymentAmount("dummy")

        value = variable.get_initial_value(submission=submission)

        self.assertEqual(value, 10.0)

    def test_auth_context_data_info_available(self):
        v2_options: RegistrationOptionsV2 = {
            "objects_api_group": self.group,
            "version": 2,
            "objecttype": UUID("f3f1b370-97ed-4730-bc7e-ebb20c230377"),
            "objecttype_version": 1,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "variables_mapping": [
                {
                    "variable_key": "auth_context",
                    "target_path": ["auth_context"],
                },
                {
                    "variable_key": "auth_context_source",
                    "target_path": ["authn", "middel"],
                },
                {
                    "variable_key": "auth_context_loa",
                    "target_path": ["authn", "loa"],
                },
                {
                    "variable_key": "auth_context_representee_identifier",
                    "target_path": ["authn", "vertegenwoordigde"],
                },
                {
                    "variable_key": "auth_context_representee_identifier_type",
                    "target_path": ["authn", "soort_vertegenwoordigde"],
                },
                {
                    "variable_key": "auth_context_legal_subject_identifier",
                    "target_path": ["authn", "gemachtigde"],
                },
                {
                    "variable_key": "auth_context_legal_subject_identifier_type",
                    "target_path": ["authn", "soort_gemachtigde"],
                },
                {
                    "variable_key": "auth_context_acting_subject_identifier",
                    "target_path": ["authn", "actor"],
                },
                {
                    "variable_key": "auth_context_acting_subject_identifier_type",
                    "target_path": ["authn", "soort_actor"],
                },
            ],
            "transform_to_list": [],
            "iot_attachment": "",
            "iot_submission_csv": "",
            "iot_submission_report": "",
        }
        handler = ObjectsAPIV2Handler()
        submission = SubmissionFactory.create(
            with_public_registration_reference=True,
            auth_info__plugin="irrelevant",
            auth_info__is_eh_bewindvoering=True,
        )
        ObjectsAPIRegistrationData.objects.create(submission=submission)

        record_data = handler.get_record_data(submission=submission, options=v2_options)

        data = record_data["data"]
        with self.subTest("full auth context"):
            expected_auth_context = {
                "source": "eherkenning",
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
                            "4B75A0EA107B3D36C82FD675B5B78CC2F"
                            "181B22E33D85F2D4A5DA63452EE3018@2"
                            "D8FF1EF10279BC2643F376D89835151"
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
            self.assertEqual(data["auth_context"], expected_auth_context)

        with self.subTest("individual auth context vars"):
            expected_obj = {
                "middel": "eherkenning",
                "loa": "urn:etoegang:core:assurance-class:loa3",
                "vertegenwoordigde": "999991607",
                "soort_vertegenwoordigde": "bsn",
                "gemachtigde": "90002768",
                "soort_gemachtigde": "kvkNummer",
                "actor": (
                    "4B75A0EA107B3D36C82FD675B5B78CC2F"
                    "181B22E33D85F2D4A5DA63452EE3018@2"
                    "D8FF1EF10279BC2643F376D89835151"
                ),
                "soort_actor": "opaque",
            }
            self.assertEqual(data["authn"], expected_obj)

    def test_auth_context_data_info_parts_missing_variants(self):
        v2_options: RegistrationOptionsV2 = {
            "objects_api_group": self.group,
            "version": 2,
            "objecttype": UUID("f3f1b370-97ed-4730-bc7e-ebb20c230377"),
            "objecttype_version": 1,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "variables_mapping": [
                {
                    "variable_key": "auth_context",
                    "target_path": ["auth_context"],
                },
                {
                    "variable_key": "auth_context_source",
                    "target_path": ["authn", "middel"],
                },
                {
                    "variable_key": "auth_context_loa",
                    "target_path": ["authn", "loa"],
                },
                {
                    "variable_key": "auth_context_representee_identifier",
                    "target_path": ["authn", "vertegenwoordigde"],
                },
                {
                    "variable_key": "auth_context_representee_identifier_type",
                    "target_path": ["authn", "soort_vertegenwoordigde"],
                },
                {
                    "variable_key": "auth_context_legal_subject_identifier",
                    "target_path": ["authn", "gemachtigde"],
                },
                {
                    "variable_key": "auth_context_legal_subject_identifier_type",
                    "target_path": ["authn", "soort_gemachtigde"],
                },
                {
                    "variable_key": "auth_context_acting_subject_identifier",
                    "target_path": ["authn", "actor"],
                },
                {
                    "variable_key": "auth_context_acting_subject_identifier_type",
                    "target_path": ["authn", "soort_actor"],
                },
            ],
            "transform_to_list": [],
            "iot_attachment": "",
            "iot_submission_csv": "",
            "iot_submission_report": "",
        }
        handler = ObjectsAPIV2Handler()

        cases = [
            (
                "anonymous",
                SubmissionFactory.create(
                    with_public_registration_reference=True,
                    auth_info=None,
                ),
                {
                    "middel": "",
                    "loa": "",
                    "vertegenwoordigde": "",
                    "soort_vertegenwoordigde": "",
                    "gemachtigde": "",
                    "soort_gemachtigde": "",
                    "actor": "",
                    "soort_actor": "",
                },
            ),
            (
                "digid",
                SubmissionFactory.create(
                    with_public_registration_reference=True,
                    auth_info__is_digid=True,
                ),
                {
                    "middel": "digid",
                    "loa": "urn:oasis:names:tc:SAML:2.0:ac:classes:MobileTwoFactorContract",
                    "vertegenwoordigde": "",
                    "soort_vertegenwoordigde": "",
                    "gemachtigde": "999991607",
                    "soort_gemachtigde": "bsn",
                    "actor": "",
                    "soort_actor": "",
                },
            ),
            (
                "digid-machtigen",
                SubmissionFactory.create(
                    with_public_registration_reference=True,
                    auth_info__is_digid_machtigen=True,
                ),
                {
                    "middel": "digid",
                    "loa": "urn:oasis:names:tc:SAML:2.0:ac:classes:MobileTwoFactorContract",
                    "vertegenwoordigde": "999991607",
                    "soort_vertegenwoordigde": "bsn",
                    "gemachtigde": "999999999",
                    "soort_gemachtigde": "bsn",
                    "actor": "",
                    "soort_actor": "",
                },
            ),
            (
                "eherkenning",
                SubmissionFactory.create(
                    with_public_registration_reference=True,
                    auth_info__is_eh=True,
                ),
                {
                    "middel": "eherkenning",
                    "loa": "urn:etoegang:core:assurance-class:loa3",
                    "vertegenwoordigde": "",
                    "soort_vertegenwoordigde": "",
                    "gemachtigde": "90002768",
                    "soort_gemachtigde": "kvkNummer",
                    "actor": (
                        "4B75A0EA107B3D36C82FD675B5B78CC2F"
                        "181B22E33D85F2D4A5DA63452EE3018@2"
                        "D8FF1EF10279BC2643F376D89835151"
                    ),
                    "soort_actor": "opaque",
                },
            ),
        ]

        for label, submission, expected in cases:
            with self.subTest(labe=label):
                ObjectsAPIRegistrationData.objects.create(submission=submission)

                record_data = handler.get_record_data(
                    submission=submission, options=v2_options
                )

                data = record_data["data"]
                self.assertEqual(data["authn"], expected)

    def test_addressNl_with_specific_target_paths(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "addressNl",
                    "type": "addressNL",
                    "label": "AddressNl component",
                },
            ],
            completed=True,
            submitted_data={
                "addressNl": {
                    "city": "",
                    "postcode": "1025 xm",
                    "streetName": "",
                    "houseLetter": "d",
                    "houseNumber": "73",
                    "secretStreetCity": "",
                    "houseNumberAddition": "2",
                },
            },
        )
        ObjectsAPIRegistrationData.objects.create(submission=submission)
        v2_options: RegistrationOptionsV2 = {
            "objects_api_group": self.group,
            "version": 2,
            "objecttype": UUID("f3f1b370-97ed-4730-bc7e-ebb20c230377"),
            "objecttype_version": 1,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "variables_mapping": [
                {
                    "variable_key": "addressNl",
                    "options": {
                        "postcode": ["addressNL", "postcode"],
                        "house_letter": ["addressNL", "houseLetter"],
                        "house_number": ["addressNL", "houseNumber"],
                        "house_number_addition": [
                            "addressNL",
                            "houseNumberAddition",
                        ],
                    },
                }
            ],
            "transform_to_list": [],
            "iot_attachment": "",
            "iot_submission_csv": "",
            "iot_submission_report": "",
        }
        handler = ObjectsAPIV2Handler()

        record_data = handler.get_record_data(submission=submission, options=v2_options)

        data = record_data["data"]
        self.assertEqual(
            data,
            {
                "addressNL": {
                    "postcode": "1025 xm",
                    "houseLetter": "d",
                    "houseNumber": "73",
                    "houseNumberAddition": "2",
                }
            },
        )

    def test_addressNl_with_specific_target_paths_mapped_and_empty_submitted_data(
        self,
    ):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "addressNl",
                    "type": "addressNL",
                    "label": "AddressNl component",
                },
            ],
            completed=True,
            submitted_data={
                "addressNl": {
                    "city": "",
                    "postcode": "1025 xm",
                    "streetName": "",
                    "houseLetter": "",
                    "houseNumber": "73",
                    "secretStreetCity": "",
                    "houseNumberAddition": "",
                },
            },
        )
        ObjectsAPIRegistrationData.objects.create(submission=submission)
        v2_options: RegistrationOptionsV2 = {
            "objects_api_group": self.group,
            "version": 2,
            "objecttype": UUID("f3f1b370-97ed-4730-bc7e-ebb20c230377"),
            "objecttype_version": 1,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "variables_mapping": [
                {
                    "variable_key": "addressNl",
                    "options": {
                        "postcode": ["addressNL", "postcode"],
                        "house_letter": ["addressNL", "houseLetter"],
                        "house_number": ["addressNL", "houseNumber"],
                        "house_number_addition": [
                            "addressNL",
                            "houseNumberAddition",
                        ],
                    },
                }
            ],
            "transform_to_list": [],
            "iot_attachment": "",
            "iot_submission_csv": "",
            "iot_submission_report": "",
        }
        handler = ObjectsAPIV2Handler()

        record_data = handler.get_record_data(submission=submission, options=v2_options)

        data = record_data["data"]
        self.assertEqual(
            data,
            {
                "addressNL": {
                    "postcode": "1025 xm",
                    "houseNumber": "73",
                }
            },
        )

    def test_addressNl_with_object_target_path(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "addressNl",
                    "type": "addressNL",
                    "label": "AddressNl component",
                },
            ],
            completed=True,
            submitted_data={
                "addressNl": {
                    "city": "",
                    "postcode": "1025 xm",
                    "streetName": "",
                    "houseLetter": "d",
                    "houseNumber": "73",
                    "secretStreetCity": "",
                    "houseNumberAddition": "2",
                },
            },
        )
        ObjectsAPIRegistrationData.objects.create(submission=submission)
        v2_options: RegistrationOptionsV2 = {
            "objects_api_group": self.group,
            "version": 2,
            "objecttype": UUID("f3f1b370-97ed-4730-bc7e-ebb20c230377"),
            "objecttype_version": 1,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "variables_mapping": [
                {"variable_key": "addressNl", "target_path": ["addressNL"]}
            ],
            "transform_to_list": [],
            "iot_attachment": "",
            "iot_submission_csv": "",
            "iot_submission_report": "",
        }
        handler = ObjectsAPIV2Handler()

        record_data = handler.get_record_data(submission=submission, options=v2_options)

        data = record_data["data"]

        self.assertEqual(
            data,
            {
                "addressNL": {
                    "postcode": "1025 xm",
                    "houseLetter": "d",
                    "houseNumber": "73",
                    "houseNumberAddition": "2",
                    "streetName": "",
                    "city": "",
                }
            },
        )

    def test_selectboxes_with_transform_to_list(self):
        submission = SubmissionFactory.from_components(
            [
                {"key": "selectBoxes1", "type": "selectboxes"},
                {"key": "selectBoxes2", "type": "selectboxes"},
            ],
            completed=True,
            submitted_data={
                "selectBoxes1": {"option1": True},
                "selectBoxes2": {"option2": True},
            },
        )
        ObjectsAPIRegistrationData.objects.create(submission=submission)
        v2_options: RegistrationOptionsV2 = {
            "objects_api_group": self.group,
            "version": 2,
            "objecttype": UUID("f3f1b370-97ed-4730-bc7e-ebb20c230377"),
            "objecttype_version": 1,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "variables_mapping": [
                {"variable_key": "selectBoxes1", "target_path": ["path1"]},
                {"variable_key": "selectBoxes2", "target_path": ["path2"]},
            ],
            "iot_attachment": "",
            "iot_submission_csv": "",
            "iot_submission_report": "",
            "transform_to_list": ["selectBoxes1"],
        }
        handler = ObjectsAPIV2Handler()

        record_data = handler.get_record_data(submission=submission, options=v2_options)

        data = record_data["data"]

        self.assertEqual(data, {"path1": ["option1"], "path2": {"option2": True}})

    def test_date_related_components(self):
        submission = SubmissionFactory.from_components(
            [
                {"key": "date", "type": "date"},
                {"key": "date_multiple", "type": "date", "multiple": True},
            ],
            completed=True,
            submitted_data={
                "date": "2000-01-01",
                "date_multiple": ["2000-01-01", "2025-08-11"],
            },
        )

        ObjectsAPIRegistrationData.objects.create(submission=submission)
        v2_options: RegistrationOptionsV2 = {
            "objects_api_group": self.group,
            "version": 2,
            "objecttype": UUID("f3f1b370-97ed-4730-bc7e-ebb20c230377"),
            "objecttype_version": 1,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "variables_mapping": [
                {"variable_key": "date", "target_path": ["path1"]},
                {"variable_key": "date_multiple", "target_path": ["path2"]},
            ],
            "iot_attachment": "",
            "iot_submission_csv": "",
            "iot_submission_report": "",
            "transform_to_list": [],
        }
        handler = ObjectsAPIV2Handler()

        record_data = handler.get_record_data(submission=submission, options=v2_options)

        data = record_data["data"]

        self.assertEqual(
            data,
            {
                "path1": "2000-01-01",
                "path2": ["2000-01-01", "2025-08-11"],
            },
        )
