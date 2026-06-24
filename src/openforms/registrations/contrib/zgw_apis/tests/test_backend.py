import json
import textwrap
from datetime import UTC, date, datetime, time
from decimal import Decimal
from unittest import expectedFailure
from unittest.mock import patch
from uuid import uuid4

from django.test import TestCase, override_settings, tag

from privates.test import temp_private_root
from unittest_parametrize import ParametrizedTestCase, parametrize
from zgw_consumers.constants import AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from openforms.authentication.constants import AuthAttribute
from openforms.authentication.tests.factories import RegistratorInfoFactory
from openforms.config.constants import FamilyMembersDataAPIChoices
from openforms.config.models import GlobalConfiguration
from openforms.contrib.haal_centraal.constants import BRPVersions
from openforms.contrib.haal_centraal.models import HaalCentraalConfig
from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory
from openforms.contrib.zgw.clients.zaken import CRS_HEADERS, ZakenClient
from openforms.forms.tests.factories import FormVariableFactory
from openforms.prefill.contrib.family_members.plugin import (
    PLUGIN_IDENTIFIER as FM_PLUGIN_IDENTIFIER,
)
from openforms.prefill.service import prefill_variables
from openforms.submissions.constants import PostSubmissionEvents
from openforms.submissions.models import Submission, SubmissionStep
from openforms.submissions.tasks import pre_registration
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
)
from openforms.utils.tests.feature_flags import enable_feature_flag
from openforms.utils.tests.vcr import OFVCRMixin

from ....constants import RegistrationAttribute
from ....exceptions import RegistrationFailed
from ..client import get_documents_client, get_zaken_client
from ..constants import SummaryDocumentChoices
from ..plugin import PLUGIN_IDENTIFIER, ZGWRegistration
from ..typing import RegistrationOptions
from .factories import ZGWApiGroupConfigFactory

NP_INITIATOR_FIELDS = [
    {
        "key": "achternaam",
        "type": "textfield",
        "label": "achternaam",
        "registration": {
            "attribute": RegistrationAttribute.initiator_geslachtsnaam,
        },
    },
    {
        "key": "postcode",
        "type": "textfield",
        "label": "postcode",
        "registration": {
            "attribute": RegistrationAttribute.initiator_postcode,
        },
    },
    {
        "key": "woonplaats",
        "type": "textfield",
        "label": "woonplaats",
        "registration": {"attribute": RegistrationAttribute.initiator_woonplaats},
    },
    {
        "key": "straat",
        "type": "textfield",
        "label": "straat",
        "registration": {
            "attribute": RegistrationAttribute.initiator_straat,
        },
    },
    {
        "key": "huisnummer",
        "type": "number",
        "label": "huisnummer",
        "registration": {
            "attribute": RegistrationAttribute.initiator_huisnummer,
        },
    },
]
NP_INITIATOR_DATA = {
    "achternaam": "Willemse",
    "postcode": "1000 AA",
    "woonplaats": "Ketnet",
    "straat": "Samsonweg",
    "huisnummer": 101,
}


def _run_preregistration(
    submission: Submission,
    plugin: ZGWRegistration,
    options: RegistrationOptions,
) -> None:
    pre_registration_result = plugin.pre_register_submission(submission, options)
    assert isinstance(submission.registration_result, dict)
    assert isinstance(pre_registration_result.data, dict)
    submission.registration_result.update(pre_registration_result.data)
    submission.save()


