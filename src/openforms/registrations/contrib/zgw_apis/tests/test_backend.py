from decimal import Decimal

from django.test import TestCase, override_settings, tag

import requests_mock
from freezegun import freeze_time
from glom import glom
from privates.test import temp_private_root
from zds_client.oas import schema_fetcher
from zgw_consumers.test import generate_oas_component
from zgw_consumers.test.schema_mock import mock_service_oas_get

from openforms.authentication.tests.factories import RegistratorInfoFactory
from openforms.submissions.constants import RegistrationStatuses
from openforms.submissions.models import SubmissionStep
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
)

from ....constants import RegistrationAttribute
from ....exceptions import RegistrationFailed
from ....service import extract_submission_reference
from ....tasks import register_submission
from ..plugin import ZGWRegistration
from .factories import ZgwConfigFactory


@temp_private_root()
@requests_mock.Mocker(real_http=False)
class ZGWBackendTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        ZgwConfigFactory.create(
            zrc_service__api_root="https://zaken.nl/api/v1/",
            zrc_service__oas="https://zaken.nl/api/v1/schema/openapi.yaml",
            drc_service__api_root="https://documenten.nl/api/v1/",
            drc_service__oas="https://documenten.nl/api/v1/schema/openapi.yaml",
            ztc_service__api_root="https://catalogus.nl/api/v1/",
            ztc_service__oas="https://catalogus.nl/api/v1/schema/openapi.yaml",
        )

    def setUp(self):
        super().setUp()
        # reset cache to keep request_history indexes consistent
        schema_fetcher.cache.clear()
        self.addCleanup(schema_fetcher.cache.clear)

    def install_mocks(self, m):
        mock_service_oas_get(m, "https://zaken.nl/api/v1/", "zaken")
        mock_service_oas_get(m, "https://documenten.nl/api/v1/", "documenten")
        mock_service_oas_get(m, "https://catalogus.nl/api/v1/", "catalogi")

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
                "coordinaat": [52.36673378967122, 4.893164274470299],
                "voorletters": "J.W.",
                "geslachtsaanduiding": "mannelijk",
            },
            bsn="111222333",
            form__product__price=Decimal("0"),
            form__payment_backend="demo",
            language_code="en",
        )

        attachment = SubmissionFileAttachmentFactory.create(
            submission_step=submission.steps[0],
        )

        zgw_form_options = dict(
            zaaktype="https://catalogi.nl/api/v1/zaaktypen/1",
            informatieobjecttype="https://catalogi.nl/api/v1/informatieobjecttypen/1",
            organisatie_rsin="000000000",
            zaak_vertrouwelijkheidaanduiding="openbaar",
            doc_vertrouwelijkheidaanduiding="openbaar",
        )

        self.install_mocks(m)

        plugin = ZGWRegistration("zgw")
        result = plugin.register_submission(submission, zgw_form_options)
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

        create_zaak = m.request_history[1]
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
            {"type": "Point", "coordinates": [52.36673378967122, 4.893164274470299]},
        )

        create_eio = m.request_history[3]
        create_eio_body = create_eio.json()
        self.assertEqual(create_eio.method, "POST")
        self.assertEqual(
            create_eio.url,
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

        create_zio = m.request_history[4]
        create_zio_body = create_zio.json()
        self.assertEqual(create_zio.method, "POST")
        self.assertEqual(
            create_zio.url, "https://zaken.nl/api/v1/zaakinformatieobjecten"
        )
        self.assertEqual(create_zio_body["zaak"], "https://zaken.nl/api/v1/zaken/1")
        self.assertEqual(
            create_zio_body["informatieobject"],
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
        )

        create_rol = m.request_history[7]
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
                "verblijfsadres": {"aoaPostcode": "1000 AA"},
                "voorletters": "J.W.",
                "geslachtsaanduiding": "m",
            },
        )
        self.assertEqual(
            create_rol_body["betrokkeneType"],
            "natuurlijk_persoon",
        )

        create_status = m.request_history[9]
        create_status_body = create_status.json()
        self.assertEqual(create_status.method, "POST")
        self.assertEqual(create_status.url, "https://zaken.nl/api/v1/statussen")
        self.assertEqual(create_status_body["zaak"], "https://zaken.nl/api/v1/zaken/1")
        self.assertEqual(
            create_status_body["statustype"],
            "https://catalogus.nl/api/v1/statustypen/1",
        )

        create_attachment = m.request_history[10]
        create_attachment_body = create_attachment.json()
        self.assertEqual(create_attachment.method, "POST")
        self.assertEqual(
            create_attachment.url,
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
        )
        self.assertEqual(create_attachment_body["bestandsnaam"], attachment.file_name)
        self.assertEqual(create_attachment_body["formaat"], attachment.content_type)
        self.assertEqual(create_attachment_body["taal"], "eng")

        relate_attachment = m.request_history[11]
        relate_attachment_body = relate_attachment.json()
        self.assertEqual(relate_attachment.method, "POST")
        self.assertEqual(
            relate_attachment.url, "https://zaken.nl/api/v1/zaakinformatieobjecten"
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
                "coordinaat": [52.36673378967122, 4.893164274470299],
                "vestigingsNummer": "87654321",
            },
            kvk="12345678",
            form__product__price=Decimal("0"),
            form__payment_backend="demo",
        )

        attachment = SubmissionFileAttachmentFactory.create(
            submission_step=submission.steps[0],
        )

        zgw_form_options = dict(
            zaaktype="https://catalogi.nl/api/v1/zaaktypen/1",
            informatieobjecttype="https://catalogi.nl/api/v1/informatieobjecttypen/1",
            organisatie_rsin="000000000",
            zaak_vertrouwelijkheidaanduiding="openbaar",
            doc_vertrouwelijkheidaanduiding="openbaar",
        )

        self.install_mocks(m)

        plugin = ZGWRegistration("zgw")
        result = plugin.register_submission(submission, zgw_form_options)
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

        create_zaak = m.request_history[1]
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
            {"type": "Point", "coordinates": [52.36673378967122, 4.893164274470299]},
        )

        create_eio = m.request_history[3]
        create_eio_body = create_eio.json()
        self.assertEqual(create_eio.method, "POST")
        self.assertEqual(
            create_eio.url,
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

        create_zio = m.request_history[4]
        create_zio_body = create_zio.json()
        self.assertEqual(create_zio.method, "POST")
        self.assertEqual(
            create_zio.url, "https://zaken.nl/api/v1/zaakinformatieobjecten"
        )
        self.assertEqual(create_zio_body["zaak"], "https://zaken.nl/api/v1/zaken/1")
        self.assertEqual(
            create_zio_body["informatieobject"],
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
        )

        create_rol = m.request_history[7]
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
                "handelsnaam": "ACME",
                "vestigingsNummer": "87654321",
                "innNnpId": "12345678",
                "statutaireNaam": "ACME",
                "verblijfsadres": {"aoaPostcode": "1000 AA"},
            },
        )

        create_status = m.request_history[9]
        create_status_body = create_status.json()
        self.assertEqual(create_status.method, "POST")
        self.assertEqual(create_status.url, "https://zaken.nl/api/v1/statussen")
        self.assertEqual(create_status_body["zaak"], "https://zaken.nl/api/v1/zaken/1")
        self.assertEqual(
            create_status_body["statustype"],
            "https://catalogus.nl/api/v1/statustypen/1",
        )

        create_attachment = m.request_history[10]
        create_attachment_body = create_attachment.json()
        self.assertEqual(create_attachment.method, "POST")
        self.assertEqual(
            create_attachment.url,
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
        )
        self.assertEqual(create_attachment_body["bestandsnaam"], attachment.file_name)
        self.assertEqual(create_attachment_body["formaat"], attachment.content_type)

        relate_attachment = m.request_history[11]
        relate_attachment_body = relate_attachment.json()
        self.assertEqual(relate_attachment.method, "POST")
        self.assertEqual(
            relate_attachment.url, "https://zaken.nl/api/v1/zaakinformatieobjecten"
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
                "coordinaat": [52.36673378967122, 4.893164274470299],
            },
            kvk="12345678",
            form__product__price=Decimal("0"),
            form__payment_backend="demo",
        )

        SubmissionFileAttachmentFactory.create(
            submission_step=submission.steps[0],
        )

        zgw_form_options = dict(
            zaaktype="https://catalogi.nl/api/v1/zaaktypen/1",
            informatieobjecttype="https://catalogi.nl/api/v1/informatieobjecttypen/1",
            organisatie_rsin="000000000",
            zaak_vertrouwelijkheidaanduiding="openbaar",
            doc_vertrouwelijkheidaanduiding="openbaar",
        )

        self.install_mocks(m)

        plugin = ZGWRegistration("zgw")
        plugin.register_submission(submission, zgw_form_options)

        create_rol = m.request_history[7]
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
                "coordinaat": [52.36673378967122, 4.893164274470299],
            },
            kvk="12345678",
            form__product__price=Decimal("0"),
            form__payment_backend="demo",
        )

        attachment = SubmissionFileAttachmentFactory.create(
            submission_step=submission.steps[0],
        )

        zgw_form_options = dict(
            zaaktype="https://catalogi.nl/api/v1/zaaktypen/1",
            informatieobjecttype="https://catalogi.nl/api/v1/informatieobjecttypen/1",
            organisatie_rsin="000000000",
            zaak_vertrouwelijkheidaanduiding="openbaar",
            doc_vertrouwelijkheidaanduiding="openbaar",
        )

        self.install_mocks(m)

        plugin = ZGWRegistration("zgw")
        result = plugin.register_submission(submission, zgw_form_options)
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

        create_zaak = m.request_history[1]
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
            {"type": "Point", "coordinates": [52.36673378967122, 4.893164274470299]},
        )

        create_eio = m.request_history[3]
        create_eio_body = create_eio.json()
        self.assertEqual(create_eio.method, "POST")
        self.assertEqual(
            create_eio.url,
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

        create_zio = m.request_history[4]
        create_zio_body = create_zio.json()
        self.assertEqual(create_zio.method, "POST")
        self.assertEqual(
            create_zio.url, "https://zaken.nl/api/v1/zaakinformatieobjecten"
        )
        self.assertEqual(create_zio_body["zaak"], "https://zaken.nl/api/v1/zaken/1")
        self.assertEqual(
            create_zio_body["informatieobject"],
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
        )

        create_rol = m.request_history[7]
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
                "handelsnaam": "ACME",
                "innNnpId": "12345678",
                "statutaireNaam": "ACME",
                "verblijfsadres": {"aoaPostcode": "1000 AA"},
            },
        )

        create_status = m.request_history[9]
        create_status_body = create_status.json()
        self.assertEqual(create_status.method, "POST")
        self.assertEqual(create_status.url, "https://zaken.nl/api/v1/statussen")
        self.assertEqual(create_status_body["zaak"], "https://zaken.nl/api/v1/zaken/1")
        self.assertEqual(
            create_status_body["statustype"],
            "https://catalogus.nl/api/v1/statustypen/1",
        )

        create_attachment = m.request_history[10]
        create_attachment_body = create_attachment.json()
        self.assertEqual(create_attachment.method, "POST")
        self.assertEqual(
            create_attachment.url,
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
        )
        self.assertEqual(create_attachment_body["bestandsnaam"], attachment.file_name)
        self.assertEqual(create_attachment_body["formaat"], attachment.content_type)

        relate_attachment = m.request_history[11]
        relate_attachment_body = relate_attachment.json()
        self.assertEqual(relate_attachment.method, "POST")
        self.assertEqual(
            relate_attachment.url, "https://zaken.nl/api/v1/zaakinformatieobjecten"
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
                "coordinaat": [52.36673378967122, 4.893164274470299],
            },
            kvk="12345678",
            form__product__price=Decimal("0"),
            form__payment_backend="demo",
        )
        RegistratorInfoFactory.create(submission=submission, value="123456782")

        zgw_form_options = dict(
            zaaktype="https://catalogi.nl/api/v1/zaaktypen/1",
            informatieobjecttype="https://catalogi.nl/api/v1/informatieobjecttypen/1",
            organisatie_rsin="000000000",
            zaak_vertrouwelijkheidaanduiding="openbaar",
            doc_vertrouwelijkheidaanduiding="openbaar",
            medewerker_roltype="Some description",
        )

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
        )

        plugin = ZGWRegistration("zgw")
        result = plugin.register_submission(submission, zgw_form_options)

        self.assertIn("medewerker_rol", result)

        create_medewerker_rol_call = m.request_history[-3]

        post_data = create_medewerker_rol_call.json()
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

    def test_retried_registration_with_internal_reference(self, m):
        """
        Assert that the internal reference is included in the "kenmerken".
        """
        submission = SubmissionFactory.from_components(
            completed=True,
            registration_in_progress=True,
            needs_on_completion_retry=True,
            public_registration_reference="OF-1234",
            components_list=[{"key": "dummy"}],
        )
        zgw_form_options = dict(
            zaaktype="https://catalogi.nl/api/v1/zaaktypen/1",
            informatieobjecttype="https://catalogi.nl/api/v1/informatieobjecttypen/1",
            organisatie_rsin="000000000",
            zaak_vertrouwelijkheidaanduiding="openbaar",
            doc_vertrouwelijkheidaanduiding="openbaar",
        )
        self.install_mocks(m)

        plugin = ZGWRegistration("zgw")
        plugin.register_submission(submission, zgw_form_options)

        create_zaak = m.request_history[1]
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

        zgw_form_options = dict(
            zaaktype="https://catalogi.nl/api/v1/zaaktypen/1",
            informatieobjecttype="https://catalogi.nl/api/v1/informatieobjecttypen/1",
            organisatie_rsin="000000000",
            zaak_vertrouwelijkheidaanduiding="openbaar",
            doc_vertrouwelijkheidaanduiding="openbaar",
        )

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
        result = plugin.register_submission(submission, zgw_form_options)
        self.assertEqual(result["zaak"]["url"], "https://zaken.nl/api/v1/zaken/1")
        submission.registration_result = result
        submission.save()

        # check initial payment status
        create_zaak_body = m.request_history[1].json()
        self.assertEqual(create_zaak_body["betalingsindicatie"], "nog_niet")
        self.assertNotIn("laatsteBetaaldatum", create_zaak_body)

        # run the actual update
        plugin.update_payment_status(submission, {})

        patch_zaak_body = m.request_history[-1].json()
        self.assertEqual(patch_zaak_body["betalingsindicatie"], "geheel")
        self.assertEqual(
            patch_zaak_body["laatsteBetaaldatum"], "2021-01-01T10:00:00+00:00"
        )

    def test_reference_can_be_extracted(self, m):
        result = {
            "zaak": {
                "url": "https://zaken.nl/api/v1/zaken/1",
                "identificatie": "abcd1234",
            }
        }
        submission = SubmissionFactory.create(
            form__registration_backend="zgw-create-zaak",
            completed=True,
            registration_success=True,
            registration_result=result,
        )

        reference = extract_submission_reference(submission)

        self.assertEqual("abcd1234", reference)

    def test_submission_with_zgw_backend_override_fields(self, m):
        """Assert that override of default values for the ZGW backend works"""
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "field1",
                    "registration": {
                        "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/10",
                        "bronorganisatie": "100000009",
                        "docVertrouwelijkheidaanduiding": "zeer_geheim",
                        "titel": "TITEL",
                    },
                },
                {
                    "key": "field2",
                    "registration": {
                        "informatieobjecttype": "",
                        "bronorganisatie": "",
                        "doc_vertrouwelijkheidaanduiding": "",
                        "titel": "",
                    },
                },
            ],
            submitted_data={
                "voornaam": "Foo",
            },
        )

        zgw_form_options = dict(
            zaaktype="https://catalogi.nl/api/v1/zaaktypen/1",
            informatieobjecttype="https://catalogi.nl/api/v1/informatieobjecttypen/1",
            organisatie_rsin="000000000",
            zaak_vertrouwelijkheidaanduiding="openbaar",
        )

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

        document_create_attachment1 = m.request_history[-4]
        document_create_attachment2 = m.request_history[-2]

        # Case 1: override fields

        # Verify attachments
        document_create_attachment1_body = document_create_attachment1.json()
        self.assertEqual(document_create_attachment1.method, "POST")
        self.assertEqual(
            document_create_attachment1.url,
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

        # Case 2: default field values

        # Verify attachments
        document_create_attachment2_body = document_create_attachment2.json()
        self.assertEqual(document_create_attachment2.method, "POST")
        self.assertEqual(
            document_create_attachment2.url,
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
        self.assertEqual(
            document_create_attachment2_body["vertrouwelijkheidaanduiding"],
            "",
        )
        # if no title is explicitly provided, the file name should be inserted
        self.assertEqual(document_create_attachment2_body["titel"], "attachment2.jpg")

    def test_zgw_backend_default_author(self, m):
        """Assert that the default values for the ZGW API configuration are inserted

        * default author: "Aanvrager"
        """
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "handelsnaam",
                    "type": "textfield",
                },
            ],
        )
        SubmissionFileAttachmentFactory.create(
            submission_step=submission.steps[0],
        )
        zgw_form_options = dict(
            zaaktype="https://catalogi.nl/api/v1/zaaktypen/1",
        )
        self.install_mocks(m)

        plugin = ZGWRegistration("zgw")
        plugin.register_submission(submission, zgw_form_options)

        # zaak
        create_zaak = m.request_history[1]
        create_zaak_body = create_zaak.json()

        # make sure we have the right request
        self.assertEqual(create_zaak.method, "POST")
        self.assertEqual(create_zaak.url, "https://zaken.nl/api/v1/zaken")

        # check defaults
        self.assertEqual(
            create_zaak_body["vertrouwelijkheidaanduiding"],
            "",
        )

        # eio
        create_eio = m.request_history[3]
        create_eio_body = create_eio.json()

        # make sure we have the right request
        self.assertEqual(create_zaak.method, "POST")
        self.assertEqual(
            create_eio.url,
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
        )

        # check defaults
        self.assertEqual(
            create_eio_body["vertrouwelijkheidaanduiding"],
            "",
        )
        self.assertEqual(create_eio_body["auteur"], "Aanvrager")

        # attachment
        create_attachment = m.request_history[10]
        create_attachment_body = create_attachment.json()

        # make sure we have the right request
        self.assertEqual(create_attachment.method, "POST")
        self.assertEqual(
            create_attachment.url,
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
        )

        # check defaults
        self.assertEqual(
            create_attachment.url,
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
        )
        self.assertEqual(create_attachment_body["auteur"], "Aanvrager")

    def test_zgw_backend_defaults_empty_string(self, m):
        """Assert that empty strings for new fields are overriden with defaults

        This test ensures that old DB entries won't have an empty string as the value
        of newly added fields like `auteur`.
        """
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "handelsnaam",
                    "type": "textfield",
                },
            ],
        )
        zgw_form_options = dict(
            zaaktype="https://catalogi.nl/api/v1/zaaktypen/1",
            informatieobjecttype="https://catalogi.nl/api/v1/informatieobjecttypen/1",
            auteur="",
        )

        SubmissionFileAttachmentFactory.create(
            submission_step=SubmissionStep.objects.first(),
            file_name="attachment1.jpg",
            form_key="field1",
        )

        self.install_mocks(m)

        plugin = ZGWRegistration("zgw")
        plugin.register_submission(submission, zgw_form_options)

        document_create_attachment = m.request_history[-2]
        document_create_attachment_body = document_create_attachment.json()

        self.assertEqual(document_create_attachment_body["auteur"], "Aanvrager")


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

        ZgwConfigFactory.create(
            zrc_service__api_root="https://zaken.nl/api/v1/",
            zrc_service__oas="https://zaken.nl/api/v1/schema/openapi.yaml",
            drc_service__api_root="https://documenten.nl/api/v1/",
            drc_service__oas="https://documenten.nl/api/v1/schema/openapi.yaml",
            ztc_service__api_root="https://catalogus.nl/api/v1/",
            ztc_service__oas="https://catalogus.nl/api/v1/schema/openapi.yaml",
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
                "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
                "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
                "organisatie_rsin": "000000000",
                "vertrouwelijkheidaanduiding": "openbaar",
            },
            completed=True,
            bsn="111222333",
            submitted_data={
                "voornaam": "Foo",
                "achternaam": "Bar",
            },
        )

    def setUp(self):
        super().setUp()
        # reset cache to keep request_history indexes consistent
        schema_fetcher.cache.clear()
        self.addCleanup(schema_fetcher.cache.clear)

        self.requests_mock = requests_mock.Mocker()
        self.requests_mock.start()
        self.addCleanup(self.requests_mock.stop)
        self.addCleanup(self.submission.refresh_from_db)

        mock_service_oas_get(self.requests_mock, "https://zaken.nl/api/v1/", "zaken")
        mock_service_oas_get(
            self.requests_mock, "https://documenten.nl/api/v1/", "documenten"
        )
        mock_service_oas_get(
            self.requests_mock, "https://catalogus.nl/api/v1/", "catalogi"
        )

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
            register_submission(self.submission.id)

            self.submission.refresh_from_db()
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
                register_submission(self.submission.id)

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
            # 1. fetch zaken API schema
            # 2. create zaak call
            # 3. fetch documenten API schema
            # 4. create report document call (fails)
            # 5. create report document call (fails)
            self.assertEqual(len(history), 5)

            self.assertEqual(history[1].url, "https://zaken.nl/api/v1/zaken")
            self.assertEqual(
                history[3].url,
                "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            )
            self.assertEqual(
                history[4].url,
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
        )
        self.requests_mock.post(
            "https://zaken.nl/api/v1/statussen",
            status_code=201,
            json=generate_oas_component(
                "zaken", "schemas/Status", url="https://zaken.nl/api/v1/statussen/1"
            ),
        )

        with self.subTest("First try, attachment relation fails"):
            register_submission(self.submission.id)

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

            rol = glom(intermediate_results, "rol")
            self.assertEqual(rol["url"], "https://zaken.nl/api/v1/rollen/1")

            status = glom(intermediate_results, "status")
            self.assertEqual(status["url"], "https://zaken.nl/api/v1/statussen/1")

            self.assertIn("traceback", self.submission.registration_result)

        with self.subTest("New attempt - ensure existing data is not created again"):
            with self.assertRaises(RegistrationFailed):
                register_submission(self.submission.id)

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

            rol = glom(intermediate_results, "rol")
            self.assertEqual(rol["url"], "https://zaken.nl/api/v1/rollen/1")

            status = glom(intermediate_results, "status")
            self.assertEqual(status["url"], "https://zaken.nl/api/v1/statussen/1")

            self.assertIn("traceback", self.submission.registration_result)

            history = self.requests_mock.request_history
            # 1. fetch zaken API schema
            # 2. create zaak call
            # 3. fetch documents API schema
            # 4. create report document call
            # 5. relate zaak & report document
            # 6. fetch catalogi API schema
            # 7. get roltypen
            # 8. create rol
            # 9. get statustypen
            # 10. create status
            # 11. create attachment document
            # 12. relate attachment document (fails)
            # 13. relate attachment document (still fails)
            self.assertEqual(len(history), 13)

            self.assertEqual(history[1].url, "https://zaken.nl/api/v1/zaken")
            self.assertEqual(
                history[3].url,
                "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            )
            self.assertEqual(
                history[4].url, "https://zaken.nl/api/v1/zaakinformatieobjecten"
            )
            self.assertEqual(history[7].url, "https://zaken.nl/api/v1/rollen")
            self.assertEqual(history[9].url, "https://zaken.nl/api/v1/statussen")
            self.assertEqual(
                history[10].url,
                "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            )
            self.assertEqual(
                history[11].url, "https://zaken.nl/api/v1/zaakinformatieobjecten"
            )
            self.assertEqual(
                history[12].url, "https://zaken.nl/api/v1/zaakinformatieobjecten"
            )
