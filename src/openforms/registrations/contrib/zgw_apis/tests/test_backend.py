import json
import textwrap
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase, override_settings, tag

import requests_mock
from freezegun import freeze_time
from furl import furl
from privates.test import temp_private_root
from zgw_consumers.test import generate_oas_component

from openforms.authentication.tests.factories import RegistratorInfoFactory
from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory
from openforms.contrib.zgw.clients.zaken import CRS_HEADERS
from openforms.registrations.contrib.objects_api.models import ObjectsAPIConfig
from openforms.submissions.constants import PostSubmissionEvents
from openforms.submissions.models import SubmissionStep
from openforms.submissions.tasks import pre_registration
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
)
from openforms.utils.tests.feature_flags import enable_feature_flag
from openforms.utils.tests.vcr import OFVCRMixin

from ....constants import RegistrationAttribute
from ..client import get_documents_client, get_zaken_client
from ..plugin import ZGWRegistration
from ..typing import RegistrationOptions
from .factories import ZGWApiGroupConfigFactory

TEST_FILES = Path(__file__).parent.resolve() / "files"


@temp_private_root()
@requests_mock.Mocker(real_http=False)
class ZGWBackendTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.zgw_group = ZGWApiGroupConfigFactory.create(
            zrc_service__api_root="https://zaken.nl/api/v1/",
            drc_service__api_root="https://documenten.nl/api/v1/",
            ztc_service__api_root="https://catalogus.nl/api/v1/",
        )

    def install_mocks(self, m):
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

    def test_submission_with_zgw_backend_with_natuurlijk_persoon_initiator(self, m):
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
            form__product__price=Decimal("0"),
            form__payment_backend="demo",
            language_code="en",
            completed=True,
        )
        attachment = SubmissionFileAttachmentFactory.create(
            submission_step=submission.steps[0],
        )
        zgw_form_options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "case_type_identification": "",
            "document_type_description": "",
            "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
            "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
            "organisatie_rsin": "000000000",
            "zaak_vertrouwelijkheidaanduiding": "openbaar",
            "doc_vertrouwelijkheidaanduiding": "openbaar",
            "objects_api_group": None,
            "product_url": "",
        }
        self.install_mocks(m)

        plugin = ZGWRegistration("zgw")
        pre_registration_result = plugin.pre_register_submission(
            submission, zgw_form_options
        )
        assert submission.registration_result is not None
        assert isinstance(pre_registration_result.data, dict)
        submission.registration_result.update(pre_registration_result.data)
        submission.save()
        result = plugin.register_submission(submission, zgw_form_options)
        assert result

        self.assertEqual(
            result["document"]["url"],
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
        )
        self.assertEqual(result["rol"]["url"], "https://zaken.nl/api/v1/rollen/1")
        self.assertEqual(result["status"]["url"], "https://zaken.nl/api/v1/statussen/1")
        self.assertEqual(result["zaak"]["url"], "https://zaken.nl/api/v1/zaken/1")
        self.assertEqual(
            result["zaak"]["zaaktype"], "https://catalogi.nl/api/v1/zaaktypen/1"
        )

        self.assertEqual(len(m.request_history), 9)
        (
            create_zaak,
            create_pdf_document,
            relate_pdf_document,
            get_roltypen,
            create_rol,
            get_statustypen,
            create_status,
            create_attachment_document,
            relate_attachment_document,
        ) = m.request_history

        with self.subTest("Create zaak call"):
            create_zaak_body = create_zaak.json()

            self.assertNotIn("kenmerken", create_zaak_body)
            self.assertEqual(create_zaak.method, "POST")
            self.assertEqual(create_zaak.url, "https://zaken.nl/api/v1/zaken")
            self.assertEqual(create_zaak_body["bronorganisatie"], "000000000")
            self.assertEqual(
                create_zaak_body["verantwoordelijkeOrganisatie"],
                "000000000",
            )
            self.assertEqual(
                create_zaak_body["vertrouwelijkheidaanduiding"],
                "openbaar",
            )
            self.assertEqual(
                create_zaak_body["zaaktype"], "https://catalogi.nl/api/v1/zaaktypen/1"
            )
            self.assertEqual(create_zaak_body["betalingsindicatie"], "nvt")

            self.assertEqual(
                create_zaak_body["zaakgeometrie"],
                {
                    "type": "Point",
                    "coordinates": [4.893164274470299, 52.36673378967122],
                },
            )

        with self.subTest("Create summary PDF document"):
            create_eio_body = create_pdf_document.json()

            self.assertEqual(create_pdf_document.method, "POST")
            self.assertEqual(
                create_pdf_document.url,
                "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            )
            self.assertEqual(create_eio_body["bronorganisatie"], "000000000")
            self.assertEqual(create_eio_body["formaat"], "application/pdf")
            self.assertEqual(
                create_eio_body["vertrouwelijkheidaanduiding"],
                "openbaar",
            )
            self.assertEqual(
                create_eio_body["informatieobjecttype"],
                "https://catalogi.nl/api/v1/informatieobjecttypen/1",
            )
            self.assertEqual(create_eio_body["taal"], "eng")

            create_zio_body = relate_pdf_document.json()
            self.assertEqual(relate_pdf_document.method, "POST")
            self.assertEqual(
                relate_pdf_document.url,
                "https://zaken.nl/api/v1/zaakinformatieobjecten",
            )
            self.assertEqual(create_zio_body["zaak"], "https://zaken.nl/api/v1/zaken/1")
            self.assertEqual(
                create_zio_body["informatieobject"],
                "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
            )

        with self.subTest("Create rol"):
            create_rol_body = create_rol.json()

            self.assertEqual(create_rol.method, "POST")
            self.assertEqual(create_rol.url, "https://zaken.nl/api/v1/rollen")
            self.assertEqual(create_zio_body["zaak"], "https://zaken.nl/api/v1/zaken/1")
            self.assertEqual(
                create_rol_body["roltype"],
                "https://catalogus.nl/api/v1/roltypen/1",
            )
            self.assertEqual(
                create_rol_body["betrokkeneIdentificatie"],
                {
                    "voornamen": "Foo",
                    "geboortedatum": "2000-12-31",
                    "inpBsn": "111222333",
                    "voorvoegselGeslachtsnaam": "de",
                    "geslachtsnaam": "Bar",
                    "verblijfsadres": {
                        "aoaPostcode": "1000 AA",
                        "aoaIdentificatie": "OFWORKAROUND",
                    },
                    "voorletters": "J.W.",
                    "geslachtsaanduiding": "m",
                },
            )
            self.assertEqual(
                create_rol_body["betrokkeneType"],
                "natuurlijk_persoon",
            )

        with self.subTest("Create initial status"):
            create_status_body = create_status.json()

            self.assertEqual(create_status.method, "POST")
            self.assertEqual(create_status.url, "https://zaken.nl/api/v1/statussen")
            self.assertEqual(
                create_status_body["zaak"], "https://zaken.nl/api/v1/zaken/1"
            )
            self.assertEqual(
                create_status_body["statustype"],
                "https://catalogus.nl/api/v1/statustypen/1",
            )

        with self.subTest("Create attachment document"):
            create_attachment_body = create_attachment_document.json()

            self.assertEqual(create_attachment_document.method, "POST")
            self.assertEqual(
                create_attachment_document.url,
                "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            )
            self.assertEqual(
                create_attachment_body["bestandsnaam"], attachment.file_name
            )
            self.assertEqual(create_attachment_body["formaat"], attachment.content_type)
            self.assertEqual(create_attachment_body["taal"], "eng")

            relate_attachment_body = relate_attachment_document.json()
            self.assertEqual(relate_attachment_document.method, "POST")
            self.assertEqual(
                relate_attachment_document.url,
                "https://zaken.nl/api/v1/zaakinformatieobjecten",
            )
            self.assertEqual(
                relate_attachment_body["zaak"], "https://zaken.nl/api/v1/zaken/1"
            )
            self.assertEqual(
                relate_attachment_body["informatieobject"],
                "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/2",
            )

    def test_submission_with_zgw_backend_with_vestiging_and_kvk_initiator(self, m):
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
                    "key": "coordinaat",
                    "type": "map",
                    "registration": {
                        "attribute": RegistrationAttribute.locatie_coordinaat,
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
                "coordinaat": {
                    "type": "Point",
                    "coordinates": [4.893164274470299, 52.36673378967122],
                },
                "vestigingsNummer": "87654321",
            },
            kvk="12345678",
            form__product__price=Decimal("0"),
            form__payment_backend="demo",
            completed=True,
        )
        attachment = SubmissionFileAttachmentFactory.create(
            submission_step=submission.steps[0],
        )
        zgw_form_options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "case_type_identification": "",
            "document_type_description": "",
            "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
            "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
            "organisatie_rsin": "000000000",
            "zaak_vertrouwelijkheidaanduiding": "openbaar",
            "doc_vertrouwelijkheidaanduiding": "openbaar",
            "objects_api_group": None,
            "product_url": "",
        }
        self.install_mocks(m)

        plugin = ZGWRegistration("zgw")
        pre_registration_result = plugin.pre_register_submission(
            submission, zgw_form_options
        )
        assert submission.registration_result is not None
        assert isinstance(pre_registration_result.data, dict)
        submission.registration_result.update(pre_registration_result.data)
        submission.save()
        result = plugin.register_submission(submission, zgw_form_options)
        assert result

        self.assertEqual(
            result["document"]["url"],
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
        )
        self.assertEqual(result["rol"]["url"], "https://zaken.nl/api/v1/rollen/1")
        self.assertEqual(result["status"]["url"], "https://zaken.nl/api/v1/statussen/1")
        self.assertEqual(result["zaak"]["url"], "https://zaken.nl/api/v1/zaken/1")
        self.assertEqual(
            result["zaak"]["zaaktype"], "https://catalogi.nl/api/v1/zaaktypen/1"
        )

        self.assertEqual(len(m.request_history), 9)
        (
            create_zaak,
            create_pdf_document,
            relate_pdf_document,
            get_roltypen,
            create_rol,
            get_statustypen,
            create_status,
            create_attachment_document,
            relate_attachment_document,
        ) = m.request_history

        with self.subTest("Create zaak call"):
            create_zaak_body = create_zaak.json()
            self.assertNotIn("kenmerken", create_zaak_body)
            self.assertEqual(create_zaak.method, "POST")
            self.assertEqual(create_zaak.url, "https://zaken.nl/api/v1/zaken")
            self.assertEqual(create_zaak_body["bronorganisatie"], "000000000")
            self.assertEqual(
                create_zaak_body["verantwoordelijkeOrganisatie"],
                "000000000",
            )
            self.assertEqual(
                create_zaak_body["vertrouwelijkheidaanduiding"],
                "openbaar",
            )
            self.assertEqual(
                create_zaak_body["zaaktype"], "https://catalogi.nl/api/v1/zaaktypen/1"
            )
            self.assertEqual(create_zaak_body["betalingsindicatie"], "nvt")

            self.assertEqual(
                create_zaak_body["zaakgeometrie"],
                {
                    "type": "Point",
                    "coordinates": [4.893164274470299, 52.36673378967122],
                },
            )

        with self.subTest("Create summary PDF document"):
            create_eio_body = create_pdf_document.json()
            self.assertEqual(create_pdf_document.method, "POST")
            self.assertEqual(
                create_pdf_document.url,
                "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            )
            self.assertEqual(create_eio_body["bronorganisatie"], "000000000")
            self.assertEqual(create_eio_body["formaat"], "application/pdf")
            self.assertEqual(
                create_eio_body["vertrouwelijkheidaanduiding"],
                "openbaar",
            )
            self.assertEqual(
                create_eio_body["informatieobjecttype"],
                "https://catalogi.nl/api/v1/informatieobjecttypen/1",
            )

            create_zio_body = relate_pdf_document.json()
            self.assertEqual(relate_pdf_document.method, "POST")
            self.assertEqual(
                relate_pdf_document.url,
                "https://zaken.nl/api/v1/zaakinformatieobjecten",
            )
            self.assertEqual(create_zio_body["zaak"], "https://zaken.nl/api/v1/zaken/1")
            self.assertEqual(
                create_zio_body["informatieobject"],
                "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
            )

        with self.subTest("Create rol"):
            create_rol_body = create_rol.json()
            self.assertEqual(create_rol.method, "POST")
            self.assertEqual(create_rol.url, "https://zaken.nl/api/v1/rollen")
            self.assertEqual(create_zio_body["zaak"], "https://zaken.nl/api/v1/zaken/1")
            self.assertEqual(
                create_rol_body["roltype"],
                "https://catalogus.nl/api/v1/roltypen/1",
            )
            self.assertEqual(
                create_rol_body["betrokkeneType"],
                "vestiging",
            )
            self.assertEqual(
                create_rol_body["betrokkeneIdentificatie"],
                {
                    "handelsnaam": ["ACME"],
                    "vestigingsNummer": "87654321",
                    "kvkNummer": "12345678",
                    "innNnpId": "12345678",
                    "statutaireNaam": "ACME",
                    "verblijfsadres": {
                        "aoaPostcode": "1000 AA",
                        "aoaIdentificatie": "OFWORKAROUND",
                    },
                },
            )

        with self.subTest("Create initial status"):
            create_status_body = create_status.json()
            self.assertEqual(create_status.method, "POST")
            self.assertEqual(create_status.url, "https://zaken.nl/api/v1/statussen")
            self.assertEqual(
                create_status_body["zaak"], "https://zaken.nl/api/v1/zaken/1"
            )
            self.assertEqual(
                create_status_body["statustype"],
                "https://catalogus.nl/api/v1/statustypen/1",
            )

        with self.subTest("Create attachment document"):
            create_attachment_body = create_attachment_document.json()
            self.assertEqual(create_attachment_document.method, "POST")
            self.assertEqual(
                create_attachment_document.url,
                "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            )
            self.assertEqual(
                create_attachment_body["bestandsnaam"], attachment.file_name
            )
            self.assertEqual(create_attachment_body["formaat"], attachment.content_type)

            relate_attachment_body = relate_attachment_document.json()
            self.assertEqual(relate_attachment_document.method, "POST")
            self.assertEqual(
                relate_attachment_document.url,
                "https://zaken.nl/api/v1/zaakinformatieobjecten",
            )
            self.assertEqual(
                relate_attachment_body["zaak"], "https://zaken.nl/api/v1/zaken/1"
            )
            self.assertEqual(
                relate_attachment_body["informatieobject"],
                "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/2",
            )

    def test_submission_with_zgw_backend_with_kvk_only_initiator(self, m):
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
                    "key": "coordinaat",
                    "type": "map",
                    "registration": {
                        "attribute": RegistrationAttribute.locatie_coordinaat,
                    },
                },
            ],
            submitted_data={
                "handelsnaam": "ACME",
                "postcode": "1000 AA",
                "coordinaat": {
                    "type": "Point",
                    "coordinates": [4.893164274470299, 52.36673378967122],
                },
            },
            kvk="12345678",
            form__product__price=Decimal("0"),
            form__payment_backend="demo",
            registration_result={
                "zaak": {
                    "url": "https://zaken.nl/api/v1/zaken/1",
                    "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
                }
            },
            completed=True,
        )
        SubmissionFileAttachmentFactory.create(submission_step=submission.steps[0])
        zgw_form_options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "case_type_identification": "",
            "document_type_description": "",
            "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
            "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
            "organisatie_rsin": "000000000",
            "zaak_vertrouwelijkheidaanduiding": "openbaar",
            "doc_vertrouwelijkheidaanduiding": "openbaar",
            "objects_api_group": None,
            "product_url": "",
        }
        self.install_mocks(m)

        plugin = ZGWRegistration("zgw")
        plugin.register_submission(submission, zgw_form_options)

        self.assertEqual(len(m.request_history), 8)
        (
            create_pdf_document,
            relate_pdf_document,
            get_roltypen,
            create_rol,
            get_statustypen,
            create_status,
            create_attachment_document,
            relate_attachment_document,
        ) = m.request_history

        create_rol_body = create_rol.json()
        self.assertEqual(
            create_rol_body["betrokkeneType"],
            "niet_natuurlijk_persoon",
        )
        self.assertEqual(
            create_rol_body["betrokkeneIdentificatie"]["statutaireNaam"],
            "ACME",
        )
        self.assertEqual(
            create_rol_body["betrokkeneIdentificatie"]["innNnpId"],
            "12345678",
        )

    def test_submission_with_zgw_backend_with_vestiging_initiator_kvk_only(self, m):
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
                    "key": "coordinaat",
                    "type": "map",
                    "registration": {
                        "attribute": RegistrationAttribute.locatie_coordinaat,
                    },
                },
            ],
            submitted_data={
                "handelsnaam": "ACME",
                "postcode": "1000 AA",
                "coordinaat": {
                    "type": "Point",
                    "coordinates": [4.893164274470299, 52.36673378967122],
                },
            },
            kvk="12345678",
            form__product__price=Decimal("0"),
            form__payment_backend="demo",
            completed=True,
        )
        attachment = SubmissionFileAttachmentFactory.create(
            submission_step=submission.steps[0],
        )
        zgw_form_options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "case_type_identification": "",
            "document_type_description": "",
            "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
            "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
            "organisatie_rsin": "000000000",
            "zaak_vertrouwelijkheidaanduiding": "openbaar",
            "doc_vertrouwelijkheidaanduiding": "openbaar",
            "objects_api_group": None,
            "product_url": "",
        }
        self.install_mocks(m)

        plugin = ZGWRegistration("zgw")
        pre_registration_result = plugin.pre_register_submission(
            submission, zgw_form_options
        )
        assert submission.registration_result is not None
        assert isinstance(pre_registration_result.data, dict)
        submission.registration_result.update(pre_registration_result.data)
        submission.save()
        result = plugin.register_submission(submission, zgw_form_options)
        assert result

        self.assertEqual(
            result["document"]["url"],
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
        )
        self.assertEqual(result["rol"]["url"], "https://zaken.nl/api/v1/rollen/1")
        self.assertEqual(result["status"]["url"], "https://zaken.nl/api/v1/statussen/1")
        self.assertEqual(result["zaak"]["url"], "https://zaken.nl/api/v1/zaken/1")
        self.assertEqual(
            result["zaak"]["zaaktype"], "https://catalogi.nl/api/v1/zaaktypen/1"
        )

        self.assertEqual(len(m.request_history), 9)
        (
            create_zaak,
            create_pdf_document,
            relate_pdf_document,
            get_roltypen,
            create_rol,
            get_statustypen,
            create_status,
            create_attachment_document,
            relate_attachment_document,
        ) = m.request_history

        with self.subTest("Create zaak call"):
            create_zaak_body = create_zaak.json()

            self.assertNotIn("kenmerken", create_zaak_body)
            self.assertEqual(create_zaak.method, "POST")
            self.assertEqual(create_zaak.url, "https://zaken.nl/api/v1/zaken")
            self.assertEqual(create_zaak_body["bronorganisatie"], "000000000")
            self.assertEqual(
                create_zaak_body["verantwoordelijkeOrganisatie"],
                "000000000",
            )
            self.assertEqual(
                create_zaak_body["vertrouwelijkheidaanduiding"],
                "openbaar",
            )
            self.assertEqual(
                create_zaak_body["zaaktype"], "https://catalogi.nl/api/v1/zaaktypen/1"
            )
            self.assertEqual(create_zaak_body["betalingsindicatie"], "nvt")

            self.assertEqual(
                create_zaak_body["zaakgeometrie"],
                {
                    "type": "Point",
                    "coordinates": [4.893164274470299, 52.36673378967122],
                },
            )

        with self.subTest("Create summary PDF document"):
            create_eio_body = create_pdf_document.json()

            self.assertEqual(create_pdf_document.method, "POST")
            self.assertEqual(
                create_pdf_document.url,
                "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            )
            self.assertEqual(create_eio_body["bronorganisatie"], "000000000")
            self.assertEqual(create_eio_body["formaat"], "application/pdf")
            self.assertEqual(
                create_eio_body["vertrouwelijkheidaanduiding"],
                "openbaar",
            )
            self.assertEqual(
                create_eio_body["informatieobjecttype"],
                "https://catalogi.nl/api/v1/informatieobjecttypen/1",
            )

            create_zio_body = relate_pdf_document.json()
            self.assertEqual(relate_pdf_document.method, "POST")
            self.assertEqual(
                relate_pdf_document.url,
                "https://zaken.nl/api/v1/zaakinformatieobjecten",
            )
            self.assertEqual(create_zio_body["zaak"], "https://zaken.nl/api/v1/zaken/1")
            self.assertEqual(
                create_zio_body["informatieobject"],
                "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
            )

        with self.subTest("Create rol"):
            create_rol_body = create_rol.json()

            self.assertEqual(create_rol.method, "POST")
            self.assertEqual(create_rol.url, "https://zaken.nl/api/v1/rollen")
            self.assertEqual(create_zio_body["zaak"], "https://zaken.nl/api/v1/zaken/1")
            self.assertEqual(
                create_rol_body["roltype"],
                "https://catalogus.nl/api/v1/roltypen/1",
            )
            self.assertEqual(
                create_rol_body["betrokkeneIdentificatie"],
                {
                    "handelsnaam": ["ACME"],
                    "innNnpId": "12345678",
                    "kvkNummer": "12345678",
                    "statutaireNaam": "ACME",
                    "verblijfsadres": {
                        "aoaPostcode": "1000 AA",
                        "aoaIdentificatie": "OFWORKAROUND",
                    },
                },
            )

        with self.subTest("Create initial status"):
            create_status_body = create_status.json()

            self.assertEqual(create_status.method, "POST")
            self.assertEqual(create_status.url, "https://zaken.nl/api/v1/statussen")
            self.assertEqual(
                create_status_body["zaak"], "https://zaken.nl/api/v1/zaken/1"
            )
            self.assertEqual(
                create_status_body["statustype"],
                "https://catalogus.nl/api/v1/statustypen/1",
            )

        with self.subTest("Create attachment document"):
            create_attachment_body = create_attachment_document.json()

            self.assertEqual(create_attachment_document.method, "POST")
            self.assertEqual(
                create_attachment_document.url,
                "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            )
            self.assertEqual(
                create_attachment_body["bestandsnaam"], attachment.file_name
            )
            self.assertEqual(create_attachment_body["formaat"], attachment.content_type)

            relate_attachment_body = relate_attachment_document.json()
            self.assertEqual(relate_attachment_document.method, "POST")
            self.assertEqual(
                relate_attachment_document.url,
                "https://zaken.nl/api/v1/zaakinformatieobjecten",
            )
            self.assertEqual(
                relate_attachment_body["zaak"], "https://zaken.nl/api/v1/zaken/1"
            )
            self.assertEqual(
                relate_attachment_body["informatieobject"],
                "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/2",
            )

    @override_settings(LANGUAGE_CODE="en")
    def test_submission_with_registrator(self, m):
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
                    "key": "coordinaat",
                    "type": "map",
                    "registration": {
                        "attribute": RegistrationAttribute.locatie_coordinaat,
                    },
                },
            ],
            submitted_data={
                "handelsnaam": "ACME",
                "postcode": "1000 AA",
                "coordinaat": {
                    "type": "Point",
                    "coordinates": [4.893164274470299, 52.36673378967122],
                },
            },
            kvk="12345678",
            form__product__price=Decimal("0"),
            form__payment_backend="demo",
            registration_result={
                "zaak": {
                    "url": "https://zaken.nl/api/v1/zaken/1",
                    "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
                }
            },
        )
        RegistratorInfoFactory.create(submission=submission, value="123456782")
        zgw_form_options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "case_type_identification": "",
            "document_type_description": "",
            "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
            "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
            "organisatie_rsin": "000000000",
            "zaak_vertrouwelijkheidaanduiding": "openbaar",
            "doc_vertrouwelijkheidaanduiding": "openbaar",
            "medewerker_roltype": "Some description",
            "objects_api_group": None,
            "product_url": "",
        }
        self.install_mocks(m)
        m.get(
            "https://catalogus.nl/api/v1/roltypen?zaaktype=https%3A%2F%2Fcatalogi.nl%2Fapi%2Fv1%2Fzaaktypen%2F1",
            status_code=200,
            json={
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    generate_oas_component(
                        "catalogi",
                        "schemas/RolType",
                        url="https://catalogus.nl/api/v1/roltypen/111",
                        omschrijving="Some description",
                    )
                ],
            },
            headers={"API-version": "1.0.0"},
        )

        plugin = ZGWRegistration("zgw")
        result = plugin.register_submission(submission, zgw_form_options)
        assert result

        self.assertIn("medewerker_rol", result)

        self.assertEqual(len(m.request_history), 8)
        (
            create_pdf_document,
            relate_pdf_document,
            get_roltypen,
            create_rol,
            get_roltypen2,
            create_medewerker_rol,
            get_statustypen,
            create_status,
        ) = m.request_history

        post_data = create_medewerker_rol.json()
        self.assertEqual(post_data["betrokkeneType"], "medewerker")
        self.assertEqual(
            post_data["roltoelichting"],
            "Employee who registered the case on behalf of the customer.",
        )
        self.assertEqual(
            post_data["roltype"],
            "https://catalogus.nl/api/v1/roltypen/111",
        )
        self.assertEqual(
            post_data["betrokkeneIdentificatie"]["identificatie"],
            "123456782",
        )

    def test_submission_with_product(self, m):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "textfield",
                    "type": "textfield",
                },
            ],
            submitted_data={
                "textfield": "Foo",
            },
            completed=True,
        )
        zgw_form_options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "case_type_identification": "",
            "document_type_description": "",
            "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
            "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
            "product_url": "https://example.com",
            "objects_api_group": None,
        }
        self.install_mocks(m)

        plugin = ZGWRegistration("zgw")
        pre_registration_result = plugin.pre_register_submission(
            submission, zgw_form_options
        )
        assert submission.registration_result is not None
        assert isinstance(pre_registration_result.data, dict)
        submission.registration_result.update(pre_registration_result.data)
        submission.save()
        result = plugin.register_submission(submission, zgw_form_options)
        assert result

        self.assertEqual(result["zaak"]["url"], "https://zaken.nl/api/v1/zaken/1")
        self.assertEqual(
            result["zaak"]["zaaktype"], "https://catalogi.nl/api/v1/zaaktypen/1"
        )

        create_zaak = m.request_history[0]

        with self.subTest("Create zaak call"):
            create_zaak_body = create_zaak.json()

            self.assertEqual(create_zaak.url, "https://zaken.nl/api/v1/zaken")
            self.assertEqual(
                create_zaak_body["productenOfDiensten"],
                ["https://example.com"],
            )
            self.assertEqual(
                create_zaak_body["zaaktype"], "https://catalogi.nl/api/v1/zaaktypen/1"
            )

    def test_submission_roltype_initiator_not_found(self, m):
        submission = SubmissionFactory.create(
            completed=True,
            with_report=True,
            registration_result={
                "zaak": {
                    "url": "https://zaken.nl/api/v1/zaken/1",
                    "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
                }
            },
        )
        zgw_form_options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "case_type_identification": "",
            "document_type_description": "",
            "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
            "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
            "organisatie_rsin": "000000000",
            "zaak_vertrouwelijkheidaanduiding": "openbaar",
            "doc_vertrouwelijkheidaanduiding": "openbaar",
            "objects_api_group": None,
            "product_url": "",
        }
        self.install_mocks(m)
        roltypen_url = furl("https://catalogus.nl/api/v1/roltypen").set(
            {
                "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
                "omschrijvingGeneriek": "initiator",
            }
        )
        m.get(
            str(roltypen_url),
            status_code=200,
            json={"count": 0, "next": None, "previous": None, "results": []},
            headers={"API-version": "1.0.0"},
        )

        plugin = ZGWRegistration("zgw")
        result = plugin.register_submission(submission, zgw_form_options)
        assert result

        self.assertIsNone(result["rol"])

    def test_retried_registration_with_internal_reference(self, m):
        """
        Assert that the internal reference is included in the "kenmerken".
        """
        submission = SubmissionFactory.from_components(
            completed_not_preregistered=True,
            needs_on_completion_retry=True,
            public_registration_reference="OF-1234",
            components_list=[{"key": "dummy"}],
            form__registration_backend="zgw-create-zaak",
            form__registration_backend_options={
                "zgw_api_group": self.zgw_group.pk,
                "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
                "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
                "organisatie_rsin": "000000000",
                "vertrouwelijkheidaanduiding": "openbaar",
                "objects_api_group": None,
            },
        )
        self.install_mocks(m)

        pre_registration(submission.pk, PostSubmissionEvents.on_retry)

        create_zaak = m.request_history[0]
        create_zaak_body = create_zaak.json()
        self.assertEqual(
            create_zaak_body["kenmerken"],
            [
                {
                    "kenmerk": "OF-1234",
                    "bron": "Open Formulieren",
                }
            ],
        )

    @freeze_time("2021-01-01 10:00")
    def test_register_and_update_paid_product(self, m):
        submission = SubmissionFactory.from_data(
            {"voornaam": "Foo"},
            # setup payment although at this level of testing it is not needed
            form__product__price=Decimal("11.35"),
            form__payment_backend="demo",
        )
        self.assertTrue(submission.payment_required)
        zgw_form_options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "case_type_identification": "",
            "document_type_description": "",
            "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
            "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
            "organisatie_rsin": "000000000",
            "zaak_vertrouwelijkheidaanduiding": "openbaar",
            "doc_vertrouwelijkheidaanduiding": "openbaar",
            "objects_api_group": None,
            "product_url": "",
        }
        self.install_mocks(m)
        m.patch(
            "https://zaken.nl/api/v1/zaken/1",
            status_code=200,
            json=generate_oas_component(
                "zaken",
                "schemas/Zaak",
                url="https://zaken.nl/api/v1/zaken/1",
                zaaktype="https://catalogi.nl/api/v1/zaaktypen/1",
            ),
        )

        plugin = ZGWRegistration("zgw")
        pre_registration_result = plugin.pre_register_submission(
            submission, zgw_form_options
        )

        submission.public_registration_reference = pre_registration_result.reference
        assert submission.registration_result is not None
        assert isinstance(pre_registration_result.data, dict)
        submission.registration_result.update(pre_registration_result.data)
        submission.save()

        result = plugin.register_submission(submission, zgw_form_options)
        assert result

        self.assertEqual(result["zaak"]["url"], "https://zaken.nl/api/v1/zaken/1")
        submission.registration_result = result
        submission.save()

        # check initial payment status
        create_zaak_body = m.request_history[0].json()
        self.assertEqual(create_zaak_body["betalingsindicatie"], "nog_niet")
        self.assertNotIn("laatsteBetaaldatum", create_zaak_body)

        # run the actual update
        plugin.update_payment_status(submission, {"zgw_api_group": self.zgw_group})

        patch_zaak_body = m.last_request.json()
        self.assertEqual(patch_zaak_body["betalingsindicatie"], "geheel")
        self.assertEqual(
            patch_zaak_body["laatsteBetaaldatum"], "2021-01-01T10:00:00+00:00"
        )

    @tag("sentry-334882")
    def test_submission_with_zgw_backend_override_fields(self, m):
        """Assert that override of default values for the ZGW backend works"""
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "field1",
                    "type": "file",
                    "registration": {
                        "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/10",
                        "bronorganisatie": "100000009",
                        "docVertrouwelijkheidaanduiding": "zeer_geheim",
                        "titel": "TITEL",
                    },
                },
                {
                    "key": "field2",
                    "type": "file",
                    "registration": {
                        "informatieobjecttype": "",
                        "bronorganisatie": "",
                        "doc_vertrouwelijkheidaanduiding": "",
                        "titel": "",
                    },
                },
            ],
            registration_result={
                "zaak": {
                    "url": "https://zaken.nl/api/v1/zaken/1",
                    "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
                }
            },
            completed=True,
        )
        zgw_form_options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "case_type_identification": "",
            "document_type_description": "",
            "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
            "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
            "organisatie_rsin": "000000000",
            "zaak_vertrouwelijkheidaanduiding": "openbaar",
            "objects_api_group": None,
            "product_url": "",
        }
        SubmissionFileAttachmentFactory.create(
            submission_step=SubmissionStep.objects.first(),
            file_name="attachment1.jpg",
            form_key="field1",
            _component_configuration_path="components.0",
        )
        SubmissionFileAttachmentFactory.create(
            submission_step=SubmissionStep.objects.first(),
            file_name="attachment2.jpg",
            form_key="field2",
            _component_configuration_path="components.1",
        )
        self.install_mocks(m)

        plugin = ZGWRegistration("zgw")
        plugin.register_submission(submission, zgw_form_options)

        self.assertEqual(len(m.request_history), 10)
        (
            create_pdf_document,
            relate_pdf_document,
            get_roltypen,
            create_rol,
            get_statustypen,
            create_status,
            create_attachment1_document,
            relate_attachment1_document,
            create_attachment2_document,
            relate_attachment2_document,
        ) = m.request_history

        with self.subTest("Attachment 1: override fields"):
            # Verify attachments
            document_create_attachment1_body = create_attachment1_document.json()
            self.assertEqual(create_attachment1_document.method, "POST")
            self.assertEqual(
                create_attachment1_document.url,
                "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            )

            # Use override fields
            self.assertEqual(
                document_create_attachment1_body["bestandsnaam"], "attachment1.jpg"
            )
            self.assertEqual(
                document_create_attachment1_body["informatieobjecttype"],
                "https://catalogi.nl/api/v1/informatieobjecttypen/10",
            )
            self.assertEqual(
                document_create_attachment1_body["bronorganisatie"],
                "100000009",
            )
            self.assertEqual(
                document_create_attachment1_body["vertrouwelijkheidaanduiding"],
                "zeer_geheim",
            )
            self.assertEqual(
                document_create_attachment1_body["titel"],
                "TITEL",
            )

        with self.subTest("Attachment 2: defaults values"):
            # Verify attachments
            document_create_attachment2_body = create_attachment2_document.json()
            self.assertEqual(create_attachment2_document.method, "POST")
            self.assertEqual(
                create_attachment2_document.url,
                "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            )
            # Use default IOType
            self.assertEqual(
                document_create_attachment2_body["bestandsnaam"], "attachment2.jpg"
            )
            self.assertEqual(
                document_create_attachment2_body["informatieobjecttype"],
                "https://catalogi.nl/api/v1/informatieobjecttypen/1",
            )
            self.assertEqual(
                document_create_attachment2_body["bronorganisatie"],
                "000000000",
            )
            # Sentry 334882 - "" is not a valid choice, validation error from Documenten API.
            # This is because you either need to *not* specify the key, or provide a valid value.
            self.assertNotIn(
                "vertrouwelijkheidaanduiding", document_create_attachment2_body
            )
            # if no title is explicitly provided, the file name should be inserted
            self.assertEqual(
                document_create_attachment2_body["titel"], "attachment2.jpg"
            )

    def test_zgw_backend_default_author(self, m):
        """Assert that the default values for the ZGW API configuration are inserted

        * default author: "Aanvrager"
        """
        attachment = SubmissionFileAttachmentFactory.create(
            submission_step__submission__completed_not_preregistered=True,
            submission_step__submission__with_report=True,
        )
        submission = attachment.submission_step.submission
        zgw_form_options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "case_type_identification": "",
            "document_type_description": "",
            "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
            "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
            "objects_api_group": None,
            "product_url": "",
        }
        self.install_mocks(m)

        plugin = ZGWRegistration("zgw")
        pre_registration_result = plugin.pre_register_submission(
            submission, zgw_form_options
        )
        submission.registration_result.update(pre_registration_result.data)
        submission.save()
        plugin.register_submission(submission, zgw_form_options)

        self.assertEqual(len(m.request_history), 9)
        (
            create_zaak,
            create_pdf_document,
            relate_pdf_document,
            get_roltypen,
            create_rol,
            get_statustypen,
            create_status,
            create_attachment_document,
            relate_attachment_document,
        ) = m.request_history

        with self.subTest("Create zaak call"):
            create_zaak_body = create_zaak.json()

            # make sure we have the right request
            self.assertEqual(create_zaak.method, "POST")
            self.assertEqual(create_zaak.url, "https://zaken.nl/api/v1/zaken")

            # check defaults
            self.assertNotIn("vertrouwelijkheidaanduiding", create_zaak_body)

        with self.subTest("Create summary PDF document"):
            create_eio_body = create_pdf_document.json()

            # make sure we have the right request
            self.assertEqual(create_zaak.method, "POST")
            self.assertEqual(
                create_pdf_document.url,
                "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            )

            # check defaults
            self.assertNotIn("vertrouwelijkheidaanduiding", create_eio_body)
            self.assertEqual(create_eio_body["auteur"], "Aanvrager")

        with self.subTest("Create attachment document"):
            create_attachment_body = create_attachment_document.json()

            # make sure we have the right request
            self.assertEqual(create_attachment_document.method, "POST")
            self.assertEqual(
                create_attachment_document.url,
                "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            )
            # check defaults
            self.assertNotIn("vertrouwelijkheidaanduiding", create_eio_body)
            self.assertEqual(create_attachment_body["auteur"], "Aanvrager")

    def test_zgw_backend_document_ontvangstdatum(self, m):
        attachment = SubmissionFileAttachmentFactory.create(
            submission_step__submission__completed_not_preregistered=True,
            submission_step__submission__with_report=True,
        )
        submission = attachment.submission_step.submission
        zgw_form_options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "case_type_identification": "",
            "document_type_description": "",
            "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
            "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
            "objects_api_group": None,
            "product_url": "",
        }
        self.install_mocks(m)

        plugin = ZGWRegistration("zgw")
        pre_registration_result = plugin.pre_register_submission(
            submission, zgw_form_options
        )
        submission.registration_result.update(pre_registration_result.data)
        submission.save()
        plugin.register_submission(submission, zgw_form_options)

        self.assertEqual(len(m.request_history), 9)
        (
            create_zaak,
            create_pdf_document,
            relate_pdf_document,
            get_roltypen,
            create_rol,
            get_statustypen,
            create_status,
            create_attachment_document,
            relate_attachment_document,
        ) = m.request_history

        create_attachment_body = create_attachment_document.json()

        self.assertIsNotNone(create_attachment_body["ontvangstdatum"])

    def test_zgw_backend_defaults_empty_string(self, m):
        """Assert that empty strings for new fields are overriden with defaults

        This test ensures that old DB entries won't have an empty string as the value
        of newly added fields like `auteur`.
        """
        attachment = SubmissionFileAttachmentFactory.create(
            submission_step__submission__completed_not_preregistered=True,
            submission_step__submission__with_report=True,
            file_name="attachment1.jpg",
            form_key="field1",
            submission_step__submission__registration_result={
                "zaak": {
                    "url": "https://zaken.nl/api/v1/zaken/1",
                    "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
                }
            },
        )
        submission = attachment.submission_step.submission
        zgw_form_options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "case_type_identification": "",
            "document_type_description": "",
            "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
            "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
            "auteur": "",
            "objects_api_group": None,
            "product_url": "",
        }
        self.install_mocks(m)

        plugin = ZGWRegistration("zgw")
        plugin.register_submission(submission, zgw_form_options)

        self.assertEqual(len(m.request_history), 8)
        (
            create_pdf_document,
            relate_pdf_document,
            get_roltypen,
            create_rol,
            get_statustypen,
            create_status,
            create_attachment_document,
            relate_attachment_document,
        ) = m.request_history

        document_create_attachment_body = create_attachment_document.json()
        self.assertEqual(document_create_attachment_body["auteur"], "Aanvrager")

    @tag("sentry-334882")
    def test_zgw_backend_unspecified_zaakvertrouwelijkheidaanduiding(self, m):
        submission = SubmissionFactory.create(
            completed_not_preregistered=True,
            with_report=True,
        )
        zgw_form_options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "case_type_identification": "",
            "document_type_description": "",
            "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
            "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
            "auteur": "",
            "zaak_vertrouwelijkheidaanduiding": "",  # type: ignore
            "objects_api_group": None,
            "product_url": "",
        }
        self.install_mocks(m)
        plugin = ZGWRegistration("zgw")

        plugin.pre_register_submission(submission, zgw_form_options)

        create_zaak = m.last_request
        self.assertEqual(create_zaak.url, "https://zaken.nl/api/v1/zaken")
        self.assertEqual(create_zaak.method, "POST")
        body = create_zaak.json()
        self.assertNotIn("vertrouwelijkheidaanduiding", body)

    def test_zgw_backend_has_reference_after_pre_submission(self, m):
        m.post(
            "https://zaken.nl/api/v1/zaken",
            status_code=201,
            json=generate_oas_component(
                "zaken",
                "schemas/Zaak",
                url="https://zaken.nl/api/v1/zaken/1",
                zaaktype="https://catalogi.nl/api/v1/zaaktypen/1",
                identificatie="ZAAK-OF-TEST",
            ),
        )
        submission = SubmissionFactory.create(
            form__registration_backend="zgw-create-zaak",
            form__registration_backend_options={
                "zgw_api_group": self.zgw_group.pk,
                "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
                "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
                "objects_api_group": None,
            },
            completed_not_preregistered=True,
        )
        assert submission.public_registration_reference == ""

        pre_registration(submission.id, PostSubmissionEvents.on_completion)

        submission.refresh_from_db()
        self.assertEqual(submission.public_registration_reference, "ZAAK-OF-TEST")

    @tag("gh-3649")
    def test_document_size_argument_present(self, m):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "field1",
                    "type": "file",
                },
            ],
            completed=True,
        )
        zgw_form_options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "case_type_identification": "",
            "document_type_description": "",
            "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
            "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
            "organisatie_rsin": "000000000",
            "zaak_vertrouwelijkheidaanduiding": "openbaar",
            "objects_api_group": None,
            "product_url": "",
        }
        SubmissionFileAttachmentFactory.create(
            submission_step=SubmissionStep.objects.first(),
            content__data=b"content",
            file_name="attachment1.txt",
            form_key="field1",
            _component_configuration_path="components.0",
        )

        self.install_mocks(m)

        plugin = ZGWRegistration("zgw")
        pre_registration_result = plugin.pre_register_submission(
            submission, zgw_form_options
        )

        submission.public_registration_reference = pre_registration_result.reference
        assert submission.registration_result is not None
        assert isinstance(pre_registration_result.data, dict)
        submission.registration_result.update(pre_registration_result.data)
        submission.save()

        plugin.register_submission(submission, zgw_form_options)

        (
            create_zaak,
            create_pdf_document,
            relate_pdf_document,
            get_roltypen,
            create_rol,
            get_statustypen,
            create_status,
            create_attachment1_document,
            relate_attachment1_document,
        ) = m.request_history

        self.assertIn("bestandsomvang", json.loads(create_pdf_document.body))

        attachment_data = json.loads(create_attachment1_document.body)

        self.assertIn("bestandsomvang", attachment_data)
        self.assertEqual(attachment_data["bestandsomvang"], 7)

    @patch(
        "openforms.registrations.contrib.objects_api.models.ObjectsAPIConfig.get_solo"
    )
    def test_submission_with_zgw_and_objects_api_backends(self, m, obj_api_config):
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

        # unused group
        ObjectsAPIGroupConfigFactory.create(
            objects_service__api_root="https://objecten2.nl/api/v1/",
            organisatie_rsin="111222333",
        )
        objects_api_group = ObjectsAPIGroupConfigFactory.create(
            objects_service__api_root="https://objecten.nl/api/v1/",
            organisatie_rsin="000000000",
        )

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

        def get_create_json_for_zaakobject(req, ctx):
            request_body = req.json()
            return {
                "url": "https://zaken.nl/api/v1/zaakobjecten/2c556247-aaa2-48d5-a94c-0aa72c78323a",
                "uuid": "2c556247-aaa2-48d5-a94c-0aa72c78323a",
                "zaak": request_body["zaak"],
                "object": request_body["object"],
                "zaakobjecttype": None,
                "objectType": "overige",
                "objectTypeOverige": "",
                "objectTypeOverigeDefinitie": {
                    "url": request_body["objectTypeOverigeDefinitie"]["url"],
                    "schema": ".jsonSchema",
                    "objectData": ".record.data",
                },
                "relatieomschrijving": "",
                "objectIdentificatie": None,
            }

        m.post(
            "https://objecten.nl/api/v1/objects",
            status_code=201,
            json=get_create_json_for_object,
        )
        m.post(
            "https://zaken.nl/api/v1/zaakobjecten",
            status_code=201,
            json=get_create_json_for_zaakobject,
        )

        obj_api_config.return_value = config

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
            form_definition_kwargs={"slug": "test"},
            registration_result={
                "zaak": {
                    "url": "https://zaken.nl/api/v1/zaken/1",
                    "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
                }
            },
        )
        zgw_form_options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "case_type_identification": "",
            "document_type_description": "",
            "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
            "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
            "organisatie_rsin": "000000000",
            "zaak_vertrouwelijkheidaanduiding": "openbaar",
            "doc_vertrouwelijkheidaanduiding": "openbaar",
            "objects_api_group": objects_api_group,
            "objecttype": "https://objecttypen.nl/api/v1/objecttypes/2",
            "objecttype_version": 1,
            "product_url": "",
        }
        self.install_mocks(m)

        plugin = ZGWRegistration("zgw")
        result = plugin.register_submission(submission, zgw_form_options)
        assert result

        self.assertEqual(
            result["document"]["url"],
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
        )
        self.assertEqual(result["rol"]["url"], "https://zaken.nl/api/v1/rollen/1")
        self.assertEqual(result["status"]["url"], "https://zaken.nl/api/v1/statussen/1")
        self.assertEqual(result["zaak"]["url"], "https://zaken.nl/api/v1/zaken/1")
        self.assertEqual(
            result["zaak"]["zaaktype"], "https://catalogi.nl/api/v1/zaaktypen/1"
        )
        self.assertEqual(
            result["objects_api_object"],
            {
                "url": "https://objecten.nl/api/v1/objects/1",
                "uuid": "095be615-a8ad-4c33-8e9c-c7612fbf6c9f",
                "type": "https://objecttypen.nl/api/v1/objecttypes/2",
                "record": {
                    "index": 0,
                    "typeVersion": 1,
                    "data": {
                        "data": {
                            "test": {
                                "voorletters": "J.W.",
                                "voornaam": "Foo",
                                "achternaam": "Bar",
                                "tussenvoegsel": "de",
                                "geboortedatum": "2000-12-31",
                                "geslachtsaanduiding": "mannelijk",
                                "postcode": "1000 AA",
                                "coordinaat": {
                                    "type": "Point",
                                    "coordinates": [
                                        4.893164274470299,
                                        52.36673378967122,
                                    ],
                                },
                            }
                        },
                        "type": "ProductAanvraag",
                        "bsn": "111222333",
                        "submission_id": str(submission.uuid),
                        "language_code": "en",
                    },
                    "startAt": date.today().isoformat(),
                    "geometry": {
                        "type": "Point",
                        "coordinates": [4.893164274470299, 52.36673378967122],
                    },
                    "endAt": None,
                    "registrationAt": date.today().isoformat(),
                    "correctionFor": 0,
                    "correctedBy": "",
                },
            },
        )
        self.assertEqual(
            result["zaakobject"],
            {
                "url": "https://zaken.nl/api/v1/zaakobjecten/2c556247-aaa2-48d5-a94c-0aa72c78323a",
                "uuid": "2c556247-aaa2-48d5-a94c-0aa72c78323a",
                "zaak": "https://zaken.nl/api/v1/zaken/1",
                "object": "https://objecten.nl/api/v1/objects/1",
                "zaakobjecttype": None,
                "objectType": "overige",
                "objectTypeOverige": "",
                "objectTypeOverigeDefinitie": {
                    "url": "https://objecttypen.nl/api/v1/objecttypes/2/versions/1",
                    "schema": ".jsonSchema",
                    "objectData": ".record.data",
                },
                "relatieomschrijving": "",
                "objectIdentificatie": None,
            },
        )

    def test_submission_with_multiple_eigenschappen_creation(self, m):
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
            language_code="en",
            form_definition_kwargs={"slug": "test-eigenschappen"},
            registration_result={
                "zaak": {
                    "url": "https://zaken.nl/api/v1/zaken/1",
                    "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
                }
            },
        )
        zgw_form_options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "case_type_identification": "",
            "document_type_description": "",
            "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
            "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
            "organisatie_rsin": "000000000",
            "zaak_vertrouwelijkheidaanduiding": "openbaar",
            "doc_vertrouwelijkheidaanduiding": "openbaar",
            "property_mappings": [
                {"component_key": "textField1", "eigenschap": "a property name"},
                {"component_key": "textField2", "eigenschap": "second property"},
            ],
            "objects_api_group": None,
            "product_url": "",
        }
        self.install_mocks(m)

        m.get(
            "https://catalogus.nl/api/v1/eigenschappen?zaaktype=https%3A%2F%2Fcatalogi.nl%2Fapi%2Fv1%2Fzaaktypen%2F1",
            status_code=200,
            json={
                "count": 2,
                "next": None,
                "previous": None,
                "results": [
                    generate_oas_component(
                        "catalogi",
                        "schemas/Eigenschap",
                        url="https://zaken.nl/catalogi/api/v1/eigenschappen/1",
                        naam="a property name",
                        definitie="a definition",
                        specificatie={
                            "groep": "",
                            "formaat": "tekst",
                            "lengte": "14",
                            "kardinaliteit": "1",
                            "waardenverzameling": [],
                        },
                        toelichting="",
                        zaaktype="https://zaken.nl/api/v1/zaaktypen/1",
                    ),
                    generate_oas_component(
                        "catalogi",
                        "schemas/Eigenschap",
                        url="https://zaken.nl/catalogi/api/v1/eigenschappen/2",
                        naam="second property",
                        definitie="a definition",
                        specificatie={
                            "groep": "",
                            "formaat": "tekst",
                            "lengte": "14",
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
            [
                {
                    "status_code": 201,
                    "json": generate_oas_component(
                        "catalogi",
                        "schemas/Eigenschap",
                        url="https://zaken.nl/zaken/api/v1/zaken/1/zaakeigenschappen/1",
                        uuid=1,
                        zaak="https://zaken.nl/api/v1/zaken/1",
                        eigenschap="https://zaken.nl/catalogi/api/v1/eigenschappen/1",
                        naam="a property name",
                        waarde="some data",
                        definitie="a definition",
                        specificatie={
                            "groep": "",
                            "formaat": "tekst",
                            "lengte": "14",
                            "kardinaliteit": "1",
                            "waardenverzameling": [],
                        },
                        toelichting="",
                        zaaktype="https://zaken.nl/api/v1/zaaktypen/1",
                    ),
                },
                {
                    "status_code": 201,
                    "json": generate_oas_component(
                        "catalogi",
                        "schemas/Eigenschap",
                        url="https://zaken.nl/zaken/api/v1/zaken/1/zaakeigenschappen/2",
                        uuid=2,
                        zaak="https://zaken.nl/api/v1/zaken/1",
                        eigenschap="https://zaken.nl/catalogi/api/v1/eigenschappen/2",
                        naam="second property",
                        waarde="more data",
                        definitie="a definition",
                        specificatie={
                            "groep": "",
                            "formaat": "tekst",
                            "lengte": "14",
                            "kardinaliteit": "1",
                            "waardenverzameling": [],
                        },
                        toelichting="",
                        zaaktype="https://zaken.nl/api/v1/zaaktypen/1",
                    ),
                },
            ],
        )

        plugin = ZGWRegistration("zgw")
        result = plugin.register_submission(submission, zgw_form_options)
        assert result

        self.assertEqual(
            result["zaakeigenschappen"]["1"],
            {
                "url": "https://zaken.nl/zaken/api/v1/zaken/1/zaakeigenschappen/1",
                "uuid": 1,
                "zaak": "https://zaken.nl/api/v1/zaken/1",
                "eigenschap": "https://zaken.nl/catalogi/api/v1/eigenschappen/1",
                "naam": "a property name",
                "waarde": "some data",
                "definitie": "a definition",
                "specificatie": {
                    "groep": "",
                    "formaat": "tekst",
                    "lengte": "14",
                    "kardinaliteit": "1",
                    "waardenverzameling": [],
                },
                "toelichting": "",
                "zaaktype": "https://zaken.nl/api/v1/zaaktypen/1",
            },
        )
        self.assertEqual(
            result["zaakeigenschappen"]["2"],
            {
                "url": "https://zaken.nl/zaken/api/v1/zaken/1/zaakeigenschappen/2",
                "uuid": 2,
                "zaak": "https://zaken.nl/api/v1/zaken/1",
                "eigenschap": "https://zaken.nl/catalogi/api/v1/eigenschappen/2",
                "naam": "second property",
                "waarde": "more data",
                "definitie": "a definition",
                "specificatie": {
                    "groep": "",
                    "formaat": "tekst",
                    "lengte": "14",
                    "kardinaliteit": "1",
                    "waardenverzameling": [],
                },
                "toelichting": "",
                "zaaktype": "https://zaken.nl/api/v1/zaaktypen/1",
            },
        )

    def test_submission_with_nested_component_columns_and_eigenschap(self, m):
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
            language_code="en",
            form_definition_kwargs={"slug": "test-eigenschappen"},
            registration_result={
                "zaak": {
                    "url": "https://zaken.nl/api/v1/zaken/1",
                    "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
                }
            },
        )
        zgw_form_options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group,
            "case_type_identification": "",
            "document_type_description": "",
            "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
            "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
            "organisatie_rsin": "000000000",
            "zaak_vertrouwelijkheidaanduiding": "openbaar",
            "doc_vertrouwelijkheidaanduiding": "openbaar",
            "property_mappings": [
                {"component_key": "textField1", "eigenschap": "a property name"},
                {"component_key": "textField2", "eigenschap": "second property"},
                {"component_key": "textField3.blah", "eigenschap": "third property"},
            ],
            "objects_api_group": None,
            "product_url": "",
        }
        self.install_mocks(m)

        m.get(
            "https://catalogus.nl/api/v1/eigenschappen?zaaktype=https%3A%2F%2Fcatalogi.nl%2Fapi%2Fv1%2Fzaaktypen%2F1",
            status_code=200,
            json={
                "count": 3,
                "next": None,
                "previous": None,
                "results": [
                    generate_oas_component(
                        "catalogi",
                        "schemas/Eigenschap",
                        url="https://zaken.nl/catalogi/api/v1/eigenschappen/1",
                        naam="a property name",
                        definitie="a definition",
                        specificatie={
                            "groep": "",
                            "formaat": "tekst",
                            "lengte": "14",
                            "kardinaliteit": "1",
                            "waardenverzameling": [],
                        },
                        toelichting="",
                        zaaktype="https://zaken.nl/api/v1/zaaktypen/1",
                    ),
                    generate_oas_component(
                        "catalogi",
                        "schemas/Eigenschap",
                        url="https://zaken.nl/catalogi/api/v1/eigenschappen/2",
                        naam="second property",
                        definitie="a definition",
                        specificatie={
                            "groep": "",
                            "formaat": "tekst",
                            "lengte": "14",
                            "kardinaliteit": "1",
                            "waardenverzameling": [],
                        },
                        toelichting="",
                        zaaktype="https://zaken.nl/api/v1/zaaktypen/1",
                    ),
                    generate_oas_component(
                        "catalogi",
                        "schemas/Eigenschap",
                        url="https://zaken.nl/catalogi/api/v1/eigenschappen/3",
                        naam="third property",
                        definitie="a definition",
                        specificatie={
                            "groep": "",
                            "formaat": "tekst",
                            "lengte": "14",
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
            [
                {
                    "status_code": 201,
                    "json": generate_oas_component(
                        "catalogi",
                        "schemas/Eigenschap",
                        url="https://zaken.nl/zaken/api/v1/zaken/1/zaakeigenschappen/1",
                        uuid=1,
                        zaak="https://zaken.nl/api/v1/zaken/1",
                        eigenschap="https://zaken.nl/catalogi/api/v1/eigenschappen/1",
                        naam="a property name",
                        waarde="data in columns",
                        definitie="a definition",
                        specificatie={
                            "groep": "",
                            "formaat": "tekst",
                            "lengte": "14",
                            "kardinaliteit": "1",
                            "waardenverzameling": [],
                        },
                        toelichting="",
                        zaaktype="https://zaken.nl/api/v1/zaaktypen/1",
                    ),
                },
                {
                    "status_code": 201,
                    "json": generate_oas_component(
                        "catalogi",
                        "schemas/Eigenschap",
                        url="https://zaken.nl/zaken/api/v1/zaken/1/zaakeigenschappen/2",
                        uuid=2,
                        zaak="https://zaken.nl/api/v1/zaken/1",
                        eigenschap="https://zaken.nl/catalogi/api/v1/eigenschappen/2",
                        naam="second property",
                        waarde="more data",
                        definitie="a definition",
                        specificatie={
                            "groep": "",
                            "formaat": "tekst",
                            "lengte": "14",
                            "kardinaliteit": "1",
                            "waardenverzameling": [],
                        },
                        toelichting="",
                        zaaktype="https://zaken.nl/api/v1/zaaktypen/1",
                    ),
                },
                {
                    "status_code": 201,
                    "json": generate_oas_component(
                        "catalogi",
                        "schemas/Eigenschap",
                        url="https://zaken.nl/zaken/api/v1/zaken/1/zaakeigenschappen/3",
                        uuid=2,
                        zaak="https://zaken.nl/api/v1/zaken/1",
                        eigenschap="https://zaken.nl/catalogi/api/v1/eigenschappen/3",
                        naam="third property",
                        waarde="a value",
                        definitie="a definition",
                        specificatie={
                            "groep": "",
                            "formaat": "tekst",
                            "lengte": "14",
                            "kardinaliteit": "1",
                            "waardenverzameling": [],
                        },
                        toelichting="",
                        zaaktype="https://zaken.nl/api/v1/zaaktypen/1",
                    ),
                },
            ],
        )

        plugin = ZGWRegistration("zgw")
        plugin.pre_register_submission(submission, zgw_form_options)
        result = plugin.register_submission(submission, zgw_form_options)
        assert result

        self.assertEqual(
            result["zaakeigenschappen"]["1"],
            {
                "url": "https://zaken.nl/zaken/api/v1/zaken/1/zaakeigenschappen/1",
                "uuid": 1,
                "zaak": "https://zaken.nl/api/v1/zaken/1",
                "eigenschap": "https://zaken.nl/catalogi/api/v1/eigenschappen/1",
                "naam": "a property name",
                "waarde": "data in columns",
                "definitie": "a definition",
                "specificatie": {
                    "groep": "",
                    "formaat": "tekst",
                    "lengte": "14",
                    "kardinaliteit": "1",
                    "waardenverzameling": [],
                },
                "toelichting": "",
                "zaaktype": "https://zaken.nl/api/v1/zaaktypen/1",
            },
        )
        self.assertEqual(
            result["zaakeigenschappen"]["2"],
            {
                "url": "https://zaken.nl/zaken/api/v1/zaken/1/zaakeigenschappen/2",
                "uuid": 2,
                "zaak": "https://zaken.nl/api/v1/zaken/1",
                "eigenschap": "https://zaken.nl/catalogi/api/v1/eigenschappen/2",
                "naam": "second property",
                "waarde": "more data",
                "definitie": "a definition",
                "specificatie": {
                    "groep": "",
                    "formaat": "tekst",
                    "lengte": "14",
                    "kardinaliteit": "1",
                    "waardenverzameling": [],
                },
                "toelichting": "",
                "zaaktype": "https://zaken.nl/api/v1/zaaktypen/1",
            },
        )
        self.assertEqual(
            result["zaakeigenschappen"]["3"],
            {
                "url": "https://zaken.nl/zaken/api/v1/zaken/1/zaakeigenschappen/3",
                "uuid": 2,
                "zaak": "https://zaken.nl/api/v1/zaken/1",
                "eigenschap": "https://zaken.nl/catalogi/api/v1/eigenschappen/3",
                "naam": "third property",
                "waarde": "a value",
                "definitie": "a definition",
                "specificatie": {
                    "groep": "",
                    "formaat": "tekst",
                    "lengte": "14",
                    "kardinaliteit": "1",
                    "waardenverzameling": [],
                },
                "toelichting": "",
                "zaaktype": "https://zaken.nl/api/v1/zaaktypen/1",
            },
        )

    @tag("gh-4337")
    def test_zgw_backend_zaak_omschrijving(self, m):
        with self.subTest("Short name that is not truncated"):
            submission = SubmissionFactory.create(
                completed_not_preregistered=True,
                with_report=True,
                form__name="Short name",
            )
            zgw_form_options: RegistrationOptions = {
                "zgw_api_group": self.zgw_group,
                "case_type_identification": "",
                "document_type_description": "",
                "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
                "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
                "auteur": "",
                "zaak_vertrouwelijkheidaanduiding": "",  # type: ignore
                "objects_api_group": None,
                "product_url": "",
            }
            self.install_mocks(m)
            plugin = ZGWRegistration("zgw")

            plugin.pre_register_submission(submission, zgw_form_options)

            create_zaak = m.last_request
            self.assertEqual(create_zaak.url, "https://zaken.nl/api/v1/zaken")
            self.assertEqual(create_zaak.method, "POST")
            body = create_zaak.json()
            self.assertEqual(body["omschrijving"], "Short name")

        with self.subTest("Long name that is truncated"):
            submission = SubmissionFactory.create(
                completed_not_preregistered=True,
                with_report=True,
                form__name="Long name that will most definitely be truncated to 80 characters right???????????",
            )
            zgw_form_options: RegistrationOptions = {
                "zgw_api_group": self.zgw_group,
                "case_type_identification": "",
                "document_type_description": "",
                "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
                "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
                "auteur": "",
                "zaak_vertrouwelijkheidaanduiding": "",  # type: ignore
                "objects_api_group": None,
                "product_url": "",
            }
            self.install_mocks(m)
            plugin = ZGWRegistration("zgw")

            plugin.pre_register_submission(submission, zgw_form_options)

            create_zaak = m.last_request
            self.assertEqual(create_zaak.url, "https://zaken.nl/api/v1/zaken")
            self.assertEqual(create_zaak.method, "POST")
            body = create_zaak.json()
            self.assertEqual(
                body["omschrijving"],
                "Long name that will most definitely be truncated to 80 characters right????????\u2026",
            )


@temp_private_root()
class ZGWBackendVCRTests(OFVCRMixin, TestCase):
    VCR_TEST_FILES = TEST_FILES

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.zgw_group = ZGWApiGroupConfigFactory.create(
            for_test_docker_compose=True,
            organisatie_rsin="000000000",
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
            completed_on=datetime(2024, 9, 9, 15, 30, 0).replace(tzinfo=timezone.utc),
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
            completed_on=datetime(2024, 11, 1, 15, 30, 0).replace(tzinfo=timezone.utc),
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
            completed_on=datetime(2024, 9, 9, 15, 30, 0).replace(tzinfo=timezone.utc),
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
            completed_on=datetime(2024, 6, 9, 15, 30, 0).replace(tzinfo=timezone.utc),
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