@temp_private_root()
class ZGWBackendVCRTests(OFVCRMixin, ParametrizedTestCase, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.zgw_group = ZGWApiGroupConfigFactory.create(
            for_test_docker_compose=True,
            organisatie_rsin="000000000",
        )

    def test_submission_has_reference_after_pre_registration(self):
        submission = SubmissionFactory.create(
            form__registration_backend="zgw-create-zaak",
            form__registration_backend_options={
                "zgw_api_group": self.zgw_group.pk,
                "catalogue": {"domain": "TEST", "rsin": "000000000"},
                "case_type_identification": "ZT-001",
                "document_type_description": "Attachment Informatieobjecttype",
                "objects_api_group": None,
            },
            completed_not_preregistered=True,
            # Pin to a known case & document type version
            completed_on=datetime(2024, 11, 9, 15, 30, 0).replace(tzinfo=UTC),
        )
        assert submission.public_registration_reference == ""

        pre_registration(submission.id, PostSubmissionEvents.on_completion)

        submission.refresh_from_db()
        self.assertEqual(
            submission.public_registration_reference,
            submission.registration_result["zaak"]["identificatie"],
        )

    def test_submission_has_reference_after_pre_registration_use_of_generator(self):
        zgw_group = ZGWApiGroupConfigFactory.create(
            for_test_docker_compose=True,
            organisatie_rsin="000000000",
            use_generated_zaaknummer=False,
        )
        submission = SubmissionFactory.create(
            form__registration_backend="zgw-create-zaak",
            form__registration_backend_options={
                "zgw_api_group": zgw_group.pk,
                "catalogue": {"domain": "TEST", "rsin": "000000000"},
                "case_type_identification": "ZT-001",
                "document_type_description": "Attachment Informatieobjecttype",
                "objects_api_group": None,
            },
            completed_not_preregistered=True,
            # Pin to a known case & document type version
            completed_on=datetime(2024, 11, 9, 15, 30, 0).replace(tzinfo=UTC),
        )
        assert submission.public_registration_reference == ""

        pre_registration(submission.id, PostSubmissionEvents.on_completion)

        # check that the identification is explicitly provided in the call and what
        # the Zaken API used + returned.
        create_zaak_request = next(
            request
            for request in self.cassette.requests
            if request.method == "POST" and request.path.endswith("/zaken/api/v1/zaken")
        )
        of_identification = json.loads(create_zaak_request.body)["identificatie"]
        submission.refresh_from_db()
        self.assertEqual(submission.public_registration_reference, of_identification)
        self.assertEqual(
            submission.registration_result["zaak"]["identificatie"], of_identification
        )

    @tag("gh-4337")
    def test_zaakomschrijving_includes_form_name(self):
        with self.subTest("Short name that is not truncated"):
            submission1 = SubmissionFactory.create(
                form__name="Short name",
                form__registration_backend="zgw-create-zaak",
                form__registration_backend_options={
                    "zgw_api_group": self.zgw_group.pk,
                    "catalogue": {"domain": "TEST", "rsin": "000000000"},
                    "case_type_identification": "ZT-001",
                    "document_type_description": "Attachment Informatieobjecttype",
                    "objects_api_group": None,
                },
                completed_not_preregistered=True,
                # Pin to a known case & document type version
                completed_on=datetime(2024, 11, 9, 15, 30, 0).replace(tzinfo=UTC),
            )
            assert submission1.public_registration_reference == ""

            pre_registration(submission1.id, PostSubmissionEvents.on_completion)

            submission1.refresh_from_db()
            zaak = submission1.registration_result["zaak"]
            self.assertEqual(zaak["omschrijving"], "Short name")

        with self.subTest("Long name that is truncated"):
            submission2 = SubmissionFactory.create(
                form__name=(
                    "Long name that will most definitely be truncated to 80 characters "
                    "right???????????"
                ),
                form__registration_backend="zgw-create-zaak",
                form__registration_backend_options={
                    "zgw_api_group": self.zgw_group.pk,
                    "catalogue": {"domain": "TEST", "rsin": "000000000"},
                    "case_type_identification": "ZT-001",
                    "document_type_description": "Attachment Informatieobjecttype",
                    "objects_api_group": None,
                },
                completed_not_preregistered=True,
                # Pin to a known case & document type version
                completed_on=datetime(2024, 11, 9, 15, 30, 0).replace(tzinfo=UTC),
            )
            assert submission2.public_registration_reference == ""

            pre_registration(submission2.id, PostSubmissionEvents.on_completion)

            submission2.refresh_from_db()
            zaak = submission2.registration_result["zaak"]
            self.assertEqual(
                zaak["omschrijving"],
                "Long name that will most definitely be truncated to 80 characters "
                "right????????\u2026",
            )

    @override_settings(LANGUAGE_CODE="en")
    def test_submission_with_registrator(self):
        submission = SubmissionFactory.from_components(
            NP_INITIATOR_FIELDS,
            submitted_data=NP_INITIATOR_DATA,
            bsn="111222333",
            completed=True,
            # Pin to a known case & document type version
            completed_on=datetime(2024, 6, 9, 15, 30, 0).replace(tzinfo=UTC),
            with_report=True,
        )
        RegistratorInfoFactory.create(submission=submission, value="123456782")
        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "case_type_identification": "ZT-001",
            "document_type_description": "Attachment Informatieobjecttype",
            "organisatie_rsin": "000000000",
            "zaak_vertrouwelijkheidaanduiding": "openbaar",
            "doc_vertrouwelijkheidaanduiding": "openbaar",
            "medewerker_roltype": "Baliemedewerker",
            "objects_api_group": None,
            "product_url": "",
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
            "summary_documents": [SummaryDocumentChoices.pdf],
        }
        plugin = ZGWRegistration("zgw")
        _run_preregistration(submission, plugin, options)

        with self.subTest("full registration"):
            result = plugin.register_submission(submission, options)
            assert result
            zaak_url = result["zaak"]["url"]

        with (
            self.subTest("verify created rol"),
            get_zaken_client(self.zgw_group) as client,
        ):
            rollen = client.get("rollen", params={"zaak": zaak_url}).json()

            self.assertEqual(rollen["count"], 2)  # inititiator, registrator
            registrator_rol = next(
                rol
                for rol in rollen["results"]
                if rol["omschrijving"] == "Baliemedewerker"
            )
            self.assertEqual(registrator_rol["betrokkeneType"], "medewerker")
            self.assertEqual(
                registrator_rol["roltoelichting"],
                "Employee who registered the case on behalf of the customer.",
            )
            self.assertEqual(
                registrator_rol["betrokkeneIdentificatie"]["identificatie"],
                "123456782",
            )

    def test_create_zaak_with_case_identification_reference(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "type": "textfield",
                    "key": "someText",
                    "label": "Some text",
                }
            ],
            submitted_data={
                "someText": "Foo",
            },
            bsn="123456782",
            completed=True,
            # Pin to a known case type version
            completed_on=datetime(2024, 7, 9, 15, 30, 0).replace(tzinfo=UTC),
            with_report=True,
        )
        RegistratorInfoFactory.create(submission=submission, value="employee-123")
        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "case_type_identification": "ZT-001",
            "document_type_description": "Attachment Informatieobjecttype",
            "product_url": "",
            "medewerker_roltype": "Baliemedewerker",
            "property_mappings": [
                {
                    "component_key": "someText",
                    "eigenschap": "a property name",
                }
            ],
            "objects_api_group": None,
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
            "summary_documents": [SummaryDocumentChoices.pdf],
        }

        plugin = ZGWRegistration("zgw")

        client = get_zaken_client(self.zgw_group)
        self.addCleanup(client.close)

        with self.subTest("pre-registration"):
            pre_registration_result = plugin.pre_register_submission(
                submission, options
            )
            assert submission.registration_result is not None
            submission.registration_result.update(pre_registration_result.data)  # type: ignore
            submission.save()

            zaak_url = pre_registration_result.data["zaak"]["url"]  # type: ignore
            zaak_data = client.get(zaak_url, headers=CRS_HEADERS).json()

            # Zaaktype version with UUID 1f41885e-23fc-4462-bbc8-80be4ae484dc, see the
            # docker/open-zaak fixtures. This version is valid on 2024-9-9
            self.assertEqual(
                zaak_data["zaaktype"],
                "http://localhost:8003/catalogi/api/v1/zaaktypen/"
                "1f41885e-23fc-4462-bbc8-80be4ae484dc",
            )

        with self.subTest("full registration"):
            result = plugin.register_submission(submission, options)
            assert result is not None
            zaak_url = result["zaak"]["url"]

        with self.subTest("verify case properties"):
            # check created eigenschap
            zaak_eigenschappen = client.get(f"{zaak_url}/zaakeigenschappen").json()
            self.assertEqual(len(zaak_eigenschappen), 1)

        with self.subTest("verify registrator role"):
            rollen = client.get("rollen", params={"zaak": zaak_url}).json()["results"]

            self.assertEqual(len(rollen), 2)
            employee_role = next(
                rol for rol in rollen if rol["betrokkeneType"] == "medewerker"
            )
            self.assertEqual(
                employee_role["betrokkeneIdentificatie"]["identificatie"],
                "employee-123",
            )
            # Roltype with UUID 7f1887e8-bf22-47e7-ae52-ed6848d7e70e, see the
            # docker/open-zaak fixtures.
            self.assertEqual(
                employee_role["roltype"],
                "http://localhost:8003/catalogi/api/v1/roltypen/"
                "7f1887e8-bf22-47e7-ae52-ed6848d7e70e",
            )

    def test_create_zaak_with_zaaktype_where_initiator_roltype_is_missing(self):
        submission = SubmissionFactory.from_components(
            [{"type": "textfield", "key": "dummy"}],
            submitted_data={"dummy": "dummy"},
            bsn="111222333",
            completed=True,
            # Pin to a known case & document type version
            completed_on=datetime(2025, 6, 9, 15, 30, 0).replace(tzinfo=UTC),
            with_report=True,
        )
        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "case_type_identification": "INCOMPLETE",
            "document_type_description": "Attachment Informatieobjecttype",
            "organisatie_rsin": "000000000",
            "objects_api_group": None,
            "product_url": "",
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
            "summary_documents": [SummaryDocumentChoices.pdf],
        }
        plugin = ZGWRegistration("zgw")
        _run_preregistration(submission, plugin, options)

        result = plugin.register_submission(submission, options)

        assert result is not None
        self.assertIsNone(result["initiator_rol"])

    def test_create_zaak_with_case_identification_reference_and_product(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "type": "textfield",
                    "key": "someText",
                    "label": "Some text",
                }
            ],
            submitted_data={
                "someText": "Foo",
            },
            bsn="123456782",
            completed=True,
            # Pin to a known case type version
            completed_on=datetime(2024, 11, 1, 15, 30, 0).replace(tzinfo=UTC),
            with_report=True,
        )
        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "case_type_identification": "ZT-001",
            "document_type_description": "Attachment Informatieobjecttype",
            "product_url": "http://localhost:81/product/1234abcd-12ab-34cd-56ef-12345abcde10",
            "objects_api_group": None,
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
            "summary_documents": [SummaryDocumentChoices.pdf],
        }
        plugin = ZGWRegistration("zgw")

        result = plugin.pre_register_submission(submission, options)

        assert result.data is not None
        zaak_url = result.data["zaak"]["url"]
        with get_zaken_client(self.zgw_group) as client:
            zaak_data = client.get(zaak_url, headers=CRS_HEADERS).json()

        self.assertEqual(
            zaak_data["zaaktype"],
            "http://localhost:8003/catalogi/api/v1/zaaktypen/f609b6fe-449a-46dc-a0af-de55dc5f6774",
        )
        self.assertEqual(
            zaak_data["productenOfDiensten"],
            ["http://localhost:81/product/1234abcd-12ab-34cd-56ef-12345abcde10"],
        )

    @enable_feature_flag("ZGW_APIS_INCLUDE_DRAFTS")
    def test_allow_registration_with_unpublished_case_types(self):
        zgw_group = ZGWApiGroupConfigFactory.create(
            for_test_docker_compose=True,
            organisatie_rsin="000000000",
        )
        submission = SubmissionFactory.from_components(
            [
                {
                    "type": "textfield",
                    "key": "someText",
                    "label": "Some text",
                }
            ],
            submitted_data={
                "someText": "Foo",
            },
            bsn="123456782",
            completed=True,
            # Pin to a known case type version
            completed_on=datetime(2024, 9, 9, 15, 30, 0).replace(tzinfo=UTC),
            with_report=True,
        )
        options: RegistrationOptions = {
            "zgw_api_group": zgw_group,
            "catalogue": {
                "domain": "DRAFT",
                "rsin": "000000000",
            },
            "case_type_identification": "DRAFT-01",
            "document_type_description": "Unpublished",
            "product_url": "",
            "objects_api_group": None,
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
            "summary_documents": [SummaryDocumentChoices.pdf],
        }
        plugin = ZGWRegistration("zgw")

        # creates the case
        result = plugin.pre_register_submission(submission, options)

        assert result.data is not None
        zaak_url = result.data["zaak"]["url"]
        with get_zaken_client(zgw_group) as client:
            zaak_data = client.get(zaak_url, headers=CRS_HEADERS).json()

        self.assertEqual(
            zaak_data["zaaktype"],
            "http://localhost:8003/catalogi/api/v1/"
            "zaaktypen/cf903a2f-0acd-4dbf-9c77-6e5e35d794e1",
        )

    def test_create_document_with_document_type_description_reference(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "type": "textfield",
                    "key": "someText",
                    "label": "Some text",
                }
            ],
            submitted_data={
                "someText": "Foo",
            },
            bsn="123456782",
            completed=True,
            # Pin to a known case & document type version
            completed_on=datetime(2024, 6, 9, 15, 30, 0).replace(tzinfo=UTC),
            with_report=True,
        )
        SubmissionFileAttachmentFactory.create(submission_step=submission.steps[0])
        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "case_type_identification": "ZT-001",
            "document_type_description": "Attachment Informatieobjecttype",
            "objects_api_group": None,
            "product_url": "",
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
            "summary_documents": [SummaryDocumentChoices.pdf],
        }
        plugin = ZGWRegistration("zgw")
        client = get_zaken_client(self.zgw_group)
        self.addCleanup(client.close)
        pre_registration_result = plugin.pre_register_submission(submission, options)
        assert submission.registration_result is not None
        submission.registration_result.update(pre_registration_result.data)  # type: ignore
        submission.save()

        with self.subTest("full registration"):
            result = plugin.register_submission(submission, options)
            assert result is not None
            zaak_url = result["zaak"]["url"]

        with self.subTest("verify related case document"):
            zios = client.get(
                "zaakinformatieobjecten", params={"zaak": zaak_url}
            ).json()
            # one for the PDF, one for the attachment
            self.assertEqual(len(zios), 2)

            with get_documents_client(self.zgw_group) as documents_client:
                for zio in zios:
                    with self.subTest(zio=zio):
                        document_data_response = documents_client.get(
                            zio["informatieobject"]
                        )
                        document_data_response.raise_for_status()

                        informatieobjecttype = document_data_response.json()[
                            "informatieobjecttype"
                        ]
                        self.assertEqual(
                            informatieobjecttype,
                            "http://localhost:8003/catalogi/api/v1/"
                            "informatieobjecttypen/531f6c1a-97f7-478c-85f0-67d2f23661c7",
                        )

    def test_retried_registration_with_internal_reference(self):
        """
        Assert that the internal reference is included in the "kenmerken".
        """
        submission = SubmissionFactory.from_components(
            completed_not_preregistered=True,
            # Pin to a known case & document type version
            completed_on=datetime(2024, 6, 9, 15, 30, 0).replace(tzinfo=UTC),
            needs_on_completion_retry=True,
            public_registration_reference="OF-1234",
            components_list=[{"key": "dummy"}],
            form__registration_backend="zgw-create-zaak",
            form__registration_backend_options={
                "zgw_api_group": self.zgw_group.pk,
                "catalogue": {"domain": "TEST", "rsin": "000000000"},
                "case_type_identification": "ZT-001",
                "document_type_description": "Attachment Informatieobjecttype",
                "organisatie_rsin": "000000000",
                "vertrouwelijkheidaanduiding": "openbaar",
                "objects_api_group": None,
                "summary_documents": [],
            },
        )

        pre_registration(submission.pk, PostSubmissionEvents.on_retry)

        submission.refresh_from_db()
        with get_zaken_client(self.zgw_group) as client:
            assert submission.registration_result is not None
            zaak_url = submission.registration_result["zaak"]["url"]
            zaak_data = client.get(zaak_url, headers=CRS_HEADERS).json()
            self.assertEqual(
                zaak_data["kenmerken"],
                [
                    {
                        "kenmerk": "OF-1234",
                        "bron": "Open Formulieren",
                    }
                ],
            )

    def test_submission_with_multiple_eigenschappen_creation(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "textField1",
                    "type": "textfield",
                },
                {
                    "key": "textField2",
                    "type": "textfield",
                },
            ],
            submitted_data={
                "textField1": "some data",
                "textField2": "more data",
            },
            bsn="123456782",
            completed=True,
            # Pin to a known case type version (2024-10-31)
            completed_on=datetime(2024, 11, 9, 15, 30, 0, tzinfo=UTC),
            with_report=True,
        )
        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "case_type_identification": "ZT-001",
            "document_type_description": "Attachment Informatieobjecttype",
            "product_url": "",
            "property_mappings": [
                {"component_key": "textField1", "eigenschap": "a property name"},
                {"component_key": "textField2", "eigenschap": "second property"},
            ],
            "objects_api_group": None,
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
            "summary_documents": [],
        }
        client = get_zaken_client(self.zgw_group)
        self.addCleanup(client.close)
        plugin = ZGWRegistration("zgw")
        pre_registration_result = plugin.pre_register_submission(submission, options)
        assert submission.registration_result is not None
        submission.registration_result.update(pre_registration_result.data)  # type: ignore
        submission.save()

        # perform the actual registration
        result = plugin.register_submission(submission, options)
        assert result is not None

        self.assertEqual(len(result["zaakeigenschappen"]), 2)
        # verify the created properties
        zaak_url = result["zaak"]["url"]
        zaakeigenschappen = {
            zaak_eigenschap["naam"]: zaak_eigenschap["waarde"]
            for zaak_eigenschap in client.get(f"{zaak_url}/zaakeigenschappen").json()
        }
        self.assertEqual(
            zaakeigenschappen,
            {
                "a property name": "some data",
                "second property": "more data",
            },
        )

    def test_submission_with_nested_component_columns_and_eigenschap(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "column1",
                    "type": "columns",
                    "columns": [
                        {
                            "size": 6,
                            "components": [
                                {
                                    "key": "textField1",
                                    "label": "textField1",
                                    "type": "textfield",
                                }
                            ],
                        },
                        {
                            "size": 6,
                            "components": [
                                {
                                    "key": "textField2",
                                    "label": "textField2",
                                    "type": "textfield",
                                }
                            ],
                        },
                    ],
                },
                {
                    "key": "textField3.blah",
                    "label": "textField3.blah",
                    "type": "textfield",
                },
            ],
            submitted_data={
                "textField1": "data in columns",
                "textField2": "more data",
                "textField3": {"blah": "a value"},
            },
            bsn="123456782",
            completed=True,
            # Pin to a known case type version (2024-10-31)
            completed_on=datetime(2024, 11, 9, 15, 30, 0, tzinfo=UTC),
            with_report=True,
        )
        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "case_type_identification": "ZT-001",
            "document_type_description": "Attachment Informatieobjecttype",
            "product_url": "",
            "property_mappings": [
                {"component_key": "textField1", "eigenschap": "a property name"},
                {"component_key": "textField3.blah", "eigenschap": "second property"},
            ],
            "objects_api_group": None,
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
            "summary_documents": [SummaryDocumentChoices.pdf],
        }
        client = get_zaken_client(self.zgw_group)
        self.addCleanup(client.close)
        plugin = ZGWRegistration("zgw")
        pre_registration_result = plugin.pre_register_submission(submission, options)
        assert submission.registration_result is not None
        submission.registration_result.update(pre_registration_result.data)  # type: ignore
        submission.save()

        # perform the actual registration
        result = plugin.register_submission(submission, options)
        assert result is not None

        self.assertEqual(len(result["zaakeigenschappen"]), 2)
        # verify the created properties
        zaak_url = result["zaak"]["url"]
        zaakeigenschappen = {
            zaak_eigenschap["naam"]: zaak_eigenschap["waarde"]
            for zaak_eigenschap in client.get(f"{zaak_url}/zaakeigenschappen").json()
        }
        self.assertEqual(
            zaakeigenschappen,
            {
                "a property name": "data in columns",
                "second property": "a value",
            },
        )

    def test_register_and_update_paid_product(self):
        submission = SubmissionFactory.from_components(
            [{"type": "textfield", "key": "voornaam", "label": "Voornaam"}],
            submitted_data={"voornaam": "Foo"},
            bsn="111222333",
            # setup payment although at this level of testing it is not needed
            form__product__price=Decimal("11.35"),
            form__payment_backend="demo",
            completed=True,
            # Pin to a known case & document type version
            completed_on=datetime(2024, 6, 9, 15, 30, 0).replace(tzinfo=UTC),
            with_report=True,
        )
        assert submission.payment_required
        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "case_type_identification": "ZT-001",
            "document_type_description": "Attachment Informatieobjecttype",
            "objects_api_group": None,
            "product_url": "",
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
            "summary_documents": [SummaryDocumentChoices.pdf],
        }
        plugin = ZGWRegistration("zgw")
        _run_preregistration(submission, plugin, options)

        with self.subTest("full registration"):
            result = plugin.register_submission(submission, options)
            assert result
            zaak_url = result["zaak"]["url"]

        client = get_zaken_client(self.zgw_group)
        self.addCleanup(client.close)

        with self.subTest("verify initial payment status"):
            zaak_data = client.get(zaak_url, headers=CRS_HEADERS).json()
            self.assertEqual(zaak_data["betalingsindicatie"], "nog_niet")
            self.assertIsNone(zaak_data["laatsteBetaaldatum"])

        before_update = datetime.combine(
            date.fromisoformat(zaak_data["registratiedatum"]),
            time(0, 0, 0, tzinfo=UTC),
        )

        with self.subTest("perform the payment status update"):
            plugin.update_payment_status(submission, options)

        with self.subTest("verify updated payment status"):
            zaak_data = client.get(zaak_url, headers=CRS_HEADERS).json()
            self.assertEqual(zaak_data["betalingsindicatie"], "geheel")
            timestamp_str = zaak_data["laatsteBetaaldatum"]
            self.assertIsNotNone(timestamp_str)
            self.assertGreater(datetime.fromisoformat(timestamp_str), before_update)

    @tag("sentry-334882", "gh-3649")
    def test_file_attachments_respect_field_specific_overrides(self):
        """
        Assert that override of default values for the Documenten API works.
        """
        submission = SubmissionFactory.from_components(
            [
                {
                    "type": "file",
                    "file": {"type": []},
                    "filePattern": "",
                    "key": "field1",
                },
                {
                    "type": "file",
                    "file": {"type": []},
                    "filePattern": "",
                    "key": "field2",
                },
            ],
            bsn="111222333",
            completed=True,
            # Pin to a known case & document type version
            completed_on=datetime(2024, 11, 9, 15, 30, 0).replace(tzinfo=UTC),
            with_report=True,
        )
        submission_step = SubmissionStep.objects.get()
        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "case_type_identification": "ZT-001",
            "document_type_description": "PDF Informatieobjecttype",
            "organisatie_rsin": "000000000",
            # empty value should be ignored, use the VA from the zaaktype
            "zaak_vertrouwelijkheidaanduiding": "",
            "objects_api_group": None,
            "product_url": "",
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
            "summary_documents": [SummaryDocumentChoices.pdf],
            # empty-ish value should fall back to default
            "auteur": "",
            "files": [
                {
                    "key": "field1",
                    "document_type_description": "Attachment Informatieobjecttype",
                    "organization_rsin": "100000009",
                    "confidentiality_level": "zeer_geheim",
                    "title": "TITEL",
                },
                # empty values -> document type defaults must be used
                {
                    "key": "field2",
                    "document_type_description": "",
                    "organization_rsin": "",
                    "title": "",
                },
            ],
        }
        attachment_1 = SubmissionFileAttachmentFactory.create(
            submission_step=submission_step,
            file_name="attachment1.jpg",
            form_key="field1",
            _component_configuration_path="components.0",
        )
        attachment_2 = SubmissionFileAttachmentFactory.create(
            submission_step=submission_step,
            file_name="attachment2.jpg",
            form_key="field2",
            _component_configuration_path="components.1",
        )
        plugin = ZGWRegistration("zgw")
        _run_preregistration(submission, plugin, options)

        plugin.register_submission(submission, options)

        submission.refresh_from_db()
        assert submission.registration_result

        with self.subTest("zaak details"):
            zaak_data = submission.registration_result["zaak"]
            # http://localhost:8003/admin/catalogi/zaaktype/5/change/
            self.assertEqual(zaak_data["vertrouwelijkheidaanduiding"], "intern")

        document_results = submission.registration_result["intermediate"]["documents"]
        with self.subTest("Attachment 1 with overridden fields"):
            document_1_data = document_results[str(attachment_1.pk)]["document"]
            self.assertEqual(document_1_data["bestandsnaam"], "attachment1.jpg")
            self.assertEqual(
                document_1_data["informatieobjecttype"],
                "http://localhost:8003/catalogi/api/v1/"
                "informatieobjecttypen/7755ab0f-9e37-4834-8bbf-158f9f2da38e",
            )
            self.assertEqual(document_1_data["bronorganisatie"], "100000009")
            self.assertEqual(
                document_1_data["vertrouwelijkheidaanduiding"], "zeer_geheim"
            )
            self.assertEqual(document_1_data["titel"], "TITEL")
            self.assertIsNotNone(document_1_data["ontvangstdatum"])

        with self.subTest("Attachment 2 with defaults"):
            document_2_data = document_results[str(attachment_2.pk)]["document"]
            self.assertEqual(document_2_data["bestandsnaam"], "attachment2.jpg")
            # PDF informatieobjecttype
            # http://localhost:8003/admin/catalogi/informatieobjecttype/4/change/
            self.assertEqual(
                document_2_data["informatieobjecttype"],
                "http://localhost:8003/catalogi/api/v1/"
                "informatieobjecttypen/29b63e5c-3835-4f68-8fad-f2aea9ae6b71",
            )
            self.assertEqual(document_2_data["bronorganisatie"], "000000000")
            # default from informatieobjecttype
            self.assertEqual(document_2_data["vertrouwelijkheidaanduiding"], "openbaar")
            self.assertEqual(document_2_data["titel"], "attachment2.jpg")
            self.assertEqual(document_2_data["auteur"], "Aanvrager")
            self.assertIsNotNone(document_2_data["ontvangstdatum"])

        with self.subTest("PDF summary document defaults"):
            pdf_report_data = document_results["report"]["document"]
            # PDF informatieobjecttype
            # http://localhost:8003/admin/catalogi/informatieobjecttype/4/change/
            self.assertEqual(
                pdf_report_data["informatieobjecttype"],
                "http://localhost:8003/catalogi/api/v1/"
                "informatieobjecttypen/29b63e5c-3835-4f68-8fad-f2aea9ae6b71",
            )
            self.assertEqual(pdf_report_data["auteur"], "Aanvrager")
            self.assertIsNone(pdf_report_data["ontvangstdatum"])

        # Issue #3649
        with self.subTest("Ensure 'bestandsomvang' is set explicitly"):
            document_requests = (
                req
                for req in self.cassette.requests
                if req.url.startswith(
                    "http://localhost:8003/documenten/api/v1/enkelvoudiginformatieobjecten"
                )
                if req.method == "POST"
            )
            for req in document_requests:
                req_data = json.loads(req.body)
                assert "bestandsnaam" in req_data
                with self.subTest(file=req_data["bestandsnaam"]):
                    self.assertIn("bestandsomvang", req_data)
                    self.assertIsInstance(req_data["bestandsomvang"], int)

    @tag("gh-5803")
    def test_submission_with_zgw_and_objects_api_backends(self):
        self.maxDiff = None
        objects_api_group = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True
        )
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "achternaam",
                    "type": "textfield",
                },
                {
                    "key": "coordinaat",
                    "type": "map",
                    "registration": {
                        "attribute": RegistrationAttribute.locatie_coordinaat,
                    },
                },
                # ensure that date/datetime/time is properly serialized - see #5803
                {
                    "key": "date",
                    "type": "date",
                    "label": "Date",
                },
                {
                    "key": "datetime",
                    "type": "datetime",
                    "label": "datetime",
                },
                {
                    "key": "editgrid",
                    "type": "editgrid",
                    "label": "Editgrid",
                    "groupLabel": "item",
                    "components": [
                        {
                            "type": "time",
                            "key": "time",
                            "label": "Time",
                        }
                    ],
                },
            ],
            submitted_data={
                "achternaam": "Bar",
                "coordinaat": {
                    "type": "Point",
                    "coordinates": [4.893164274470299, 52.36673378967122],
                },
                "date": "2025-12-10",
                "datetime": "2025-12-11T12:34:56+01:00",
                "editgrid": [{"time": "12:34:56"}],
            },
            bsn="111222333",
            language_code="en",
            form_definition_kwargs={"slug": "test"},
            completed=True,
            # Pin to a known case & document type version
            completed_on=datetime(2024, 11, 9, 15, 30, 0).replace(tzinfo=UTC),
            with_report=True,
        )
        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "case_type_identification": "ZT-001",
            "document_type_description": "PDF Informatieobjecttype",
            "organisatie_rsin": "000000000",
            "objects_api_group": objects_api_group,
            "objecttype": (
                "http://host.docker.internal:8001/api/v2/"
                "objecttypes/8faed0fa-7864-4409-aa6d-533a37616a9e"
            ),
            "objecttype_version": 1,
            "product_url": "",
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
            "content_json": textwrap.dedent(
                """
                {
                    "bron": {
                        "naam": "Open Formulieren",
                        "kenmerk": "{{ submission.kenmerk }}"
                    },
                    "type": "{{ productaanvraag_type }}",
                    "aanvraaggegevens": {% json_summary %},
                    "gh-5803": {
                        "datum": "{{ variables.date }}",
                        "datumtijd": "{{ variables.datetime }}",
                        "editgrid": "{{ variables.editgrid }}"
                    },
                    "taal": "{{ submission.language_code  }}",
                    "betrokkenen": [
                        {
                            "inpBsn" : "{{ variables.auth_bsn }}",
                            "rolOmschrijvingGeneriek" : "initiator"
                        }
                    ]
                }"""
            ),
            "summary_documents": [SummaryDocumentChoices.pdf],
        }
        plugin = ZGWRegistration("zgw")
        _run_preregistration(submission, plugin, options)
        # we need to patch the ZGW client `create_zaakobject` method so that we can
        # fix up the object URL since Open Zaak validates the format and needs to resolve
        # this inside the container network
        original_create_zaakobject = ZakenClient.create_zaakobject

        def wrapped_create_zaakobject(
            self,
            zaak,
            object_url: str,
            objecttype_version_url: str,
        ):
            object_url = object_url.replace(
                "http://objects-web:8000",
                "http://host.docker.internal:8002",
                1,
            )
            return original_create_zaakobject(
                self, zaak, object_url, objecttype_version_url
            )

        with patch.object(
            ZakenClient,
            "create_zaakobject",
            side_effect=wrapped_create_zaakobject,
            autospec=True,
        ):
            result = plugin.register_submission(submission, options)

        # verify the created objects
        assert result is not None
        # grab "today's" date from the zaak registratiedatum
        today = result["zaak"]["registratiedatum"]

        created_object = result["objects_api_object"]
        with self.subTest("objects API object"):
            self.assertEqual(
                created_object["type"],
                (
                    "http://host.docker.internal:8001/api/v2/"
                    "objecttypes/8faed0fa-7864-4409-aa6d-533a37616a9e"
                ),
            )

            self.assertIsInstance(
                created_object["record"]["data"]["bron"]["kenmerk"], str
            )
            del created_object["record"]["data"]["bron"]["kenmerk"]
            self.assertEqual(
                created_object["record"],
                {
                    "index": 1,
                    "typeVersion": 1,
                    "data": {
                        "bron": {"naam": "Open Formulieren"},
                        "type": "ProductAanvraag",
                        "aanvraaggegevens": {
                            "test": {
                                "achternaam": "Bar",
                                "coordinaat": {
                                    "type": "Point",
                                    "coordinates": [
                                        4.893164274470299,
                                        52.36673378967122,
                                    ],
                                },
                                "date": "2025-12-10",
                                "datetime": "2025-12-11T12:34:56+01:00",
                                "editgrid": [{"time": "12:34:56"}],
                            }
                        },
                        "gh-5803": {
                            "datum": "2025-12-10",
                            "datumtijd": "2025-12-11T12:34:56+01:00",
                            # note: string formatted list because of template!
                            "editgrid": "[{'time': '12:34:56'}]",
                        },
                        "taal": "en",
                        "betrokkenen": [
                            {
                                "inpBsn": "111222333",
                                "rolOmschrijvingGeneriek": "initiator",
                            }
                        ],
                    },
                    "startAt": today,
                    "geometry": {
                        "type": "Point",
                        "coordinates": [4.893164274470299, 52.36673378967122],
                    },
                    "endAt": None,
                    "registrationAt": today,
                    "correctionFor": None,
                    "correctedBy": None,
                },
            )

        with self.subTest("zaakobject relation"):
            zaakobject = result["zaakobject"]
            self.assertEqual(zaakobject["zaak"], result["zaak"]["url"])
            self.assertIsNone(zaakobject["zaakobjecttype"])
            self.assertEqual(
                zaakobject["object"],
                created_object["url"].replace(
                    "objects-web:8000", "host.docker.internal:8002"
                ),
            )
            self.assertEqual(zaakobject["objectType"], "overige")
            self.assertEqual(zaakobject["objectTypeOverige"], "")
            self.assertEqual(
                zaakobject["objectTypeOverigeDefinitie"],
                {
                    "url": (
                        "http://host.docker.internal:8001/api/v2/"
                        "objecttypes/8faed0fa-7864-4409-aa6d-533a37616a9e/versions/1"
                    ),
                    "schema": ".jsonSchema",
                    "objectData": ".record.data",
                },
            )
            self.assertEqual(zaakobject["relatieomschrijving"], "")
            self.assertIsNone(zaakobject["objectIdentificatie"])

    @patch(
        "openforms.registrations.contrib.zgw_apis.plugin.get_last_confirmation_email",
        side_effect=[("HTML content 1", 1), ("HTML content 2", 2)],
    )
    def test_confirmation_emails_are_attached_when_updating_registration(
        self, mock_get_last_email
    ):
        submission = SubmissionFactory.from_components(
            [
                {
                    "type": "textfield",
                    "key": "someText",
                    "label": "Some text",
                }
            ],
            submitted_data={"someText": "Foo"},
            bsn="123456782",
            completed=True,
            # Pin to a known case & document type version
            completed_on=datetime(2024, 6, 9, 15, 30, 0).replace(tzinfo=UTC),
            with_report=True,
            confirmation_email_sent=True,
        )
        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "case_type_identification": "ZT-001",
            "document_type_description": "Attachment Informatieobjecttype",
            "objects_api_group": None,
            "product_url": "",
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
            "summary_documents": [SummaryDocumentChoices.pdf],
        }
        plugin = ZGWRegistration("zgw")
        pre_registration_result = plugin.pre_register_submission(submission, options)
        assert submission.registration_result is not None
        submission.registration_result.update(pre_registration_result.data)  # type: ignore
        submission.save()

        # Full registration
        plugin.register_submission(submission, options)

        # Confirmation email updates
        for _ in range(2):
            result = plugin.update_registration_with_confirmation_email(
                submission, options
            )
            assert result is not None

        result = submission.registration_result
        self.assertEqual(len(result["intermediate"]["confirmation_emails"]), 2)

        for document in result["intermediate"]["confirmation_emails"].values():
            document_data = document["document"]
            self.assertEqual(document_data["bronorganisatie"], "000000000")
            self.assertEqual(document_data["formaat"], "application/pdf")
            self.assertEqual(document_data["vertrouwelijkheidaanduiding"], "openbaar")
            self.assertEqual(document_data["taal"], "nld")
            self.assertEqual(document_data["titel"], "Bevestigingsmail")

        with get_zaken_client(self.zgw_group) as zaken_client:
            zios = zaken_client.get(
                "zaakinformatieobjecten", params={"zaak": result["zaak"]["url"]}
            ).json()
            # One for the submission report pdf and two for the confirmation emails
            self.assertEqual(len(zios), 3)

    @patch(
        "openforms.registrations.contrib.zgw_apis.plugin.get_last_confirmation_email",
        return_value=("HTML content", 1),
    )
    def test_confirmation_email_is_only_attached_once(self, mock_get_last_email):
        """
        Can occur when sending another confirmation email has failed for whatever
        reason.
        """
        submission = SubmissionFactory.from_components(
            [
                {
                    "type": "textfield",
                    "key": "someText",
                    "label": "Some text",
                }
            ],
            submitted_data={"someText": "Foo"},
            bsn="123456782",
            completed=True,
            # Pin to a known case & document type version
            completed_on=datetime(2024, 6, 9, 15, 30, 0).replace(tzinfo=UTC),
            with_report=True,
            confirmation_email_sent=True,
        )
        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "case_type_identification": "ZT-001",
            "document_type_description": "Attachment Informatieobjecttype",
            "objects_api_group": None,
            "product_url": "",
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
            "summary_documents": [SummaryDocumentChoices.pdf],
        }
        plugin = ZGWRegistration("zgw")
        pre_registration_result = plugin.pre_register_submission(submission, options)
        assert submission.registration_result is not None
        submission.registration_result.update(pre_registration_result.data)  # type: ignore
        submission.save()

        # Full registration
        plugin.register_submission(submission, options)

        # Confirmation email updates
        for _ in range(2):
            result = plugin.update_registration_with_confirmation_email(
                submission, options
            )
            assert result is not None

        result = submission.registration_result
        self.assertEqual(len(result["intermediate"]["confirmation_emails"]), 1)

        with get_zaken_client(self.zgw_group) as zaken_client:
            zios = zaken_client.get(
                "zaakinformatieobjecten", params={"zaak": result["zaak"]["url"]}
            ).json()
            # One for the submission report pdf and only one confirmation email
            self.assertEqual(len(zios), 2)

    def test_updating_registration_skips_when_confirmation_email_was_not_sent(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "type": "textfield",
                    "key": "someText",
                    "label": "Some text",
                }
            ],
            submitted_data={"someText": "Foo"},
            bsn="123456782",
            completed=True,
            # Pin to a known case & document type version
            completed_on=datetime(2024, 6, 9, 15, 30, 0).replace(tzinfo=UTC),
            with_report=True,
            confirmation_email_sent=False,
        )
        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "case_type_identification": "ZT-001",
            "document_type_description": "Attachment Informatieobjecttype",
            "objects_api_group": None,
            "product_url": "",
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
            "summary_documents": [SummaryDocumentChoices.pdf],
        }
        plugin = ZGWRegistration("zgw")

        self.assertIsNone(
            plugin.update_registration_with_confirmation_email(submission, options)
        )

    @patch(
        "openforms.registrations.contrib.zgw_apis.plugin.get_last_confirmation_email",
        return_value=None,
    )
    def test_updating_registration_raises_when_confirmation_email_was_not_found(
        self, mock_get_last_email
    ):
        submission = SubmissionFactory.from_components(
            [
                {
                    "type": "textfield",
                    "key": "someText",
                    "label": "Some text",
                }
            ],
            submitted_data={"someText": "Foo"},
            bsn="123456782",
            completed=True,
            # Pin to a known case & document type version
            completed_on=datetime(2024, 6, 9, 15, 30, 0).replace(tzinfo=UTC),
            with_report=True,
            confirmation_email_sent=True,
        )
        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "case_type_identification": "ZT-001",
            "document_type_description": "Attachment Informatieobjecttype",
            "objects_api_group": None,
            "product_url": "",
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
            "summary_documents": [SummaryDocumentChoices.pdf],
        }
        plugin = ZGWRegistration("zgw")
        pre_registration_result = plugin.pre_register_submission(submission, options)
        assert submission.registration_result is not None
        submission.registration_result.update(pre_registration_result.data)  # type: ignore
        submission.save()

        # Full registration
        plugin.register_submission(submission, options)

        with self.assertRaises(RegistrationFailed):
            plugin.update_registration_with_confirmation_email(submission, options)

    @patch(
        "openforms.contrib.haal_centraal.clients.HaalCentraalConfig.get_solo",
        return_value=HaalCentraalConfig(
            brp_personen_service=ServiceFactory.build(
                api_root="http://localhost:5010/haalcentraal/api/brp/",
                auth_type=AuthTypes.no_auth,
            ),
            brp_personen_version=BRPVersions.v20,
        ),
    )
    @patch(
        "openforms.config.models.GlobalConfiguration.get_solo",
        return_value=GlobalConfiguration(
            family_members_data_api=FamilyMembersDataAPIChoices.haal_centraal
        ),
    )
    def test_submission_with_partners_component(self, m, n):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "partners",
                    "type": "partners",
                    "registration": {
                        "attribute": RegistrationAttribute.partners,
                    },
                }
            ],
            auth_info__value="000009921",
            auth_info__attribute=AuthAttribute.bsn,
            completed_on=datetime(2024, 11, 9, 15, 30, 0, tzinfo=UTC),
            with_report=True,
        )
        FormVariableFactory.create(
            key="partners_immutable",
            form=submission.form,
            user_defined=True,
            prefill_plugin=FM_PLUGIN_IDENTIFIER,
            prefill_options={
                "type": "partners",
                "mutable_data_form_variable": "partners",
                "min_age": None,
                "max_age": None,
            },
        )
        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "PARTN",
                "rsin": "000000000",
            },
            "case_type_identification": "ZAAKTYPE-2020-0000000001",
            "document_type_description": "Partners PDF Informatieobjecttype",
            "product_url": "",
            "objects_api_group": None,
            "partners_roltype": "Partner role type",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
            "summary_documents": [
                SummaryDocumentChoices.json,
            ],
        }

        prefill_variables(submission)

        client = get_zaken_client(self.zgw_group)
        self.addCleanup(client.close)
        plugin = ZGWRegistration("zgw")
        pre_registration_result = plugin.pre_register_submission(submission, options)
        assert submission.registration_result is not None
        submission.registration_result.update(pre_registration_result.data)  # type: ignore
        submission.save()

        # perform the actual registration
        result = plugin.register_submission(submission, options)
        assert result is not None

        self.assertEqual(
            result["intermediate"]["initiator_rol"]["betrokkeneIdentificatie"],
            {
                "inpBsn": "000009921",
                "anpIdentificatie": "",
                "inpA_nummer": "",
                "geslachtsnaam": "",
                "voorvoegselGeslachtsnaam": "",
                "voorletters": "",
                "voornamen": "",
                "geslachtsaanduiding": "",
                "geboortedatum": "",
                "verblijfsadres": None,
                "subVerblijfBuitenland": None,
            },
        )
        self.assertEqual(
            result["intermediate"]["partner_rol"]["1"]["betrokkeneIdentificatie"],
            {
                "inpBsn": "999995182",
                "anpIdentificatie": "",
                "inpA_nummer": "",
                "geslachtsnaam": "Jansma",
                "voorvoegselGeslachtsnaam": "",
                "voorletters": "A.M.P.",
                "voornamen": "Anna Maria Petra",
                "geslachtsaanduiding": "",
                "geboortedatum": "1945-04-18",
                "verblijfsadres": None,
                "subVerblijfBuitenland": None,
            },
        )
        self.assertEqual(
            result["intermediate"]["partner_rol"]["2"]["betrokkeneIdentificatie"],
            {
                "inpBsn": "123456782",
                "anpIdentificatie": "",
                "inpA_nummer": "",
                "geslachtsnaam": "Test",
                "voorvoegselGeslachtsnaam": "",
                "voorletters": "T.s.p.",
                "voornamen": "Test second partner",
                "geslachtsaanduiding": "",
                "geboortedatum": "1945-04-18",
                "verblijfsadres": None,
                "subVerblijfBuitenland": None,
            },
        )

        # download the summary json document and check the contents
        documents_client = get_documents_client(self.zgw_group)
        self.addCleanup(documents_client.close)

        document_results = result["intermediate"]["documents"]
        json_document = document_results["json"]["document"]
        json_document_content_response = documents_client.get(
            f"{json_document['url']}/download"
        )
        json_document_content_response.raise_for_status()
        json_document_data = json.loads(json_document_content_response.content)

        expected_values = [
            {
                "bsn": "999995182",
                "affixes": "",
                "initials": "A.M.P.",
                "lastName": "Jansma",
                "firstNames": "Anna Maria Petra",
                "dateOfBirth": "1945-04-18",
            },
            {
                "bsn": "123456782",
                "affixes": "",
                "initials": "T.s.p.",
                "lastName": "Test",
                "firstNames": "Test second partner",
                "dateOfBirth": "1945-04-18",
            },
        ]
        expected_schema = {
            "items": {
                "additionalProperties": False,
                "properties": {
                    "affixes": {"type": "string"},
                    "bsn": {
                        "format": "nl-bsn",
                        "pattern": "^\\d{9}$",
                        "type": "string",
                    },
                    "dateOfBirth": {"format": "date", "type": "string"},
                    "firstNames": {"type": "string"},
                    "initials": {"type": "string"},
                    "lastName": {"type": "string"},
                },
                "required": ["bsn"],
                "type": "object",
            },
            "title": "Partners",
            "type": "array",
        }
        self.assertEqual(json_document_data["values"]["partners"], expected_values)
        self.assertEqual(
            json_document_data["values_schema"]["properties"]["partners"],
            expected_schema,
        )

    @tag("gh-5840")
    def test_submission_with_partners_component_and_manually_added_data(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "partners",
                    "type": "partners",
                    "registration": {
                        "attribute": RegistrationAttribute.partners,
                    },
                }
            ],
            auth_info__value="123456782",
            auth_info__attribute=AuthAttribute.bsn,
            completed_on=datetime(2024, 11, 9, 15, 30, 0, tzinfo=UTC),
            # mimic the frontend data we receive
            submitted_data={
                "partners": [
                    {
                        "bsn": "999970409",
                        "affixes": "",
                        "initials": "",
                        "lastName": "Paassen",
                        "dateOfBirth": "2023-02-01",
                        "__addedManually": True,
                    },
                ]
            },
            with_report=True,
        )

        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "PARTN",
                "rsin": "000000000",
            },
            "case_type_identification": "ZAAKTYPE-2020-0000000001",
            "document_type_description": "Partners PDF Informatieobjecttype",
            "product_url": "",
            "objects_api_group": None,
            "partners_roltype": "Partner role type",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
            "summary_documents": [
                SummaryDocumentChoices.json,
            ],
        }

        client = get_zaken_client(self.zgw_group)
        self.addCleanup(client.close)
        plugin = ZGWRegistration("zgw")
        pre_registration_result = plugin.pre_register_submission(submission, options)
        assert submission.registration_result is not None
        submission.registration_result.update(pre_registration_result.data)  # type: ignore
        submission.save()

        # perform the actual registration
        result = plugin.register_submission(submission, options)
        assert result is not None

        self.assertEqual(len(result["intermediate"]["partner_rol"]), 1)
        self.assertEqual(
            result["intermediate"]["initiator_rol"]["betrokkeneIdentificatie"],
            {
                "inpBsn": "123456782",
                "anpIdentificatie": "",
                "inpA_nummer": "",
                "geslachtsnaam": "",
                "voorvoegselGeslachtsnaam": "",
                "voorletters": "",
                "voornamen": "",
                "geslachtsaanduiding": "",
                "geboortedatum": "",
                "verblijfsadres": None,
                "subVerblijfBuitenland": None,
            },
        )
        self.assertEqual(
            result["intermediate"]["partner_rol"]["1"]["betrokkeneIdentificatie"],
            {
                "inpBsn": "999970409",
                "anpIdentificatie": "",
                "inpA_nummer": "",
                "geslachtsnaam": "Paassen",
                "voorvoegselGeslachtsnaam": "",
                "voorletters": "",
                "voornamen": "",
                "geslachtsaanduiding": "",
                "geboortedatum": "2023-02-01",
                "verblijfsadres": None,
                "subVerblijfBuitenland": None,
            },
        )
        self.assertEqual(
            result["intermediate"]["partner_rol"]["1"]["roltoelichting"],
            "natuurlijk_persoon",
        )

    @patch(
        "openforms.contrib.haal_centraal.clients.HaalCentraalConfig.get_solo",
        return_value=HaalCentraalConfig(
            brp_personen_service=ServiceFactory.build(
                api_root="http://localhost:5010/haalcentraal/api/brp/",
                auth_type=AuthTypes.no_auth,
            ),
            brp_personen_version=BRPVersions.v20,
        ),
    )
    @patch(
        "openforms.config.models.GlobalConfiguration.get_solo",
        return_value=GlobalConfiguration(
            family_members_data_api=FamilyMembersDataAPIChoices.haal_centraal
        ),
    )
    def test_submission_with_children_component_and_selection_disabled(self, m, n):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "children",
                    "type": "children",
                    "enableSelection": False,
                    "registration": {
                        "attribute": RegistrationAttribute.children,
                    },
                }
            ],
            auth_info__value="999970094",
            auth_info__attribute=AuthAttribute.bsn,
            completed_on=datetime(2024, 11, 9, 15, 30, 0, tzinfo=UTC),
            with_report=True,
        )
        FormVariableFactory.create(
            key="children_immutable",
            form=submission.form,
            user_defined=True,
            prefill_plugin=FM_PLUGIN_IDENTIFIER,
            prefill_options={
                "type": "children",
                "mutable_data_form_variable": "children",
                "min_age": None,
                "max_age": None,
            },
        )

        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "CHILD",
                "rsin": "000000000",
            },
            "case_type_identification": "ZAAKTYPE-2020-0000000002",
            "document_type_description": "Children PDF Informatieobjecttype",
            "product_url": "",
            "objects_api_group": None,
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "Children role type",
            "children_description": "",
            "summary_documents": [SummaryDocumentChoices.json],
        }

        prefill_variables(submission)

        # the submitted data needs extra handling because frontend adds some extra field
        # to it which is not happenning here, so we have to update it manually in order
        # to mimic the frontend behaviour
        state = submission.variables_state
        children_data = state.get_data()["children"]
        assert isinstance(children_data, list)

        for child in children_data:
            assert isinstance(child, dict)
            child.update(
                {
                    "selected": None,
                    "__id": str(uuid4()),
                    "__addedManually": False,
                }
            )

        client = get_zaken_client(self.zgw_group)
        self.addCleanup(client.close)
        plugin = ZGWRegistration("zgw")
        pre_registration_result = plugin.pre_register_submission(submission, options)
        assert submission.registration_result is not None
        submission.registration_result.update(pre_registration_result.data)  # type: ignore
        submission.save()

        # perform the actual registration
        result = plugin.register_submission(submission, options)
        assert result is not None

        self.assertEqual(len(result["intermediate"]["child_rol"]), 2)
        self.assertEqual(
            result["intermediate"]["initiator_rol"]["betrokkeneIdentificatie"],
            {
                "inpBsn": "999970094",
                "anpIdentificatie": "",
                "inpA_nummer": "",
                "geslachtsnaam": "",
                "voorvoegselGeslachtsnaam": "",
                "voorletters": "",
                "voornamen": "",
                "geslachtsaanduiding": "",
                "geboortedatum": "",
                "verblijfsadres": None,
                "subVerblijfBuitenland": None,
            },
        )
        self.assertEqual(
            result["intermediate"]["child_rol"]["1"]["betrokkeneIdentificatie"],
            {
                "inpBsn": "999970100",
                "anpIdentificatie": "",
                "inpA_nummer": "",
                "geslachtsnaam": "Oostingh",
                "voorvoegselGeslachtsnaam": "",
                "voorletters": "O.",
                "voornamen": "Olle",
                "geslachtsaanduiding": "",
                "geboortedatum": "2022-02-02",
                "verblijfsadres": None,
                "subVerblijfBuitenland": None,
            },
        )
        self.assertEqual(
            result["intermediate"]["child_rol"]["2"]["betrokkeneIdentificatie"],
            {
                "inpBsn": "999970112",
                "anpIdentificatie": "",
                "inpA_nummer": "",
                "geslachtsnaam": "Oostingh",
                "voorvoegselGeslachtsnaam": "",
                "voorletters": "O.",
                "voornamen": "Onne",
                "geslachtsaanduiding": "",
                "geboortedatum": "2022-02-02",
                "verblijfsadres": None,
                "subVerblijfBuitenland": None,
            },
        )

        document_results = result["intermediate"]["documents"]

        # download the summary json document and check the contents
        documents_client = get_documents_client(self.zgw_group)
        self.addCleanup(documents_client.close)

        json_document = document_results["json"]["document"]
        json_document_content_response = documents_client.get(
            f"{json_document['url']}/download"
        )
        json_document_content_response.raise_for_status()
        json_document_data = json.loads(json_document_content_response.content)

        expected_values = [
            {
                "affixes": "",
                "bsn": "999970100",
                "dateOfBirth": "2022-02-02",
                "firstNames": "Olle",
                "initials": "O.",
                "lastName": "Oostingh",
            },
            {
                "affixes": "",
                "bsn": "999970112",
                "dateOfBirth": "2022-02-02",
                "firstNames": "Onne",
                "initials": "O.",
                "lastName": "Oostingh",
            },
        ]
        expected_schema = {
            "items": {
                "additionalProperties": False,
                "properties": {
                    "affixes": {"type": "string"},
                    "bsn": {
                        "format": "nl-bsn",
                        "pattern": "^\\d{9}$",
                        "type": "string",
                    },
                    "dateOfBirth": {"format": "date", "type": "string"},
                    "firstNames": {"type": "string"},
                    "initials": {"type": "string"},
                    "lastName": {"type": "string"},
                },
                "required": ["bsn"],
                "type": "object",
            },
            "title": "Children",
            "type": "array",
        }
        self.assertEqual(json_document_data["values"]["children"], expected_values)
        self.assertEqual(
            json_document_data["values_schema"]["properties"]["children"],
            expected_schema,
        )

    @patch(
        "openforms.contrib.haal_centraal.clients.HaalCentraalConfig.get_solo",
        return_value=HaalCentraalConfig(
            brp_personen_service=ServiceFactory.build(
                api_root="http://localhost:5010/haalcentraal/api/brp/",
                auth_type=AuthTypes.no_auth,
            ),
            brp_personen_version=BRPVersions.v20,
        ),
    )
    @patch(
        "openforms.config.models.GlobalConfiguration.get_solo",
        return_value=GlobalConfiguration(
            family_members_data_api=FamilyMembersDataAPIChoices.haal_centraal
        ),
    )
    def test_submission_with_children_component_and_selection_enabled(self, m, n):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "children",
                    "type": "children",
                    "enableSelection": True,
                    "registration": {
                        "attribute": RegistrationAttribute.children,
                    },
                }
            ],
            auth_info__value="999970094",
            auth_info__attribute=AuthAttribute.bsn,
            completed_on=datetime(2024, 11, 9, 15, 30, 0, tzinfo=UTC),
            with_report=True,
        )
        FormVariableFactory.create(
            key="children_immutable",
            form=submission.form,
            user_defined=True,
            prefill_plugin=FM_PLUGIN_IDENTIFIER,
            prefill_options={
                "type": "children",
                "mutable_data_form_variable": "children",
                "min_age": None,
                "max_age": None,
            },
        )

        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "CHILD",
                "rsin": "000000000",
            },
            "case_type_identification": "ZAAKTYPE-2020-0000000002",
            "document_type_description": "Children PDF Informatieobjecttype",
            "product_url": "",
            "objects_api_group": None,
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "Children role type",
            "children_description": "",
            "summary_documents": [SummaryDocumentChoices.pdf],
        }

        prefill_variables(submission)

        # the submitted data needs extra handling because frontend adds some extra field
        # to it which is not happenning here, so we have to update it manually in order
        # to mimic the frontend behaviour
        state = submission.variables_state
        children_data = state.get_data()["children"]
        assert isinstance(children_data, list)
        assert isinstance(children_data[0], dict)
        assert isinstance(children_data[1], dict)
        children_data[0].update(
            {
                "selected": True,
                "__id": str(uuid4()),
                "__addedManually": False,
            }
        )
        children_data[1].update(
            {
                "selected": False,
                "__id": str(uuid4()),
                "__addedManually": False,
            }
        )

        client = get_zaken_client(self.zgw_group)
        self.addCleanup(client.close)
        plugin = ZGWRegistration("zgw")
        pre_registration_result = plugin.pre_register_submission(submission, options)
        assert submission.registration_result is not None
        submission.registration_result.update(pre_registration_result.data)  # type: ignore
        submission.save()

        # perform the actual registration
        result = plugin.register_submission(submission, options)
        assert result is not None

        self.assertEqual(len(result["intermediate"]["child_rol"]), 1)
        self.assertEqual(
            result["intermediate"]["initiator_rol"]["betrokkeneIdentificatie"],
            {
                "inpBsn": "999970094",
                "anpIdentificatie": "",
                "inpA_nummer": "",
                "geslachtsnaam": "",
                "voorvoegselGeslachtsnaam": "",
                "voorletters": "",
                "voornamen": "",
                "geslachtsaanduiding": "",
                "geboortedatum": "",
                "verblijfsadres": None,
                "subVerblijfBuitenland": None,
            },
        )
        self.assertEqual(
            result["intermediate"]["child_rol"]["1"]["betrokkeneIdentificatie"],
            {
                "inpBsn": "999970100",
                "anpIdentificatie": "",
                "inpA_nummer": "",
                "geslachtsnaam": "Oostingh",
                "voorvoegselGeslachtsnaam": "",
                "voorletters": "O.",
                "voornamen": "Olle",
                "geslachtsaanduiding": "",
                "geboortedatum": "2022-02-02",
                "verblijfsadres": None,
                "subVerblijfBuitenland": None,
            },
        )

    def test_submission_with_manually_added_children_and_selection_enabled(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "children",
                    "type": "children",
                    "enableSelection": True,
                    "registration": {
                        "attribute": RegistrationAttribute.children,
                    },
                }
            ],
            auth_info__value="123456782",
            auth_info__attribute=AuthAttribute.bsn,
            completed_on=datetime(2024, 11, 9, 15, 30, 0, tzinfo=UTC),
            submitted_data={
                "children": [
                    {
                        "bsn": "999970409",
                        "affixes": "van",
                        "initials": "P.",
                        "lastName": "Paassen",
                        "firstNames": "Pero",
                        "dateOfBirth": "2023-02-01",
                        "dateOfBirthPrecision": "date",
                        "selected": True,
                        "__id": str(uuid4()),
                        "__addedManually": True,
                    },
                    {
                        "bsn": "999970161",
                        "affixes": "van",
                        "initials": "P.",
                        "lastName": "Paassen",
                        "firstNames": "Peet",
                        "dateOfBirth": "2018-12-01",
                        "dateOfBirthPrecision": "date",
                        "selected": False,
                        "__id": str(uuid4()),
                        "__addedManually": True,
                    },
                ]
            },
            with_report=True,
        )
        FormVariableFactory.create(
            key="children_immutable",
            form=submission.form,
            user_defined=True,
            prefill_plugin=FM_PLUGIN_IDENTIFIER,
            prefill_options={
                "type": "children",
                "mutable_data_form_variable": "children",
                "min_age": None,
                "max_age": None,
            },
        )

        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "CHILD",
                "rsin": "000000000",
            },
            "case_type_identification": "ZAAKTYPE-2020-0000000002",
            "document_type_description": "Children PDF Informatieobjecttype",
            "product_url": "",
            "objects_api_group": None,
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "Children role type",
            "children_description": "",
            "summary_documents": [SummaryDocumentChoices.pdf],
        }

        client = get_zaken_client(self.zgw_group)
        self.addCleanup(client.close)
        plugin = ZGWRegistration("zgw")
        pre_registration_result = plugin.pre_register_submission(submission, options)
        assert submission.registration_result is not None
        submission.registration_result.update(pre_registration_result.data)  # type: ignore
        submission.save()

        # perform the actual registration
        result = plugin.register_submission(submission, options)
        assert result is not None

        self.assertEqual(len(result["intermediate"]["child_rol"]), 1)
        self.assertEqual(
            result["intermediate"]["initiator_rol"]["betrokkeneIdentificatie"],
            {
                "inpBsn": "123456782",
                "anpIdentificatie": "",
                "inpA_nummer": "",
                "geslachtsnaam": "",
                "voorvoegselGeslachtsnaam": "",
                "voorletters": "",
                "voornamen": "",
                "geslachtsaanduiding": "",
                "geboortedatum": "",
                "verblijfsadres": None,
                "subVerblijfBuitenland": None,
            },
        )
        self.assertEqual(
            result["intermediate"]["child_rol"]["1"]["betrokkeneIdentificatie"],
            {
                "inpBsn": "999970409",
                "anpIdentificatie": "",
                "inpA_nummer": "",
                "geslachtsnaam": "Paassen",
                "voorvoegselGeslachtsnaam": "van",
                "voorletters": "P.",
                "voornamen": "Pero",
                "geslachtsaanduiding": "",
                "geboortedatum": "2023-02-01",
                "verblijfsadres": None,
                "subVerblijfBuitenland": None,
            },
        )

    def test_submission_with_manually_added_children_and_selection_disabled(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "children",
                    "type": "children",
                    "enableSelection": False,
                    "registration": {
                        "attribute": RegistrationAttribute.children,
                    },
                }
            ],
            auth_info__value="123456782",
            auth_info__attribute=AuthAttribute.bsn,
            completed_on=datetime(2024, 11, 9, 15, 30, 0, tzinfo=UTC),
            submitted_data={
                "children": [
                    {
                        "bsn": "999970409",
                        "affixes": "van",
                        "initials": "P.",
                        "lastName": "Paassen",
                        "firstNames": "Pero",
                        "dateOfBirth": "2023-02-01",
                        "dateOfBirthPrecision": "date",
                        "selected": None,
                        "__id": str(uuid4()),
                        "__addedManually": True,
                    },
                    {
                        "bsn": "999970161",
                        "affixes": "van",
                        "initials": "P.",
                        "lastName": "Paassen",
                        "firstNames": "Peet",
                        "dateOfBirth": "2018-12-01",
                        "dateOfBirthPrecision": "date",
                        "selected": None,
                        "__id": str(uuid4()),
                        "__addedManually": True,
                    },
                ]
            },
            with_report=True,
        )
        FormVariableFactory.create(
            key="children_immutable",
            form=submission.form,
            user_defined=True,
            prefill_plugin=FM_PLUGIN_IDENTIFIER,
            prefill_options={
                "type": "children",
                "mutable_data_form_variable": "children",
                "min_age": None,
                "max_age": None,
            },
        )

        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "CHILD",
                "rsin": "000000000",
            },
            "case_type_identification": "ZAAKTYPE-2020-0000000002",
            "document_type_description": "Children PDF Informatieobjecttype",
            "product_url": "",
            "objects_api_group": None,
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "Children role type",
            "children_description": "",
            "summary_documents": [SummaryDocumentChoices.pdf],
        }

        # the submitted data needs extra handling because frontend adds some extra field
        # to it which is not happenning here, so we have to update it manually in order
        # to mimic the frontend behaviour

        client = get_zaken_client(self.zgw_group)
        self.addCleanup(client.close)
        plugin = ZGWRegistration("zgw")
        pre_registration_result = plugin.pre_register_submission(submission, options)
        assert submission.registration_result is not None
        submission.registration_result.update(pre_registration_result.data)  # type: ignore
        submission.save()

        # perform the actual registration
        result = plugin.register_submission(submission, options)
        assert result is not None

        self.assertEqual(len(result["intermediate"]["child_rol"]), 2)
        self.assertEqual(
            result["intermediate"]["initiator_rol"]["betrokkeneIdentificatie"],
            {
                "inpBsn": "123456782",
                "anpIdentificatie": "",
                "inpA_nummer": "",
                "geslachtsnaam": "",
                "voorvoegselGeslachtsnaam": "",
                "voorletters": "",
                "voornamen": "",
                "geslachtsaanduiding": "",
                "geboortedatum": "",
                "verblijfsadres": None,
                "subVerblijfBuitenland": None,
            },
        )
        self.assertEqual(
            result["intermediate"]["child_rol"]["1"]["betrokkeneIdentificatie"],
            {
                "inpBsn": "999970409",
                "anpIdentificatie": "",
                "inpA_nummer": "",
                "geslachtsnaam": "Paassen",
                "voorvoegselGeslachtsnaam": "van",
                "voorletters": "P.",
                "voornamen": "Pero",
                "geslachtsaanduiding": "",
                "geboortedatum": "2023-02-01",
                "verblijfsadres": None,
                "subVerblijfBuitenland": None,
            },
        )
        self.assertEqual(
            result["intermediate"]["child_rol"]["2"]["betrokkeneIdentificatie"],
            {
                "inpBsn": "999970161",
                "anpIdentificatie": "",
                "inpA_nummer": "",
                "geslachtsnaam": "Paassen",
                "voorvoegselGeslachtsnaam": "van",
                "voorletters": "P.",
                "voornamen": "Peet",
                "geslachtsaanduiding": "",
                "geboortedatum": "2018-12-01",
                "verblijfsadres": None,
                "subVerblijfBuitenland": None,
            },
        )

    @tag("gh-5840")
    def test_submission_with_children_component_and_manually_added_data(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "children",
                    "type": "children",
                    "enableSelection": False,
                    "registration": {
                        "attribute": RegistrationAttribute.children,
                    },
                }
            ],
            auth_info__value="123456782",
            auth_info__attribute=AuthAttribute.bsn,
            completed_on=datetime(2024, 11, 9, 15, 30, 0, tzinfo=UTC),
            submitted_data={
                "children": [
                    {
                        "bsn": "999970409",
                        "firstNames": "Pero",
                        "dateOfBirth": "2023-02-01",
                        "selected": None,
                        "__id": str(uuid4()),
                        "__addedManually": True,
                    },
                ]
            },
            with_report=True,
        )

        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "CHILD",
                "rsin": "000000000",
            },
            "case_type_identification": "ZAAKTYPE-2020-0000000002",
            "document_type_description": "Children PDF Informatieobjecttype",
            "product_url": "",
            "objects_api_group": None,
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "Children role type",
            "children_description": "",
            "summary_documents": [SummaryDocumentChoices.pdf],
        }

        client = get_zaken_client(self.zgw_group)
        self.addCleanup(client.close)
        plugin = ZGWRegistration("zgw")
        pre_registration_result = plugin.pre_register_submission(submission, options)
        assert submission.registration_result is not None
        submission.registration_result.update(pre_registration_result.data)  # type: ignore
        submission.save()

        # perform the actual registration
        result = plugin.register_submission(submission, options)
        assert result is not None

        self.assertEqual(len(result["intermediate"]["child_rol"]), 1)
        self.assertEqual(
            result["intermediate"]["initiator_rol"]["betrokkeneIdentificatie"],
            {
                "inpBsn": "123456782",
                "anpIdentificatie": "",
                "inpA_nummer": "",
                "geslachtsnaam": "",
                "voorvoegselGeslachtsnaam": "",
                "voorletters": "",
                "voornamen": "",
                "geslachtsaanduiding": "",
                "geboortedatum": "",
                "verblijfsadres": None,
                "subVerblijfBuitenland": None,
            },
        )
        self.assertEqual(
            result["intermediate"]["child_rol"]["1"]["betrokkeneIdentificatie"],
            {
                "inpBsn": "999970409",
                "anpIdentificatie": "",
                "inpA_nummer": "",
                "geslachtsnaam": "",
                "voorvoegselGeslachtsnaam": "",
                "voorletters": "",
                "voornamen": "Pero",
                "geslachtsaanduiding": "",
                "geboortedatum": "2023-02-01",
                "verblijfsadres": None,
                "subVerblijfBuitenland": None,
            },
        )

    def test_documents_use_public_form_name(self):
        submission = SubmissionFactory.from_components(
            [],
            form__name="Public form name",
            form__internal_name="Internal form name",
            form__registration_backend="zgw-create-zaak",
            bsn="111222333",
            completed=True,
            # Pin to a known case & document type version
            completed_on=datetime(2024, 11, 9, 15, 30, 0).replace(tzinfo=UTC),
            with_report=True,
        )
        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "case_type_identification": "ZT-001",
            "document_type_description": "PDF Informatieobjecttype",
            "organisatie_rsin": "000000000",
            # empty value should be ignored, use the VA from the zaaktype
            "zaak_vertrouwelijkheidaanduiding": "",
            "objects_api_group": None,
            "product_url": "",
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
            "summary_documents": [SummaryDocumentChoices.pdf],
            # empty-ish value should fall back to default
            "auteur": "",
        }
        plugin = ZGWRegistration("zgw")
        _run_preregistration(submission, plugin, options)

        plugin.register_submission(submission, options)

        submission.refresh_from_db()
        assert submission.registration_result

        document_results = submission.registration_result["intermediate"]["documents"]
        pdf_details = document_results["report"]["document"]
        self.assertEqual(pdf_details["titel"], "Public form name (PDF)")

    def test_create_zaak_with_templated_description_and_explanation(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "type": "textfield",
                    "key": "someText",
                    "label": "Some text",
                }
            ],
            submitted_data={
                "someText": "Foo",
            },
            form__name="BBQ permission",
            completed=True,
            # Pin to a known case type version
            completed_on=datetime(2024, 11, 1, 15, 30, 0).replace(tzinfo=UTC),
            with_report=True,
        )
        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "case_type_identification": "ZT-001",
            "document_type_description": "PDF Informatieobjecttype",
            "organisatie_rsin": "000000000",
            # empty value should be ignored, use the VA from the zaaktype
            "zaak_vertrouwelijkheidaanduiding": "",
            "objects_api_group": None,
            "product_url": "",
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
            # empty-ish value should fall back to default
            "auteur": "",
            "zaak_omschrijving": "Description: {{ form_name }}",
            "zaak_toelichting": "Extra explanation about {{ form_name }}",
            "summary_documents": [SummaryDocumentChoices.pdf],
        }
        plugin = ZGWRegistration("zgw")

        result = plugin.pre_register_submission(submission, options)

        assert result.data is not None
        zaak_url = result.data["zaak"]["url"]
        with get_zaken_client(self.zgw_group) as client:
            zaak_data = client.get(zaak_url, headers=CRS_HEADERS).json()

        self.assertEqual(zaak_data["omschrijving"], "Description: BBQ permission")
        self.assertEqual(
            zaak_data["toelichting"], "Extra explanation about BBQ permission"
        )

    def test_create_zaak_with_empty_description_and_explanation(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "type": "textfield",
                    "key": "someText",
                    "label": "Some text",
                }
            ],
            submitted_data={
                "someText": "Foo",
            },
            form__name="Some form",
            completed=True,
            # Pin to a known case type version
            completed_on=datetime(2024, 11, 1, 15, 30, 0).replace(tzinfo=UTC),
            with_report=True,
        )
        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "case_type_identification": "ZT-001",
            "document_type_description": "PDF Informatieobjecttype",
            "product_url": "",
            "objects_api_group": None,
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
            "zaak_omschrijving": "",
            "zaak_toelichting": "",
            "summary_documents": [SummaryDocumentChoices.pdf],
        }
        plugin = ZGWRegistration("zgw")

        result = plugin.pre_register_submission(submission, options)

        assert result.data is not None
        zaak_url = result.data["zaak"]["url"]
        with get_zaken_client(self.zgw_group) as client:
            zaak_data = client.get(zaak_url, headers=CRS_HEADERS).json()

        self.assertEqual(zaak_data["omschrijving"], "Some form")
        self.assertEqual(zaak_data["toelichting"], "")

    def test_can_upload_attachments_with_indirect_document_type_reference(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "type": "file",
                    "key": "file",
                    "label": "File",
                    "file": {"type": []},
                    "filePattern": "",
                    "registration": {
                        "informatieobjecttype": "https://example.com/ignore-me",
                    },
                }
            ],
            form__name="Public form name",
            form__internal_name="Internal form name",
            form__registration_backend="zgw-create-zaak",
            bsn="111222333",
            completed=True,
            # Pin to a known case & document type version
            completed_on=datetime(2024, 11, 9, 15, 30, 0).replace(tzinfo=UTC),
            with_report=True,
        )
        attachment = SubmissionFileAttachmentFactory.create(
            submission_step=submission.steps[0],
            content_type="image/png",
            form_key="file",
            _component_configuration_path="components.0",
        )
        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "case_type_identification": "ZT-001",
            "document_type_description": "PDF Informatieobjecttype",
            "organisatie_rsin": "000000000",
            # empty value should be ignored, use the VA from the zaaktype
            "zaak_vertrouwelijkheidaanduiding": "",
            "objects_api_group": None,
            "product_url": "",
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
            # empty-ish value should fall back to default
            "auteur": "",
            "summary_documents": [SummaryDocumentChoices.pdf],
            "files": [
                {
                    "key": "file",
                    "document_type_description": "Attachment Informatieobjecttype",
                },
            ],
        }
        plugin = ZGWRegistration("zgw")
        _run_preregistration(submission, plugin, options)

        plugin.register_submission(submission, options)

        submission.refresh_from_db()
        assert submission.registration_result

        document_results = submission.registration_result["intermediate"]["documents"]
        resolved_document_type = document_results[str(attachment.pk)]["document"][
            "informatieobjecttype"
        ]
        # UUID copied from Open Zaak admin based on fixture data
        self.assertTrue(
            resolved_document_type.endswith("/7755ab0f-9e37-4834-8bbf-158f9f2da38e")
        )

    def test_create_zaak_with_contactpersoon_rol_attrs(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "naam",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_contactpersoonNaam,
                    },
                },
                {
                    "key": "telefoonnummer",
                    "type": "phoneNumber",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_telefoonnummer,
                    },
                },
                {
                    "key": "email",
                    "type": "email",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_emailadres,
                    },
                },
                *NP_INITIATOR_FIELDS,
            ],
            submitted_data={
                "naam": "Jan Willemse",
                "telefoonnummer": "0612345678",
                "email": "willemse@example.com",
                **NP_INITIATOR_DATA,
            },
            bsn="111222333",
            language_code="en",
            completed=True,
            # Pin to a known case & document type version
            completed_on=datetime(2024, 6, 9, 15, 30, 0).replace(tzinfo=UTC),
            with_report=True,
        )
        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "case_type_identification": "ZT-001",
            "document_type_description": "Attachment Informatieobjecttype",
            "organisatie_rsin": "000000000",
            "zaak_vertrouwelijkheidaanduiding": "openbaar",
            "doc_vertrouwelijkheidaanduiding": "openbaar",
            "objects_api_group": None,
            "product_url": "",
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
            "summary_documents": [SummaryDocumentChoices.pdf],
        }

        plugin = ZGWRegistration("zgw")
        _run_preregistration(submission, plugin, options)

        result = plugin.register_submission(submission, options)
        assert result

        client = get_zaken_client(self.zgw_group)
        self.addCleanup(client.close)

        rol_data = client.get(result["initiator_rol"]["url"]).json()

        self.assertEqual(rol_data["omschrijvingGeneriek"], "initiator")
        self.assertEqual(rol_data["zaak"], result["zaak"]["url"])
        self.assertEqual(rol_data["betrokkene"], "")
        self.assertEqual(rol_data["betrokkeneType"], "natuurlijk_persoon")
        self.assertEqual(
            rol_data["contactpersoonRol"],
            {
                "naam": "Jan Willemse",
                "emailadres": "willemse@example.com",
                "telefoonnummer": "0612345678",
                "functie": "",
            },
        )

    def test_addressnl_registration_attribute_initiator_address(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "address",
                    "type": "addressNL",
                    "label": "Adres",
                    "deriveAddress": True,
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_adres
                    },
                },
            ],
            submitted_data={
                "address": {
                    "postcode": "1043 GR",
                    "houseNumber": "151",
                    "houseLetter": "L",
                    "houseNumberAddition": "67",
                    "streetName": "Kingsfordweg",
                    "city": "Amsterdam",
                    "secretStreetCity": "-irrelevant-",
                },
            },
            bsn="123456782",
            completed=True,
            # Pin to a known case type version
            completed_on=datetime(2024, 11, 9, 15, 30, 0).replace(tzinfo=UTC),
            with_report=True,
        )
        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "case_type_identification": "ZT-001",
            "document_type_description": "Attachment Informatieobjecttype",
            "product_url": "",
            "medewerker_roltype": "",
            "property_mappings": [],
            "objects_api_group": None,
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
            "summary_documents": [SummaryDocumentChoices.pdf],
        }

        plugin = ZGWRegistration("zgw")
        _run_preregistration(submission, plugin, options)

        plugin.register_submission(submission, options)

        submission.refresh_from_db()
        assert submission.registration_result

        initiator_data = submission.registration_result["initiator_rol"]
        self.assertEqual(
            initiator_data["betrokkeneIdentificatie"]["verblijfsadres"],
            {
                "aoaHuisletter": "L",
                "aoaHuisnummer": 151,
                "aoaHuisnummertoevoeging": "67",
                "aoaIdentificatie": "OFWORKAROUND",
                "aoaPostcode": "1043 GR",
                "gorOpenbareRuimteNaam": "Kingsfordweg",
                "inpLocatiebeschrijving": "",
                "wplWoonplaatsNaam": "Amsterdam",
            },
        )

    # breaks because we can't put a KVK number in an RSIN field
    @expectedFailure
    def test_addressnl_registration_attribute_initiator_partial_address(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "handelsnaam",
                    "label": "handelsnaam",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_handelsnaam,
                    },
                },
                {
                    "key": "address",
                    "type": "addressNL",
                    "label": "Adres",
                    "deriveAddress": False,
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_adres
                    },
                },
            ],
            kvk="12345678",
            submitted_data={
                "handelsnaam": "ACME",
                "address": {
                    "postcode": "1043 GR",
                    "houseNumber": "151",
                    "houseLetter": "",
                    "houseNumberAddition": "",
                    "streetName": "",
                    "city": "",
                    "secretStreetCity": "",
                },
            },
            completed=True,
            # Pin to a known case type version
            completed_on=datetime(2024, 11, 9, 15, 30, 0).replace(tzinfo=UTC),
            with_report=True,
        )
        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "case_type_identification": "ZT-001",
            "document_type_description": "Attachment Informatieobjecttype",
            "product_url": "",
            "medewerker_roltype": "",
            "property_mappings": [],
            "objects_api_group": None,
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
            "summary_documents": [SummaryDocumentChoices.pdf],
        }
        plugin = ZGWRegistration("zgw")
        _run_preregistration(submission, plugin, options)

        plugin.register_submission(submission, options)

        submission.refresh_from_db()
        assert submission.registration_result

        initiator_data = submission.registration_result["initiator_rol"]
        self.assertEqual(
            initiator_data["betrokkeneIdentificatie"]["bezoekadres"], "1043 GR 151"
        )

    @parametrize("submitted_value", [None, {}, "bad"])
    def test_addressnl_empty_or_broken_mapping(self, submitted_value):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "address",
                    "type": "addressNL",
                    "label": "Adres",
                    "deriveAddress": True,
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_adres
                    },
                },
            ],
            submitted_data={"address": submitted_value},
            bsn="123456782",
            completed=True,
            # Pin to a known case type version
            completed_on=datetime(2024, 11, 9, 15, 30, 0).replace(tzinfo=UTC),
            with_report=True,
        )
        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "case_type_identification": "ZT-001",
            "document_type_description": "Attachment Informatieobjecttype",
            "product_url": "",
            "medewerker_roltype": "",
            "property_mappings": [],
            "objects_api_group": None,
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
            "summary_documents": [SummaryDocumentChoices.pdf],
        }
        plugin = ZGWRegistration("zgw")
        _run_preregistration(submission, plugin, options)

        try:
            plugin.register_submission(submission, options)
        except TypeError:  # crash will be logged in the admin
            return

        submission.refresh_from_db()
        assert submission.registration_result

        initiator_data = submission.registration_result["initiator_rol"]
        self.assertIsNone(initiator_data["betrokkeneIdentificatie"]["verblijfsadres"])

    def test_all_summary_documents(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "type": "textfield",
                    "key": "someText",
                    "label": "Some text",
                },
                {
                    "type": "file",
                    "key": "file",
                    "label": "File",
                    "file": {"type": []},
                    "filePattern": "",
                    "url": "",
                    "multiple": False,
                },
                {
                    "type": "file",
                    "key": "fileMultiple",
                    "label": "Filemultiple",
                    "file": {"type": []},
                    "filePattern": "",
                    "url": "",
                    "multiple": True,
                },
                {
                    "key": "editgrid",
                    "type": "editgrid",
                    "label": "Editgrid",
                    "groupLabel": "Item",
                    "components": [
                        {
                            "type": "time",
                            "key": "time",
                            "label": "Time",
                        },
                        {
                            "key": "editgridFile",
                            "type": "file",
                            "label": "File",
                            "file": {"type": []},
                            "filePattern": "",
                            "url": "",
                            "multiple": False,
                        },
                    ],
                },
            ],
            submitted_data={
                "someText": "Foo",
                "file": [
                    {
                        "url": "some://url",
                        "name": "my-foo.bin",
                        "type": "application/foo",
                        "originalName": "my-foo.bin",
                    },
                ],
                "fileMultiple": [
                    {
                        "url": "some://url",
                        "name": "my-bar.bin",
                        "type": "application/bar",
                        "originalName": "my-bar.bin",
                    },
                ],
                "editgrid": [
                    {
                        "time": "12:34:56",
                        "editgridFile": [
                            {
                                "url": "some://url",
                                "name": "my-baz.bin",
                                "type": "application/baz",
                                "originalName": "my-baz.bin",
                            },
                        ],
                    }
                ],
            },
            form__name="Public form name",
            form__internal_name="Internal form name",
            form__registration_backend=PLUGIN_IDENTIFIER,
            bsn="111222333",
            completed=True,
            # Pin to a known case & document type version
            completed_on=datetime(2024, 11, 9, 15, 30, 0).replace(tzinfo=UTC),
            with_report=True,
        )

        SubmissionFileAttachmentFactory.create(
            form_key="file",
            submission_step=submission.steps[0],
            file_name="test_file.txt",
            original_name="test_file.txt",
            content_type="application/text",
            content__data=b"This is example content.",
            _component_configuration_path="components.1",
            _component_data_path="file",
        )
        SubmissionFileAttachmentFactory.create(
            form_key="fileMultiple",
            submission_step=submission.steps[0],
            file_name="test_file2.txt",
            original_name="test_file2.txt",
            content_type="application/text",
            content__data=b"This is example content.",
            _component_configuration_path="components.2",
            _component_data_path="fileMultiple",
        )
        SubmissionFileAttachmentFactory.create(
            form_key="editgrid",
            submission_step=submission.steps[0],
            file_name="test_file3.txt",
            original_name="test_file3.txt",
            content_type="application/text",
            content__data=b"This is example content.",
            _component_configuration_path="components.3.components.1",
            _component_data_path="editgrid.0.editgridFile",
        )

        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "case_type_identification": "ZT-001",
            "document_type_description": "PDF Informatieobjecttype",
            "organisatie_rsin": "000000000",
            # empty value should be ignored, use the VA from the zaaktype
            "zaak_vertrouwelijkheidaanduiding": "",
            "objects_api_group": None,
            "product_url": "",
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
            "summary_documents": [
                SummaryDocumentChoices.pdf,
                SummaryDocumentChoices.json,
            ],
            # empty-ish value should fall back to default
            "auteur": "",
        }

        plugin = ZGWRegistration("zgw")
        _run_preregistration(submission, plugin, options)

        plugin.register_submission(submission, options)

        submission.refresh_from_db()
        assert submission.registration_result

        document_results = submission.registration_result["intermediate"]["documents"]
        pdf_details = document_results["report"]["document"]
        self.assertEqual(pdf_details["titel"], "Public form name (PDF)")

        # download the summary json document and check the contents
        documents_client = get_documents_client(self.zgw_group)
        self.addCleanup(documents_client.close)

        json_document = document_results["json"]["document"]
        json_document_content_response = documents_client.get(
            f"{json_document['url']}/download"
        )
        json_document_content_response.raise_for_status()
        json_document_data = json.loads(json_document_content_response.content)

        self.assertEqual(json_document["titel"], "Public form name (JSON)")
        self.assertEqual(json_document["formaat"], "application/json")
        self.assertEqual(json_document_data["values"]["someText"], "Foo")

        with self.subTest("single file upload", aspect="values"):
            single_file_value = json_document_data["values"]["file"]

            self.assertIsInstance(single_file_value, str)
            self.assertTrue(
                single_file_value.startswith(
                    "http://localhost:8003/documenten/api/v1/"
                    "enkelvoudiginformatieobjecten/"
                ),
            )

        with self.subTest("single file upload", aspect="schema"):
            single_file_schema = json_document_data["values_schema"]["properties"][
                "file"
            ]

            self.assertEqual(
                single_file_schema,
                {
                    "type": "string",
                    "title": "File",
                    "anyOf": [
                        {"format": "uri"},
                        {"const": ""},
                    ],
                },
            )

        with self.subTest("multiple file upload", aspect="values"):
            multiple_file_value = json_document_data["values"]["fileMultiple"]

            self.assertIsInstance(multiple_file_value, list)
            self.assertTrue(
                multiple_file_value[0].startswith(
                    "http://localhost:8003/documenten/api/v1/"
                    "enkelvoudiginformatieobjecten/"
                ),
            )

        with self.subTest("multiple file upload", aspect="schema"):
            multiple_file_schema = json_document_data["values_schema"]["properties"][
                "fileMultiple"
            ]

            self.assertEqual(
                multiple_file_schema,
                {
                    "type": "array",
                    "title": "Filemultiple",
                    "items": {"type": "string", "format": "uri"},
                },
            )

        with self.subTest("editgrid", aspect="values"):
            editgrid_value = json_document_data["values"]["editgrid"]

            self.assertIsInstance(editgrid_value, list)
            item_value = editgrid_value[0]
            self.assertIsInstance(item_value, dict)
            self.assertEqual(item_value["time"], "12:34:56")
            self.assertIsInstance(item_value["editgridFile"], str)
            self.assertTrue(
                item_value["editgridFile"].startswith(
                    "http://localhost:8003/documenten/api/v1/"
                    "enkelvoudiginformatieobjecten/"
                ),
            )

        with self.subTest("editgrid", aspect="schema"):
            editgrid_schema = json_document_data["values_schema"]["properties"][
                "editgrid"
            ]

            self.assertEqual(
                editgrid_schema,
                {
                    "type": "array",
                    "title": "Editgrid",
                    "items": {
                        "additionalProperties": False,
                        "type": "object",
                        "properties": {
                            "time": {
                                "format": "time",
                                "title": "Time",
                                "type": "string",
                            },
                            "editgridFile": {
                                "type": "string",
                                "title": "File",
                                "anyOf": [
                                    {"format": "uri"},
                                    {"const": ""},
                                ],
                            },
                        },
                        "required": ["time", "editgridFile"],
                    },
                },
            )

    def test_single_document_summary(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "type": "textfield",
                    "key": "someText",
                    "label": "Some text",
                }
            ],
            submitted_data={
                "someText": "Foo",
            },
            form__name="Public form name",
            form__internal_name="Internal form name",
            form__registration_backend=PLUGIN_IDENTIFIER,
            bsn="111222333",
            completed=True,
            # Pin to a known case & document type version
            completed_on=datetime(2024, 11, 9, 15, 30, 0).replace(tzinfo=UTC),
            with_report=True,
        )

        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "case_type_identification": "ZT-001",
            "document_type_description": "PDF Informatieobjecttype",
            "organisatie_rsin": "000000000",
            # empty value should be ignored, use the VA from the zaaktype
            "zaak_vertrouwelijkheidaanduiding": "",
            "objects_api_group": None,
            "product_url": "",
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
            "summary_documents": [SummaryDocumentChoices.pdf],
            # empty-ish value should fall back to default
            "auteur": "",
        }
        plugin = ZGWRegistration("zgw")
        _run_preregistration(submission, plugin, options)

        plugin.register_submission(submission, options)

        submission.refresh_from_db()
        assert submission.registration_result

        document_results = submission.registration_result["intermediate"]["documents"]
        pdf_details = document_results["report"]["document"]
        self.assertEqual(pdf_details["titel"], "Public form name (PDF)")
        self.assertTrue("json" not in document_results)
