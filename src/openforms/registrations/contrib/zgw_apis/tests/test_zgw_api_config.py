from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

import requests_mock
from django_webtest import WebTest
from privates.test import temp_private_root
from requests.models import HTTPError
from zds_client.oas import schema_fetcher
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen
from zgw_consumers.test import generate_oas_component
from zgw_consumers.test.schema_mock import mock_service_oas_get

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.submissions.models import SubmissionStep
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
)

from ..models import ZgwConfig
from ..plugin import ZGWRegistration
from .factories import ZGWApiGroupConfigFactory


@temp_private_root()
@requests_mock.Mocker()
class ZGWRegistrationMultipleZGWAPIsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.zgw_group1 = ZGWApiGroupConfigFactory.create(
            zrc_service__api_root="https://zaken-1.nl/api/v1/",
            zrc_service__oas="https://zaken-1.nl/api/v1/schema/openapi.yaml",
            drc_service__api_root="https://documenten-1.nl/api/v1/",
            drc_service__oas="https://documenten-1.nl/api/v1/schema/openapi.yaml",
            ztc_service__api_root="https://catalogus-1.nl/api/v1/",
            ztc_service__oas="https://catalogus-1.nl/api/v1/schema/openapi.yaml",
            zaaktype="https://catalogi-1.nl/api/v1/zaaktypen/1",
            informatieobjecttype="https://catalogi-1.nl/api/v1/informatieobjecttypen/1",
            organisatie_rsin="000000000",
            zaak_vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        cls.zgw_group2 = ZGWApiGroupConfigFactory.create(
            zrc_service__api_root="https://zaken-2.nl/api/v1/",
            zrc_service__oas="https://zaken-2.nl/api/v1/schema/openapi.yaml",
            drc_service__api_root="https://documenten-2.nl/api/v1/",
            drc_service__oas="https://documenten-2.nl/api/v1/schema/openapi.yaml",
            ztc_service__api_root="https://catalogus-2.nl/api/v1/",
            ztc_service__oas="https://catalogus-2.nl/api/v1/schema/openapi.yaml",
            zaaktype="https://catalogi-2.nl/api/v1/zaaktypen/1",
            informatieobjecttype="https://catalogi-2.nl/api/v1/informatieobjecttypen/1",
            organisatie_rsin="000000001",
            zaak_vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.beperkt_openbaar,
        )

    def setUp(self):
        super().setUp()
        # reset cache to keep request_history indexes consistent
        schema_fetcher.cache.clear()
        self.addCleanup(schema_fetcher.cache.clear)

    def install_mocks(self, m):
        # API set 1
        mock_service_oas_get(m, "https://zaken-1.nl/api/v1/", "zaken")
        mock_service_oas_get(m, "https://documenten-1.nl/api/v1/", "documenten")
        mock_service_oas_get(m, "https://catalogus-1.nl/api/v1/", "catalogi")

        m.get(
            "https://zaken-1.nl/api/v1/zaken",
            status_code=200,
            json=[],
        )
        m.post(
            "https://zaken-1.nl/api/v1/zaken",
            status_code=201,
            json=generate_oas_component(
                "zaken",
                "schemas/Zaak",
                url="https://zaken-1.nl/api/v1/zaken/1",
                zaaktype="https://catalogi-1.nl/api/v1/zaaktypen/1",
            ),
        )
        m.get(
            "https://documenten-1.nl/api/v1/enkelvoudiginformatieobjecten",
            status_code=200,
            json=[],
        )
        m.post(
            "https://documenten-1.nl/api/v1/enkelvoudiginformatieobjecten",
            [
                # two calls on same URL: one PDF and one attachment
                {
                    "json": generate_oas_component(
                        "documenten",
                        "schemas/EnkelvoudigInformatieObject",
                        url="https://documenten-1.nl/api/v1/enkelvoudiginformatieobjecten/1",
                    ),
                    "status_code": 201,
                },
                {
                    "json": generate_oas_component(
                        "documenten",
                        "schemas/EnkelvoudigInformatieObject",
                        url="https://documenten-1.nl/api/v1/enkelvoudiginformatieobjecten/2",
                    ),
                    "status_code": 201,
                },
            ],
        )
        m.post(
            "https://zaken-1.nl/api/v1/zaakinformatieobjecten",
            [
                # two calls on same URL: one PDF and one attachment
                {
                    "json": generate_oas_component(
                        "zaken",
                        "schemas/ZaakInformatieObject",
                        url="https://zaken-1.nl/api/v1/zaakinformatieobjecten/1",
                    ),
                    "status_code": 201,
                },
                {
                    "json": generate_oas_component(
                        "zaken",
                        "schemas/ZaakInformatieObject",
                        url="https://zaken-1.nl/api/v1/zaakinformatieobjecten/2",
                    ),
                    "status_code": 201,
                },
            ],
        )

        m.get(
            "https://catalogus-1.nl/api/v1/roltypen?zaaktype=https%3A%2F%2Fcatalogi-1.nl%2Fapi%2Fv1%2Fzaaktypen%2F1&omschrijvingGeneriek=initiator",
            status_code=200,
            json={
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    generate_oas_component(
                        "catalogi",
                        "schemas/RolType",
                        url="https://catalogus-1.nl/api/v1/roltypen/1",
                    )
                ],
            },
        )
        m.post(
            "https://zaken-1.nl/api/v1/rollen",
            status_code=201,
            json=generate_oas_component(
                "zaken", "schemas/Rol", url="https://zaken-1.nl/api/v1/rollen/1"
            ),
        )
        m.get(
            "https://catalogus-1.nl/api/v1/statustypen?zaaktype=https%3A%2F%2Fcatalogi-1.nl%2Fapi%2Fv1%2Fzaaktypen%2F1",
            status_code=200,
            json={
                "count": 2,
                "next": None,
                "previous": None,
                "results": [
                    generate_oas_component(
                        "catalogi",
                        "schemas/StatusType",
                        url="https://catalogus-1.nl/api/v1/statustypen/2",
                        volgnummer=2,
                    ),
                    generate_oas_component(
                        "catalogi",
                        "schemas/StatusType",
                        url="https://catalogus-1.nl/api/v1/statustypen/1",
                        volgnummer=1,
                    ),
                ],
            },
        )
        m.get("https://catalogus-1.nl/api/v1/zaaktypen", status_code=200, json=[])
        m.post(
            "https://zaken-1.nl/api/v1/statussen",
            status_code=201,
            json=generate_oas_component(
                "zaken", "schemas/Status", url="https://zaken-1.nl/api/v1/statussen/1"
            ),
        )

        # API set 2
        mock_service_oas_get(m, "https://zaken-2.nl/api/v1/", "zaken")
        mock_service_oas_get(m, "https://documenten-2.nl/api/v1/", "documenten")
        mock_service_oas_get(m, "https://catalogus-2.nl/api/v1/", "catalogi")

        m.get(
            "https://zaken-2.nl/api/v1/zaken",
            status_code=200,
            json=[],
        )
        m.post(
            "https://zaken-2.nl/api/v1/zaken",
            status_code=201,
            json=generate_oas_component(
                "zaken",
                "schemas/Zaak",
                url="https://zaken-2.nl/api/v1/zaken/1",
                zaaktype="https://catalogi-2.nl/api/v1/zaaktypen/1",
            ),
        )
        m.get(
            "https://documenten-2.nl/api/v1/enkelvoudiginformatieobjecten",
            status_code=200,
            json=[],
        )
        m.post(
            "https://documenten-2.nl/api/v1/enkelvoudiginformatieobjecten",
            [
                # two calls on same URL: one PDF and one attachment
                {
                    "json": generate_oas_component(
                        "documenten",
                        "schemas/EnkelvoudigInformatieObject",
                        url="https://documenten-2.nl/api/v1/enkelvoudiginformatieobjecten/1",
                    ),
                    "status_code": 201,
                },
                {
                    "json": generate_oas_component(
                        "documenten",
                        "schemas/EnkelvoudigInformatieObject",
                        url="https://documenten-2.nl/api/v1/enkelvoudiginformatieobjecten/2",
                    ),
                    "status_code": 201,
                },
            ],
        )
        m.post(
            "https://zaken-2.nl/api/v1/zaakinformatieobjecten",
            [
                # two calls on same URL: one PDF and one attachment
                {
                    "json": generate_oas_component(
                        "zaken",
                        "schemas/ZaakInformatieObject",
                        url="https://zaken-2.nl/api/v1/zaakinformatieobjecten/1",
                    ),
                    "status_code": 201,
                },
                {
                    "json": generate_oas_component(
                        "zaken",
                        "schemas/ZaakInformatieObject",
                        url="https://zaken-2.nl/api/v1/zaakinformatieobjecten/2",
                    ),
                    "status_code": 201,
                },
            ],
        )

        m.get(
            "https://catalogus-2.nl/api/v1/roltypen?zaaktype=https%3A%2F%2Fcatalogi-2.nl%2Fapi%2Fv1%2Fzaaktypen%2F1&omschrijvingGeneriek=initiator",
            status_code=200,
            json={
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    generate_oas_component(
                        "catalogi",
                        "schemas/RolType",
                        url="https://catalogus-2.nl/api/v1/roltypen/1",
                    )
                ],
            },
        )
        m.get(
            "https://catalogus-2.nl/api/v1/roltypen?zaaktype=https%3A%2F%2Fcatalogi-2.nl%2Fapi%2Fv1%2Fzaaktypen%2F2&omschrijvingGeneriek=initiator",
            status_code=200,
            json={
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    generate_oas_component(
                        "catalogi",
                        "schemas/RolType",
                        url="https://catalogus-2.nl/api/v1/roltypen/2",
                    )
                ],
            },
        )
        m.get("https://catalogus-2.nl/api/v1/zaaktypen", status_code=200, json=[])
        m.post(
            "https://zaken-2.nl/api/v1/rollen",
            status_code=201,
            json=generate_oas_component(
                "zaken", "schemas/Rol", url="https://zaken-2.nl/api/v1/rollen/1"
            ),
        )
        m.get(
            "https://catalogus-2.nl/api/v1/statustypen?zaaktype=https%3A%2F%2Fcatalogi-2.nl%2Fapi%2Fv1%2Fzaaktypen%2F1",
            status_code=200,
            json={
                "count": 2,
                "next": None,
                "previous": None,
                "results": [
                    generate_oas_component(
                        "catalogi",
                        "schemas/StatusType",
                        url="https://catalogus-2.nl/api/v1/statustypen/2",
                        volgnummer=2,
                    ),
                    generate_oas_component(
                        "catalogi",
                        "schemas/StatusType",
                        url="https://catalogus-2.nl/api/v1/statustypen/1",
                        volgnummer=1,
                    ),
                ],
            },
        )
        m.post(
            "https://zaken-2.nl/api/v1/statussen",
            status_code=201,
            json=generate_oas_component(
                "zaken", "schemas/Status", url="https://zaken-2.nl/api/v1/statussen/1"
            ),
        )

    def test_the_right_api_is_used(self, m):
        submission = SubmissionFactory.from_components(
            [
                {"key": "field1", "type": "file"},
            ],
            submitted_data={
                "field1": "Foo",
            },
        )

        zgw_form_options = dict(
            zgw_api_group=self.zgw_group2,  # Configure to use the second ZGW API
        )

        SubmissionFileAttachmentFactory.create(
            submission_step=SubmissionStep.objects.first(),
            file_name="attachment1.jpg",
            form_key="field1",
            _component_configuration_path="components.0",
        )

        self.install_mocks(m)

        plugin = ZGWRegistration("zgw")
        plugin.pre_register_submission(submission, zgw_form_options)
        plugin.register_submission(submission, zgw_form_options)

        history = m.request_history

        for request in history:
            self.assertTrue(request.hostname.endswith("-2.nl"))

    def test_per_form_overwrites(self, m):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "field1",
                    "type": "file",
                },
            ],
            submitted_data={
                "field1": "Foo",
            },
        )

        zgw_form_options = dict(
            zgw_api_group=self.zgw_group2,  # Configure to use the second ZGW API
            zaaktype="https://catalogi-2.nl/api/v1/zaaktypen/2",  # Use zaaktype 2 instead of 1
            informatieobjecttype="https://catalogi-2.nl/api/v1/informatieobjecttypen/2",  # Use iot 2 instead of 1
            organisatie_rsin="000000123",
            zaak_vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.confidentieel,
            doc_vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.geheim,
        )

        SubmissionFileAttachmentFactory.create(
            submission_step=SubmissionStep.objects.first(),
            file_name="attachment1.jpg",
            form_key="field1",
            _component_configuration_path="components.0",
        )

        self.install_mocks(m)

        plugin = ZGWRegistration("zgw")
        plugin.pre_register_submission(submission, zgw_form_options)
        plugin.register_submission(submission, zgw_form_options)

        history = m.request_history
        zaak_body = history[1].json()
        report_body = history[3].json()
        attachment_body = history[10].json()

        self.assertEqual(
            zaak_body["zaaktype"], "https://catalogi-2.nl/api/v1/zaaktypen/2"
        )
        self.assertEqual(
            zaak_body["vertrouwelijkheidaanduiding"],
            VertrouwelijkheidsAanduidingen.confidentieel,
        )
        self.assertEqual(zaak_body["bronorganisatie"], "000000123")
        self.assertEqual(
            report_body["informatieobjecttype"],
            "https://catalogi-2.nl/api/v1/informatieobjecttypen/2",
        )
        self.assertEqual(
            report_body["vertrouwelijkheidaanduiding"],
            VertrouwelijkheidsAanduidingen.geheim,
        )
        self.assertEqual(
            attachment_body["informatieobjecttype"],
            "https://catalogi-2.nl/api/v1/informatieobjecttypen/2",
        )
        self.assertEqual(
            attachment_body["vertrouwelijkheidaanduiding"],
            VertrouwelijkheidsAanduidingen.geheim,
        )

    def test_uses_field_overwrites_for_documents(self, m):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "field1",
                    "type": "file",
                    "registration": {
                        "informatieobjecttype": "https://catalogi-2.nl/api/v1/informatieobjecttypen/3",
                        "bronorganisatie": "100000009",
                        "docVertrouwelijkheidaanduiding": VertrouwelijkheidsAanduidingen.zeer_geheim,
                        "titel": "TITEL",
                    },
                },
            ],
            submitted_data={
                "field1": "Foo",
            },
        )

        zgw_form_options = dict(
            zgw_api_group=self.zgw_group2,
            zaaktype="https://catalogi-2.nl/api/v1/zaaktypen/2",
            informatieobjecttype="https://catalogi-2.nl/api/v1/informatieobjecttypen/2",
            organisatie_rsin="000000123",
            zaak_vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.confidentieel,
            doc_vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.geheim,
        )

        SubmissionFileAttachmentFactory.create(
            submission_step=SubmissionStep.objects.first(),
            file_name="attachment1.jpg",
            form_key="field1",
            _component_configuration_path="components.0",
        )

        self.install_mocks(m)

        plugin = ZGWRegistration("zgw")
        plugin.pre_register_submission(submission, zgw_form_options)
        plugin.register_submission(submission, zgw_form_options)

        history = m.request_history
        attachment_body = history[10].json()

        self.assertEqual(
            attachment_body["informatieobjecttype"],
            "https://catalogi-2.nl/api/v1/informatieobjecttypen/3",
        )
        self.assertEqual(
            attachment_body["vertrouwelijkheidaanduiding"],
            VertrouwelijkheidsAanduidingen.zeer_geheim,
        )
        self.assertEqual(
            attachment_body["titel"],
            "TITEL",
        )
        self.assertEqual(
            attachment_body["bronorganisatie"],
            "100000009",
        )

    def test_check_config(self, m):
        self.install_mocks(m)

        plugin = ZGWRegistration("zgw")
        plugin.check_config()

        history = m.request_history

        self.assertEqual(len(history), 12)
        self.assertEqual(history[1].hostname, "zaken-1.nl")
        self.assertEqual(history[3].hostname, "documenten-1.nl")
        self.assertEqual(history[5].hostname, "catalogus-1.nl")

        self.assertEqual(history[7].hostname, "zaken-2.nl")
        self.assertEqual(history[9].hostname, "documenten-2.nl")
        self.assertEqual(history[11].hostname, "catalogus-2.nl")

    def test_check_config_no_service(self, m):
        self.install_mocks(m)

        ZGWApiGroupConfigFactory.create(zrc_service=None)

        plugin = ZGWRegistration("zgw")

        with self.assertRaises(InvalidPluginConfiguration):
            plugin.check_config()

    def test_check_config_http_error(self, m):
        self.install_mocks(m)

        m.get(
            "https://zaken-1.nl/api/v1/zaken",
            exc=HTTPError,
        )

        plugin = ZGWRegistration("zgw")
        with self.assertRaises(InvalidPluginConfiguration):
            plugin.check_config()

    def test_check_config_random_error(self, m):
        self.install_mocks(m)

        m.get(
            "https://zaken-1.nl/api/v1/zaken",
            exc=Exception,
        )

        plugin = ZGWRegistration("zgw")
        with self.assertRaises(InvalidPluginConfiguration):
            plugin.check_config()

    def test_get_zgw_config(self, m):
        plugin = ZGWRegistration("zgw")

        with patch(
            "openforms.registrations.contrib.zgw_apis.plugin.ZgwConfig.get_solo",
            return_value=ZgwConfig(default_zgw_api_group=self.zgw_group1),
        ):
            api_group = plugin.get_zgw_config({})

        self.assertEqual(api_group, self.zgw_group1)


