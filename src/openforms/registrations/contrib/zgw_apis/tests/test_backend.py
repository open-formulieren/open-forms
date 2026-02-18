import json
import textwrap
from datetime import UTC, date, datetime, time
from decimal import Decimal
from unittest import expectedFailure
from unittest.mock import patch
from uuid import uuid4

from django.test import TestCase, override_settings, tag

from privates.test import temp_private_root
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
from ..plugin import ZGWRegistration
from ..typing import RegistrationOptions
from .factories import ZGWApiGroupConfigFactory

NP_INITIATOR_FIELDS = [
    {
        "key": "achternaam",
        "type": "textfield",
        "registration": {
            "attribute": RegistrationAttribute.initiator_geslachtsnaam,
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
        "key": "woonplaats",
        "type": "textfield",
        "registration": {"attribute": RegistrationAttribute.initiator_woonplaats},
    },
    {
        "key": "straat",
        "type": "textfield",
        "registration": {
            "attribute": RegistrationAttribute.initiator_straat,
        },
    },
    {
        "key": "huisnummer",
        "type": "number",
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
class ZGWBackendVCRTests(OFVCRMixin, TestCase):
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

    @patch(
        "openforms.registrations.contrib.zgw_apis.plugin.generate_unique_submission_reference",
        return_value="OF-JCRWBX",
    )
    def test_submission_has_reference_after_pre_registration_use_of_generator(
        self, mock
    ):
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

        submission.refresh_from_db()
        self.assertEqual(submission.public_registration_reference, "OF-JCRWBX")
        self.assertEqual(
            submission.registration_result["zaak"]["identificatie"], "OF-JCRWBX"
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
            "zaaktype": "",
            "informatieobjecttype": "",
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

    def test_create_zaak_with_natuurlijk_persoon_initiator_and_legacy_config(self):
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
                    "key": "coordinaat",
                    "type": "map",
                    "registration": {
                        "attribute": RegistrationAttribute.locatie_coordinaat,
                    },
                },
                *NP_INITIATOR_FIELDS,
            ],
            submitted_data={
                "voornaam": "Foo",
                "achternaam": "Bar",
                "tussenvoegsel": "de",
                "postcode": "1000 AA",
                "woonplaats": "Ketnet",
                "straat": "Samsonweg",
                "huisnummer": 101,
                "geboortedatum": "2000-12-31",
                "voorletters": "J.W.",
                "geslachtsaanduiding": "mannelijk",
            },
            bsn="111222333",
            form__product__price=Decimal("0"),
            form__payment_backend="demo",
            language_code="en",
            completed=True,
        )
        SubmissionFileAttachmentFactory.create(
            submission_step=submission.steps[0],
            content_type="image/png",
        )
        catalogi_root = self.zgw_group.ztc_service.api_root
        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "case_type_identification": "",
            "document_type_description": "",
            "zaaktype": f"{catalogi_root}zaaktypen/1f41885e-23fc-4462-bbc8-80be4ae484dc",
            "informatieobjecttype": f"{catalogi_root}informatieobjecttypen/531f6c1a-97f7-478c-85f0-67d2f23661c7",
            "organisatie_rsin": "000000000",
            "zaak_vertrouwelijkheidaanduiding": "openbaar",
            "doc_vertrouwelijkheidaanduiding": "openbaar",
            "objects_api_group": None,
            "product_url": "",
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
        }

        plugin = ZGWRegistration("zgw")
        pre_registration_result = plugin.pre_register_submission(submission, options)
        assert submission.registration_result is not None
        assert isinstance(pre_registration_result.data, dict)
        submission.registration_result.update(pre_registration_result.data)
        submission.save()

        result = plugin.register_submission(submission, options)
        assert result

        with self.subTest("check recorded result"):
            zaken_root = self.zgw_group.zrc_service.api_root
            documenten_root = self.zgw_group.drc_service.api_root
            self.assertTrue(result["zaak"]["url"].startswith(f"{zaken_root}zaken/"))
            self.assertTrue(
                result["document"]["url"].startswith(
                    f"{documenten_root}enkelvoudiginformatieobjecten/"
                )
            )
            self.assertTrue(
                result["initiator_rol"]["url"].startswith(f"{zaken_root}rollen/")
            )
            self.assertTrue(
                result["status"]["url"].startswith(f"{zaken_root}statussen/")
            )

        client = get_zaken_client(self.zgw_group)
        self.addCleanup(client.close)
        documents_client = get_documents_client(self.zgw_group)
        self.addCleanup(documents_client.close)

        with self.subTest("verify zaak"):
            zaak_data = client.get(result["zaak"]["url"], headers=CRS_HEADERS).json()

            self.assertEqual(zaak_data["kenmerken"], [])
            self.assertEqual(zaak_data["bronorganisatie"], "000000000")
            self.assertEqual(zaak_data["verantwoordelijkeOrganisatie"], "000000000")
            self.assertEqual(zaak_data["vertrouwelijkheidaanduiding"], "openbaar")
            self.assertEqual(
                zaak_data["zaaktype"],
                f"{catalogi_root}zaaktypen/1f41885e-23fc-4462-bbc8-80be4ae484dc",
            )
            self.assertEqual(zaak_data["betalingsindicatie"], "nvt")
            self.assertEqual(
                zaak_data["zaakgeometrie"],
                {
                    "type": "Point",
                    "coordinates": [4.893164274470299, 52.36673378967122],
                },
            )

        with self.subTest("verify rol"):
            rol_data = client.get(result["initiator_rol"]["url"]).json()

            self.assertEqual(rol_data["omschrijvingGeneriek"], "initiator")
            self.assertEqual(rol_data["zaak"], result["zaak"]["url"])
            self.assertEqual(rol_data["betrokkene"], "")
            self.assertEqual(rol_data["betrokkeneType"], "natuurlijk_persoon")
            expected_identificatie = {
                "inpBsn": "111222333",
                "anpIdentificatie": "",
                "inpA_nummer": "",
                "geboortedatum": "2000-12-31",
                "geslachtsaanduiding": "m",
                "geslachtsnaam": "Bar",
                "voorletters": "J.W.",
                "voornamen": "Foo",
                "subVerblijfBuitenland": None,
                "verblijfsadres": {
                    "aoaHuisletter": "",
                    "aoaHuisnummer": 101,
                    "aoaHuisnummertoevoeging": "",
                    "aoaIdentificatie": "OFWORKAROUND",
                    "aoaPostcode": "1000 AA",
                    "gorOpenbareRuimteNaam": "Samsonweg",
                    "inpLocatiebeschrijving": "",
                    "wplWoonplaatsNaam": "Ketnet",
                },
                "voorvoegselGeslachtsnaam": "de",
            }
            self.assertEqual(
                rol_data["betrokkeneIdentificatie"], expected_identificatie
            )

        with self.subTest("verify initial status"):
            status_data = client.get(
                "statussen", params={"zaak": result["zaak"]["url"]}
            ).json()
            self.assertEqual(status_data["count"], 1)

        with self.subTest("verify related documents"):
            zios = client.get(
                "zaakinformatieobjecten", params={"zaak": result["zaak"]["url"]}
            ).json()
            self.assertEqual(len(zios), 2)  # one for summary PDF, one for attachment

            attachment_document_data = documents_client.get(
                zios[0]["informatieobject"]
            ).json()
            summary_pdf_data = documents_client.get(zios[1]["informatieobject"]).json()

            self.assertEqual(summary_pdf_data["bronorganisatie"], "000000000")
            self.assertEqual(summary_pdf_data["formaat"], "application/pdf")
            self.assertEqual(
                summary_pdf_data["vertrouwelijkheidaanduiding"], "openbaar"
            )
            self.assertEqual(summary_pdf_data["taal"], "eng")

            self.assertEqual(attachment_document_data["bronorganisatie"], "000000000")
            self.assertEqual(attachment_document_data["formaat"], "image/png")
            self.assertEqual(
                attachment_document_data["vertrouwelijkheidaanduiding"], "openbaar"
            )
            self.assertEqual(attachment_document_data["taal"], "eng")

    def test_create_zaak_with_vestiging_and_kvk_initiator_and_legacy_config(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "handelsnaam",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_handelsnaam,
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
                    "key": "woonplaats",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_woonplaats
                    },
                },
                {
                    "key": "straat",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_straat,
                    },
                },
                {
                    "key": "huisnummer",
                    "type": "number",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_huisnummer,
                    },
                },
                {
                    "key": "vestigingsNummer",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_vestigingsnummer,
                    },
                },
            ],
            submitted_data={
                "handelsnaam": "ACME",
                "postcode": "1000 AA",
                "woonplaats": "Ketnet",
                "straat": "Samsonweg",
                "huisnummer": 101,
                "vestigingsNummer": "87654321",
            },
            kvk="12345678",
            completed=True,
        )
        catalogi_root = self.zgw_group.ztc_service.api_root
        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "case_type_identification": "",
            "document_type_description": "",
            "zaaktype": f"{catalogi_root}zaaktypen/1f41885e-23fc-4462-bbc8-80be4ae484dc",
            "informatieobjecttype": f"{catalogi_root}informatieobjecttypen/531f6c1a-97f7-478c-85f0-67d2f23661c7",
            "organisatie_rsin": "000000000",
            "zaak_vertrouwelijkheidaanduiding": "openbaar",
            "doc_vertrouwelijkheidaanduiding": "openbaar",
            "objects_api_group": None,
            "product_url": "",
            "partners_description": "",
            "partners_roltype": "",
            "children_roltype": "",
            "children_description": "",
        }
        plugin = ZGWRegistration("zgw")
        pre_registration_result = plugin.pre_register_submission(submission, options)
        assert submission.registration_result is not None
        assert isinstance(pre_registration_result.data, dict)
        submission.registration_result.update(pre_registration_result.data)
        submission.save()

        result = plugin.register_submission(submission, options)
        assert result

        with self.subTest("check recorded result"):
            zaken_root = self.zgw_group.zrc_service.api_root
            self.assertTrue(
                result["initiator_rol"]["url"].startswith(f"{zaken_root}rollen/")
            )

        client = get_zaken_client(self.zgw_group)
        self.addCleanup(client.close)

        with self.subTest("verify initiator"):
            rol_data = client.get(result["initiator_rol"]["url"]).json()

            self.assertEqual(rol_data["omschrijvingGeneriek"], "initiator")
            self.assertEqual(rol_data["zaak"], result["zaak"]["url"])
            self.assertEqual(rol_data["betrokkene"], "")
            self.assertEqual(rol_data["betrokkeneType"], "vestiging")
            expected_identificatie = {
                "handelsnaam": ["ACME"],
                "kvkNummer": "12345678",
                "vestigingsNummer": "87654321",
                "verblijfsadres": {
                    "aoaHuisletter": "",
                    "aoaHuisnummer": 101,
                    "aoaHuisnummertoevoeging": "",
                    "aoaIdentificatie": "OFWORKAROUND",
                    "aoaPostcode": "1000 AA",
                    "gorOpenbareRuimteNaam": "Samsonweg",
                    "inpLocatiebeschrijving": "",
                    "wplWoonplaatsNaam": "Ketnet",
                },
                "subVerblijfBuitenland": None,
            }
            self.assertEqual(
                rol_data["betrokkeneIdentificatie"], expected_identificatie
            )

    def test_create_zaak_with_vestiging_and_kvk_initiator_and_legacy_config_through_auth(
        self,
    ):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "handelsnaam",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_handelsnaam,
                    },
                },
            ],
            submitted_data={
                "handelsnaam": "ACME",
            },
            kvk="12345678",
            branch_number="000038509490",
            completed=True,
        )
        catalogi_root = self.zgw_group.ztc_service.api_root
        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "case_type_identification": "",
            "document_type_description": "",
            "zaaktype": f"{catalogi_root}zaaktypen/1f41885e-23fc-4462-bbc8-80be4ae484dc",
            "informatieobjecttype": f"{catalogi_root}informatieobjecttypen/531f6c1a-97f7-478c-85f0-67d2f23661c7",
            "organisatie_rsin": "000000000",
            "zaak_vertrouwelijkheidaanduiding": "openbaar",
            "doc_vertrouwelijkheidaanduiding": "openbaar",
            "objects_api_group": None,
            "product_url": "",
            "partners_description": "",
            "partners_roltype": "",
            "children_roltype": "",
            "children_description": "",
        }
        plugin = ZGWRegistration("zgw")
        pre_registration_result = plugin.pre_register_submission(submission, options)
        assert submission.registration_result is not None
        assert isinstance(pre_registration_result.data, dict)
        submission.registration_result.update(pre_registration_result.data)
        submission.save()

        result = plugin.register_submission(submission, options)
        assert result

        with self.subTest("check recorded result"):
            zaken_root = self.zgw_group.zrc_service.api_root
            self.assertTrue(
                result["initiator_rol"]["url"].startswith(f"{zaken_root}rollen/")
            )

        client = get_zaken_client(self.zgw_group)
        self.addCleanup(client.close)

        with self.subTest("verify initiator"):
            rol_data = client.get(result["initiator_rol"]["url"]).json()

            self.assertEqual(rol_data["omschrijvingGeneriek"], "initiator")
            self.assertEqual(rol_data["zaak"], result["zaak"]["url"])
            self.assertEqual(rol_data["betrokkene"], "")
            self.assertEqual(rol_data["betrokkeneType"], "vestiging")
            expected_identificatie = {
                "handelsnaam": ["ACME"],
                "kvkNummer": "12345678",
                "vestigingsNummer": "000038509490",
                "verblijfsadres": None,
                "subVerblijfBuitenland": None,
            }
            self.assertEqual(
                rol_data["betrokkeneIdentificatie"], expected_identificatie
            )

    # breaks because we can't put a KVK number in an RSIN field
    @expectedFailure
    def test_create_zaak_with_kvk_initiator_only_and_legacy_config(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "handelsnaam",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_handelsnaam,
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
                    "key": "woonplaats",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_woonplaats
                    },
                },
                {
                    "key": "straat",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_straat,
                    },
                },
                {
                    "key": "huisnummer",
                    "type": "number",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_huisnummer,
                    },
                },
            ],
            submitted_data={
                "handelsnaam": "ACME",
                "postcode": "1000 AA",
                "woonplaats": "Ketnet",
                "straat": "Samsonweg",
                "huisnummer": 101,
            },
            kvk="12345678",
            completed=True,
        )

        catalogi_root = self.zgw_group.ztc_service.api_root
        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "case_type_identification": "",
            "document_type_description": "",
            "zaaktype": f"{catalogi_root}zaaktypen/1f41885e-23fc-4462-bbc8-80be4ae484dc",
            "informatieobjecttype": f"{catalogi_root}informatieobjecttypen/531f6c1a-97f7-478c-85f0-67d2f23661c7",
            "organisatie_rsin": "000000000",
            "zaak_vertrouwelijkheidaanduiding": "openbaar",
            "doc_vertrouwelijkheidaanduiding": "openbaar",
            "objects_api_group": None,
            "product_url": "",
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
        }
        plugin = ZGWRegistration("zgw")
        pre_registration_result = plugin.pre_register_submission(submission, options)
        assert submission.registration_result is not None
        assert isinstance(pre_registration_result.data, dict)
        submission.registration_result.update(pre_registration_result.data)
        submission.save()

        result = plugin.register_submission(submission, options)
        assert result

        with self.subTest("check recorded result"):
            zaken_root = self.zgw_group.zrc_service.api_root
            self.assertTrue(result["rol"]["url"].startswith(f"{zaken_root}rollen/"))

        client = get_zaken_client(self.zgw_group)
        self.addCleanup(client.close)

        with self.subTest("verify initiator"):
            rol_data = client.get(result["rol"]["url"]).json()

            self.assertEqual(rol_data["omschrijvingGeneriek"], "initiator")
            self.assertEqual(rol_data["zaak"], result["zaak"]["url"])
            self.assertEqual(rol_data["betrokkene"], "")
            self.assertEqual(rol_data["betrokkeneType"], "niet_natuurlijk_persoon")
            expected_identificatie = {
                "annIdentificatie": "",
                "bezoekadres": "",
                "innNnpId": "12345678",
                "innRechtsvorm": "",
                "statutaireNaam": "ACME",
                "subVerblijfBuitenland": None,
            }
            self.assertEqual(
                rol_data["betrokkeneIdentificatie"], expected_identificatie
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
            completed_on=datetime(2024, 9, 9, 15, 30, 0).replace(tzinfo=UTC),
        )
        RegistratorInfoFactory.create(submission=submission, value="employee-123")
        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "case_type_identification": "ZT-001",
            "document_type_description": "",
            "zaaktype": "",
            "informatieobjecttype": (
                "http://localhost:8003/catalogi/api/v1/"
                "informatieobjecttypen/531f6c1a-97f7-478c-85f0-67d2f23661c7"
            ),
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
        )
        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "case_type_identification": "INCOMPLETE",
            "document_type_description": "Attachment Informatieobjecttype",
            "zaaktype": "",
            "informatieobjecttype": "",
            "organisatie_rsin": "000000000",
            "objects_api_group": None,
            "product_url": "",
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
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
        )
        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "case_type_identification": "ZT-001",
            "document_type_description": "",
            "zaaktype": "",
            "informatieobjecttype": (
                "http://localhost:8003/catalogi/api/v1/"
                "informatieobjecttypen/531f6c1a-97f7-478c-85f0-67d2f23661c7"
            ),
            "product_url": "http://localhost/product/1234abcd-12ab-34cd-56ef-12345abcde10",
            "objects_api_group": None,
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
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
            ["http://localhost/product/1234abcd-12ab-34cd-56ef-12345abcde10"],
        )

    @enable_feature_flag("ZGW_APIS_INCLUDE_DRAFTS")
    def test_allow_registration_with_unpublished_case_types(self):
        zgw_group = ZGWApiGroupConfigFactory.create(
            for_test_docker_compose=True,
            catalogue_domain="DRAFT",
            catalogue_rsin="000000000",
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
        )
        options: RegistrationOptions = {
            "zgw_api_group": zgw_group,
            "case_type_identification": "DRAFT-01",
            "document_type_description": "",
            "zaaktype": "",
            "informatieobjecttype": (
                "http://localhost:8003/catalogi/api/v1/"
                "informatieobjecttypen/3628d25f-f491-4375-a752-39d16bf2dd59"
            ),
            "product_url": "",
            "objects_api_group": None,
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
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
            "zaaktype": "",
            "informatieobjecttype": "",
            "objects_api_group": None,
            "product_url": "",
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
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
                "zaaktype": "",
                "informatieobjecttype": "",
                "organisatie_rsin": "000000000",
                "vertrouwelijkheidaanduiding": "openbaar",
                "objects_api_group": None,
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
        )
        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "case_type_identification": "ZT-001",
            "document_type_description": "Attachment Informatieobjecttype",
            "zaaktype": "",
            "informatieobjecttype": "",
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
                                    "type": "textfield",
                                }
                            ],
                        },
                        {
                            "size": 6,
                            "components": [
                                {
                                    "key": "textField2",
                                    "type": "textfield",
                                }
                            ],
                        },
                    ],
                },
                {
                    "key": "textField3.blah",
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
        )
        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "case_type_identification": "ZT-001",
            "document_type_description": "Attachment Informatieobjecttype",
            "zaaktype": "",
            "informatieobjecttype": "",
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
        submission = SubmissionFactory.from_data(
            {"voornaam": "Foo"},
            bsn="111222333",
            # setup payment although at this level of testing it is not needed
            form__product__price=Decimal("11.35"),
            form__payment_backend="demo",
            completed=True,
            # Pin to a known case & document type version
            completed_on=datetime(2024, 6, 9, 15, 30, 0).replace(tzinfo=UTC),
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
            "zaaktype": "",
            "informatieobjecttype": "",
            "objects_api_group": None,
            "product_url": "",
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
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
                    "key": "field1",
                    "type": "file",
                    "registration": {
                        # attachment informatieobjecttype in docker compose
                        "informatieobjecttype": (
                            "http://localhost:8003/catalogi/api/v1/"
                            "informatieobjecttypen/7755ab0f-9e37-4834-8bbf-158f9f2da38e"
                        ),
                        "bronorganisatie": "100000009",
                        "docVertrouwelijkheidaanduiding": "zeer_geheim",
                        "titel": "TITEL",
                    },
                },
                {
                    "key": "field2",
                    "type": "file",
                    # options should be omitted in the actual call and the document type
                    # defaults must be used
                    "registration": {
                        "informatieobjecttype": "",
                        "bronorganisatie": "",
                        "doc_vertrouwelijkheidaanduiding": "",
                        "titel": "",
                    },
                },
            ],
            bsn="111222333",
            completed=True,
            # Pin to a known case & document type version
            completed_on=datetime(2024, 11, 9, 15, 30, 0).replace(tzinfo=UTC),
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
            "zaaktype": "",
            "informatieobjecttype": "",
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
        )
        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "case_type_identification": "ZT-001",
            "document_type_description": "PDF Informatieobjecttype",
            "zaaktype": "",
            "informatieobjecttype": "",
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
            "zaaktype": "",
            "informatieobjecttype": "",
            "objects_api_group": None,
            "product_url": "",
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
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
            "zaaktype": "",
            "informatieobjecttype": "",
            "objects_api_group": None,
            "product_url": "",
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
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
            "zaaktype": "",
            "informatieobjecttype": "",
            "objects_api_group": None,
            "product_url": "",
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
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
            "zaaktype": "",
            "informatieobjecttype": "",
            "objects_api_group": None,
            "product_url": "",
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
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
                api_root="http://localhost:5010/haalcentraal/api/brp/"
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
            "zaaktype": "",
            "informatieobjecttype": "",
            "product_url": "",
            "objects_api_group": None,
            "partners_roltype": "Partner role type",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
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
        )

        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "PARTN",
                "rsin": "000000000",
            },
            "case_type_identification": "ZAAKTYPE-2020-0000000001",
            "document_type_description": "Partners PDF Informatieobjecttype",
            "zaaktype": "",
            "informatieobjecttype": "",
            "product_url": "",
            "objects_api_group": None,
            "partners_roltype": "Partner role type",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
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
                api_root="http://localhost:5010/haalcentraal/api/brp/"
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

        catalogi_root = self.zgw_group.ztc_service.api_root
        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "CHILD",
                "rsin": "000000000",
            },
            "case_type_identification": "ZAAKTYPE-2020-0000000002",
            "document_type_description": "Children PDF Informatieobjecttype",
            "zaaktype": f"{catalogi_root}zaaktypen/a516793a-cb5f-446d-bfa3-56077c1897be",
            "informatieobjecttype": f"{catalogi_root}informatieobjecttypen/68ce2d9c-fe0f-49cc-a1d6-ddb3d404da35",
            "product_url": "",
            "objects_api_group": None,
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "Children role type",
            "children_description": "",
        }

        prefill_variables(submission)

        # the submitted data needs extra handling because frontend adds some extra field
        # to it which is not happenning here, so we have to update it manually in order
        # to mimic the frontend behaviour
        children_data = submission.data["children"]
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

    @patch(
        "openforms.contrib.haal_centraal.clients.HaalCentraalConfig.get_solo",
        return_value=HaalCentraalConfig(
            brp_personen_service=ServiceFactory.build(
                api_root="http://localhost:5010/haalcentraal/api/brp/"
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

        catalogi_root = self.zgw_group.ztc_service.api_root
        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "CHILD",
                "rsin": "000000000",
            },
            "case_type_identification": "ZAAKTYPE-2020-0000000002",
            "document_type_description": "Children PDF Informatieobjecttype",
            "zaaktype": f"{catalogi_root}zaaktypen/a516793a-cb5f-446d-bfa3-56077c1897be",
            "informatieobjecttype": f"{catalogi_root}informatieobjecttypen/68ce2d9c-fe0f-49cc-a1d6-ddb3d404da35",
            "product_url": "",
            "objects_api_group": None,
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "Children role type",
            "children_description": "",
        }

        prefill_variables(submission)

        # the submitted data needs extra handling because frontend adds some extra field
        # to it which is not happenning here, so we have to update it manually in order
        # to mimic the frontend behaviour
        children_data = submission.data["children"]
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

        catalogi_root = self.zgw_group.ztc_service.api_root
        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "CHILD",
                "rsin": "000000000",
            },
            "case_type_identification": "ZAAKTYPE-2020-0000000002",
            "document_type_description": "Children PDF Informatieobjecttype",
            "zaaktype": f"{catalogi_root}zaaktypen/a516793a-cb5f-446d-bfa3-56077c1897be",
            "informatieobjecttype": f"{catalogi_root}informatieobjecttypen/68ce2d9c-fe0f-49cc-a1d6-ddb3d404da35",
            "product_url": "",
            "objects_api_group": None,
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "Children role type",
            "children_description": "",
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

        catalogi_root = self.zgw_group.ztc_service.api_root
        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "CHILD",
                "rsin": "000000000",
            },
            "case_type_identification": "ZAAKTYPE-2020-0000000002",
            "document_type_description": "Children PDF Informatieobjecttype",
            "zaaktype": f"{catalogi_root}zaaktypen/a516793a-cb5f-446d-bfa3-56077c1897be",
            "informatieobjecttype": f"{catalogi_root}informatieobjecttypen/68ce2d9c-fe0f-49cc-a1d6-ddb3d404da35",
            "product_url": "",
            "objects_api_group": None,
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "Children role type",
            "children_description": "",
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
        )

        catalogi_root = self.zgw_group.ztc_service.api_root
        options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "catalogue": {
                "domain": "CHILD",
                "rsin": "000000000",
            },
            "case_type_identification": "ZAAKTYPE-2020-0000000002",
            "document_type_description": "Children PDF Informatieobjecttype",
            "zaaktype": f"{catalogi_root}zaaktypen/a516793a-cb5f-446d-bfa3-56077c1897be",
            "informatieobjecttype": f"{catalogi_root}informatieobjecttypen/68ce2d9c-fe0f-49cc-a1d6-ddb3d404da35",
            "product_url": "",
            "objects_api_group": None,
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "Children role type",
            "children_description": "",
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
