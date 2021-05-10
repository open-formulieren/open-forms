import json

from django.test import TestCase

import requests_mock
from zgw_consumers.constants import APITypes
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
    def setUp(self):
        self.form = FormFactory.create()
        self.fd = FormDefinitionFactory.create()
        self.fs = FormStepFactory.create(form=self.form, form_definition=self.fd)

        self.zaken_api = ServiceFactory.create(api_root="https://zaken.nl/api/v1/")
        self.documenten_api = ServiceFactory.create(
            api_root="https://documenten.nl/api/v1/", api_type=APITypes.drc
        )
        self.catalogus_api = ServiceFactory.create(
            api_root="https://catalogus.nl/api/v1/", api_type=APITypes.ztc
        )
        self.zgw_config = ZgwConfigFactory.create(
            zrc_service=self.zaken_api,
            drc_service=self.documenten_api,
            ztc_service=self.catalogus_api,
        )

    def test_submission_with_zgw_backend(self, m):
        zgw_form_options = dict(
            zaaktype="https://catalogi.nl/api/v1/zaaktypen/1",
            informatieobjecttype="https://catalogi.nl/api/v1/informatieobjecttypen/1",
            organisatie_rsin="000000000",
            vertrouwelijkheidaanduiding="openbaar",
        )

        mock_service_oas_get(m, self.zaken_api.api_root, "zaken")
        mock_service_oas_get(m, self.documenten_api.api_root, "documenten")
        mock_service_oas_get(m, self.catalogus_api.api_root, "catalogi")

        # FIXME is there an equivalent for `get_operation_url` in zgw_consumers?
        m.register_uri(
            "POST",
            f"{self.zaken_api.api_root}zaken",
            status_code=201,
            json={
                "url": f"{self.zaken_api.api_root}zaken/1",
                "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
            },
        )
        m.register_uri(
            "POST",
            f"{self.documenten_api.api_root}enkelvoudiginformatieobjecten",
            status_code=201,
            json={
                "url": f"{self.documenten_api.api_root}enkelvoudiginformatieobjecten/1"
            },
        )
        m.register_uri(
            "POST",
            f"{self.zaken_api.api_root}zaakinformatieobjecten",
            status_code=201,
            json={"url": f"{self.zaken_api.api_root}zaakinformatieobjecten/1"},
        )

        m.register_uri(
            "GET",
            f"{self.catalogus_api.api_root}roltypen?zaaktype=https%3A%2F%2Fcatalogi.nl%2Fapi%2Fv1%2Fzaaktypen%2F1&omschrijvingGeneriek=initiator",
            status_code=200,
            json={
                "count": 1,
                "next": None,
                "previous": None,
                "results": [{"url": f"{self.catalogus_api.api_root}roltypen/1"}],
            },
        )
        m.register_uri(
            "POST",
            f"{self.zaken_api.api_root}rollen",
            status_code=201,
            json={"url": f"{self.zaken_api.api_root}rollen/1"},
        )
        m.register_uri(
            "GET",
            f"{self.catalogus_api.api_root}statustypen?zaaktype=https%3A%2F%2Fcatalogi.nl%2Fapi%2Fv1%2Fzaaktypen%2F1",
            status_code=200,
            json={
                "count": 2,
                "next": None,
                "previous": None,
                "results": [
                    {
                        "url": f"{self.catalogus_api.api_root}statustypen/2",
                        "volgnummer": 2,
                    },
                    {
                        "url": f"{self.catalogus_api.api_root}statustypen/1",
                        "volgnummer": 1,
                    },
                ],
            },
        )
        m.register_uri(
            "POST",
            f"{self.zaken_api.api_root}statussen",
            status_code=201,
            json={"url": f"{self.zaken_api.api_root}statussen/1"},
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
            result,
            {
                "document": {
                    "url": "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1"
                },
                "rol": {"url": "https://zaken.nl/api/v1/rollen/1"},
                "status": {"url": "https://zaken.nl/api/v1/statussen/1"},
                "zaak": {
                    "url": "https://zaken.nl/api/v1/zaken/1",
                    "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
                },
            },
        )

        # 10 requests in total, 3 of which are GETs on the OAS and 2 are searches
        self.assertEqual(len(m.request_history), 10)

        create_zaak = m.request_history[1]
        create_zaak_body = json.loads(create_zaak.body)
        self.assertEqual(create_zaak.method, "POST")
        self.assertEqual(create_zaak.url, f"{self.zaken_api.api_root}zaken")
        self.assertEqual(
            create_zaak_body["bronorganisatie"], zgw_form_options["organisatie_rsin"]
        )
        self.assertEqual(
            create_zaak_body["verantwoordelijkeOrganisatie"],
            zgw_form_options["organisatie_rsin"],
        )
        self.assertEqual(
            create_zaak_body["vertrouwelijkheidaanduiding"],
            zgw_form_options["vertrouwelijkheidaanduiding"],
        )
        self.assertEqual(create_zaak_body["zaaktype"], zgw_form_options["zaaktype"])

        create_eio = m.request_history[3]
        create_eio_body = json.loads(create_eio.body)
        self.assertEqual(create_eio.method, "POST")
        self.assertEqual(
            create_eio.url,
            f"{self.documenten_api.api_root}enkelvoudiginformatieobjecten",
        )
        self.assertEqual(
            create_eio_body["bronorganisatie"], zgw_form_options["organisatie_rsin"]
        )
        self.assertEqual(
            create_eio_body["vertrouwelijkheidaanduiding"],
            zgw_form_options["vertrouwelijkheidaanduiding"],
        )
        self.assertEqual(
            create_eio_body["informatieobjecttype"],
            zgw_form_options["informatieobjecttype"],
        )

        create_zio = m.request_history[4]
        create_zio_body = json.loads(create_zio.body)
        self.assertEqual(create_zio.method, "POST")
        self.assertEqual(
            create_zio.url, f"{self.zaken_api.api_root}zaakinformatieobjecten"
        )
        self.assertEqual(create_zio_body["zaak"], f"{self.zaken_api.api_root}zaken/1")
        self.assertEqual(
            create_zio_body["informatieobject"],
            f"{self.documenten_api.api_root}enkelvoudiginformatieobjecten/1",
        )

        create_rol = m.request_history[7]
        create_rol_body = json.loads(create_rol.body)
        self.assertEqual(create_rol.method, "POST")
        self.assertEqual(create_rol.url, f"{self.zaken_api.api_root}rollen")
        self.assertEqual(create_zio_body["zaak"], f"{self.zaken_api.api_root}zaken/1")
        self.assertEqual(
            create_rol_body["roltype"],
            f"{self.catalogus_api.api_root}roltypen/1",
        )
        self.assertEqual(
            create_rol_body["betrokkeneIdentificatie"]["voornamen"],
            "Foo",
        )

        create_status = m.request_history[9]
        create_status_body = json.loads(create_status.body)
        self.assertEqual(create_status.method, "POST")
        self.assertEqual(create_status.url, f"{self.zaken_api.api_root}statussen")
        self.assertEqual(
            create_status_body["zaak"], f"{self.zaken_api.api_root}zaken/1"
        )
        self.assertEqual(
            create_status_body["statustype"],
            f"{self.catalogus_api.api_root}statustypen/1",
        )