@temp_private_root()
class ZGWApiGroupConfigAdminTests(WebTest):
    csrf_checks = False

    @classmethod
    def setUpTestData(cls):
        cls.zgw_group = ZGWApiGroupConfigFactory.create(
            zrc_service__api_root="https://zaken-1.nl/api/v1/",
            zrc_service__oas="https://zaken-1.nl/api/v1/schema/openapi.yaml",
            drc_service__api_root="https://documenten-1.nl/api/v1/",
            drc_service__oas="https://documenten-1.nl/api/v1/schema/openapi.yaml",
            ztc_service__api_root="https://catalogus-1.nl/api/v1/",
            ztc_service__oas="https://catalogus-1.nl/api/v1/schema/openapi.yaml",
            zaaktype="https://catalogi-1.nl/api/v1/zaaktypen/1",
            informatieobjecttype="https://catalogi-1.nl/api/v1/informatieobjecttypen/1",
            organisatie_rsin="000000000",
            zaak_vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )

    def setUp(self):
        super().setUp()
        # reset cache to keep request_history indexes consistent
        schema_fetcher.cache.clear()
        self.addCleanup(schema_fetcher.cache.clear)

    def test_admin_while_services_are_down(self):
        superuser = SuperUserFactory.create(app=self.app)

        # calling admin page without requests calls being set up to mimic services that are down.
        response = self.app.get(
            reverse("admin:zgw_apis_zgwapigroupconfig_change", args=(1,)),
            user=superuser,
        )
        self.assertEqual(response.status_code, 200)

        zaaktype = response.context["adminform"].form["zaaktype"]
        self.assertEqual(zaaktype.initial, self.zgw_group.zaaktype)

        zaaktype_rendered_widget = zaaktype.field.widget.render(
            zaaktype.name, [zaaktype.initial]
        )

        self.assertIn(
            "Could not load data - enable and check the request logs for more details",
            zaaktype_rendered_widget,
        )

        response.forms[0].submit()
        self.zgw_group.refresh_from_db()

        self.assertEqual(
            self.zgw_group.zaaktype, "https://catalogi-1.nl/api/v1/zaaktypen/1"
        )
