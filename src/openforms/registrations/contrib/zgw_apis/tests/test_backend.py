from django.test import TestCase

import requests_mock
from zgw_consumers.constants import APITypes
from zgw_consumers.test import generate_oas_component
from zgw_consumers.test.schema_mock import mock_service_oas_get

from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
)
from openforms.registrations.contrib.zgw_apis.plugin import create_zaak_plugin
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionStepFactory,
)

from .factories import ServiceFactory, ZgwConfigFactory


@requests_mock.Mocker()
class ZGWBackendTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.form = FormFactory.create()
        cls.fd = FormDefinitionFactory.create()
        cls.fs = FormStepFactory.create(form=cls.form, form_definition=cls.fd)

        ZgwConfigFactory.create(
            zrc_service__api_root="https://zaken.nl/api/v1/",
            drc_service__api_root="https://documenten.nl/api/v1/",
            ztc_service__api_root="https://catalogus.nl/api/v1/",
        )

    def test_submission_with_zgw_backend(self, m):
        zgw_form_options = dict(
            zaaktype="https://catalogi.nl/api/v1/zaaktypen/1",
            informatieobjecttype="https://catalogi.nl/api/v1/informatieobjecttypen/1",
            organisatie_rsin="000000000",
            vertrouwelijkheidaanduiding="openbaar",
        )

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
            status_code=201,
            json=generate_oas_component(
                "documenten",
                "schemas/EnkelvoudigInformatieObject",
                url="https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
            ),
        )
        m.post(
            "https://zaken.nl/api/v1/zaakinformatieobjecten",
            status_code=201,
            json=generate_oas_component(
                "zaken",
                "schemas/ZaakInformatieObject",
                url="https://zaken.nl/api/v1/zaakinformatieobjecten/1",
            ),
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

        data = {
            "voornaam": "Foo",
        }

        submission = SubmissionFactory.create(form=self.form)
        submission_step = SubmissionStepFactory.create(
            submission=submission, form_step=self.fs, data=data
        )

        result = create_zaak_plugin(submission, zgw_form_options)
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

        # 10 requests in total, 3 of which are GETs on the OAS and 2 are searches
        self.assertEqual(len(m.request_history), 10)

        create_zaak = m.request_history[1]
        create_zaak_body = create_zaak.json()
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

        create_eio = m.request_history[3]
        create_eio_body = create_eio.json()
        self.assertEqual(create_eio.method, "POST")
        self.assertEqual(
            create_eio.url,
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
        )
        self.assertEqual(create_eio_body["bronorganisatie"], "000000000")
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
            create_rol_body["betrokkeneIdentificatie"]["voornamen"],
            "Foo",
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
