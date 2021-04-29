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
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionStepFactory,
)

from ..plugin import create_zaak_plugin
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
        self.zgw_config = ZgwConfigFactory.create(
            zrc_service=self.zaken_api, drc_service=self.documenten_api
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

        # FIXME is there an equivalent for `get_operation_url` in zgw_consumers?
        m.register_uri(
            "POST",
            f"{self.zaken_api.api_root}zaken",
            status_code=201,
            json={"url": f"{self.zaken_api.api_root}zaken/1"},
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
            json={"url": f"{self.documenten_api.api_root}zaakinformatieobjecten/1"},
        )

        submission = SubmissionFactory.create(form=self.form)
        submission_step = SubmissionStepFactory.create(
            submission=submission, form_step=self.fs, data={"type": "test"}
        )

        result = create_zaak_plugin(submission, zgw_form_options)

        self.assertEqual(
            result,
            {
                "zaak": {"url": f"{self.zaken_api.api_root}zaken/1"},
                "document": {
                    "url": f"{self.documenten_api.api_root}enkelvoudiginformatieobjecten/1"
                },
            },
        )

        # 5 requests in total, 2 of which are GETs on the OAS
        self.assertEqual(len(m.request_history), 5)

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
