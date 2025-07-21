from django.test import TestCase

import requests_mock
from privates.test import temp_private_root
from requests.models import HTTPError
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen
from zgw_consumers.test import generate_oas_component

from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
)

from ..plugin import ZGWRegistration
from ..typing import RegistrationOptions
from .factories import ZGWApiGroupConfigFactory


@temp_private_root()
@requests_mock.Mocker()
class ZGWRegistrationMultipleZGWAPIsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.zgw_group1 = ZGWApiGroupConfigFactory.create(
            zrc_service__api_root="https://zaken-1.nl/api/v1/",
            drc_service__api_root="https://documenten-1.nl/api/v1/",
            ztc_service__api_root="https://catalogi-1.nl/api/v1/",
            organisatie_rsin="000000000",
            zaak_vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        cls.zgw_group2 = ZGWApiGroupConfigFactory.create(
            zrc_service__api_root="https://zaken-2.nl/api/v1/",
            drc_service__api_root="https://documenten-2.nl/api/v1/",
            ztc_service__api_root="https://catalogi-2.nl/api/v1/",
            organisatie_rsin="000000001",
            zaak_vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.beperkt_openbaar,
        )

    def install_mocks(self, m):
        # API set 1
        m.get("https://zaken-1.nl/api/v1/zaken", status_code=200, json=[])
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
            "https://catalogi-1.nl/api/v1/roltypen?zaaktype=https%3A%2F%2Fcatalogi-1.nl%2Fapi%2Fv1%2Fzaaktypen%2F1&omschrijvingGeneriek=initiator",
            status_code=200,
            json={
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    generate_oas_component(
                        "catalogi",
                        "schemas/RolType",
                        url="https://catalogi-1.nl/api/v1/roltypen/1",
                    )
                ],
            },
            headers={"API-version": "1.0.0"},
        )
        m.post(
            "https://zaken-1.nl/api/v1/rollen",
            status_code=201,
            json=generate_oas_component(
                "zaken", "schemas/Rol", url="https://zaken-1.nl/api/v1/rollen/1"
            ),
        )
        m.get(
            "https://catalogi-1.nl/api/v1/statustypen?zaaktype=https%3A%2F%2Fcatalogi-1.nl%2Fapi%2Fv1%2Fzaaktypen%2F1",
            status_code=200,
            json={
                "count": 2,
                "next": None,
                "previous": None,
                "results": [
                    generate_oas_component(
                        "catalogi",
                        "schemas/StatusType",
                        url="https://catalogi-1.nl/api/v1/statustypen/2",
                        volgnummer=2,
                    ),
                    generate_oas_component(
                        "catalogi",
                        "schemas/StatusType",
                        url="https://catalogi-1.nl/api/v1/statustypen/1",
                        volgnummer=1,
                    ),
                ],
            },
            headers={"API-version": "1.0.0"},
        )
        m.get(
            "https://catalogi-1.nl/api/v1/zaaktypen",
            status_code=200,
            json=[],
            headers={"API-version": "1.0.0"},
        )
        m.post(
            "https://zaken-1.nl/api/v1/statussen",
            status_code=201,
            json=generate_oas_component(
                "zaken", "schemas/Status", url="https://zaken-1.nl/api/v1/statussen/1"
            ),
        )

        # API set 2
        m.get("https://zaken-2.nl/api/v1/zaken", status_code=200, json=[])
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
            "https://catalogi-2.nl/api/v1/roltypen?zaaktype=https%3A%2F%2Fcatalogi-2.nl%2Fapi%2Fv1%2Fzaaktypen%2F1&omschrijvingGeneriek=initiator",
            status_code=200,
            json={
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    generate_oas_component(
                        "catalogi",
                        "schemas/RolType",
                        url="https://catalogi-2.nl/api/v1/roltypen/1",
                    )
                ],
            },
            headers={"API-version": "1.0.0"},
        )
        m.get(
            "https://catalogi-2.nl/api/v1/roltypen?zaaktype=https%3A%2F%2Fcatalogi-2.nl%2Fapi%2Fv1%2Fzaaktypen%2F2&omschrijvingGeneriek=initiator",
            status_code=200,
            json={
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    generate_oas_component(
                        "catalogi",
                        "schemas/RolType",
                        url="https://catalogi-2.nl/api/v1/roltypen/2",
                    )
                ],
            },
            headers={"API-version": "1.0.0"},
        )
        m.get(
            "https://catalogi-2.nl/api/v1/zaaktypen",
            status_code=200,
            json=[],
            headers={"API-version": "1.0.0"},
        )
        m.post(
            "https://zaken-2.nl/api/v1/rollen",
            status_code=201,
            json=generate_oas_component(
                "zaken", "schemas/Rol", url="https://zaken-2.nl/api/v1/rollen/1"
            ),
        )
        m.get(
            "https://catalogi-2.nl/api/v1/statustypen?zaaktype=https%3A%2F%2Fcatalogi-2.nl%2Fapi%2Fv1%2Fzaaktypen%2F1",
            status_code=200,
            json={
                "count": 2,
                "next": None,
                "previous": None,
                "results": [
                    generate_oas_component(
                        "catalogi",
                        "schemas/StatusType",
                        url="https://catalogi-2.nl/api/v1/statustypen/2",
                        volgnummer=2,
                    ),
                    generate_oas_component(
                        "catalogi",
                        "schemas/StatusType",
                        url="https://catalogi-2.nl/api/v1/statustypen/1",
                        volgnummer=1,
                    ),
                ],
            },
            headers={"API-version": "1.0.0"},
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
            [{"key": "field1", "type": "file"}],
            submitted_data={
                "field1": "Foo",
            },
            completed=True,
        )
        # Configure to use the second ZGW API
        SubmissionFileAttachmentFactory.create(
            submission_step=submission.steps[0],
            file_name="attachment1.jpg",
            form_key="field1",
            _component_configuration_path="components.0",
        )
        zgw_form_options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group2,
            "case_type_identification": "",
            "document_type_description": "",
            "zaaktype": "https://catalogi-2.nl/api/v1/zaaktypen/1",
            "informatieobjecttype": "https://catalogi-2.nl/api/v1/informatieobjecttypen/1",
            "objects_api_group": None,
            "product_url": "",
            "partners_roltype": "",
            "partners_description": "",
        }
        self.install_mocks(m)

        plugin = ZGWRegistration("zgw")
        pre_registration_result = plugin.pre_register_submission(
            submission, zgw_form_options
        )

        assert submission.registration_result is not None
        assert isinstance(pre_registration_result.data, dict)
        submission.public_registration_reference = pre_registration_result.reference
        submission.registration_result.update(pre_registration_result.data)
        submission.save()

        plugin.register_submission(submission, zgw_form_options)

        history = m.request_history
        for request in history:
            self.assertTrue(request.hostname.endswith("-2.nl"))

    def test_per_form_overwrites(self, m):
        submission = SubmissionFactory.from_components(
            [{"key": "field1", "type": "file"}],
            submitted_data={"field1": "Foo"},
            completed=True,
        )
        SubmissionFileAttachmentFactory.create(
            submission_step=submission.steps[0],
            file_name="attachment1.jpg",
            form_key="field1",
            _component_configuration_path="components.0",
        )
        zgw_form_options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group2,  # Configure to use the second ZGW API
            "case_type_identification": "",
            "document_type_description": "",
            "zaaktype": "https://catalogi-2.nl/api/v1/zaaktypen/2",
            "informatieobjecttype": "https://catalogi-2.nl/api/v1/informatieobjecttypen/2",
            "organisatie_rsin": "000000123",
            "zaak_vertrouwelijkheidaanduiding": "confidentieel",
            "doc_vertrouwelijkheidaanduiding": "geheim",
            "objects_api_group": None,
            "product_url": "",
            "partners_roltype": "",
            "partners_description": "",
        }

        self.install_mocks(m)

        plugin = ZGWRegistration("zgw")
        pre_registration_result = plugin.pre_register_submission(
            submission, zgw_form_options
        )

        assert submission.registration_result is not None
        assert isinstance(pre_registration_result.data, dict)
        submission.public_registration_reference = pre_registration_result.reference
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

        zaak_body = create_zaak.json()
        report_body = create_pdf_document.json()
        attachment_body = create_attachment_document.json()

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
            completed=True,
        )
        SubmissionFileAttachmentFactory.create(
            submission_step=submission.steps[0],
            file_name="attachment1.jpg",
            form_key="field1",
            _component_configuration_path="components.0",
        )
        zgw_form_options: RegistrationOptions = {
            "zgw_api_group": self.zgw_group2,
            "case_type_identification": "",
            "document_type_description": "",
            "zaaktype": "https://catalogi-2.nl/api/v1/zaaktypen/2",
            "informatieobjecttype": "https://catalogi-2.nl/api/v1/informatieobjecttypen/2",
            "organisatie_rsin": "000000123",
            "zaak_vertrouwelijkheidaanduiding": "confidentieel",
            "doc_vertrouwelijkheidaanduiding": "geheim",
            "objects_api_group": None,
            "product_url": "",
            "partners_roltype": "",
            "partners_description": "",
        }
        self.install_mocks(m)

        plugin = ZGWRegistration("zgw")
        pre_registration_result = plugin.pre_register_submission(
            submission, zgw_form_options
        )

        assert submission.registration_result is not None
        assert isinstance(pre_registration_result.data, dict)
        submission.public_registration_reference = pre_registration_result.reference
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
        attachment_body = create_attachment_document.json()

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

        self.assertEqual(len(m.request_history), 6)
        (
            list_zaken_1,
            list_documenten_1,
            list_zaaktypen_1,
            list_zaken_2,
            list_documenten_2,
            list_zaaktypen_2,
        ) = m.request_history

        self.assertEqual(list_zaken_1.hostname, "zaken-1.nl")
        self.assertEqual(list_documenten_1.hostname, "documenten-1.nl")
        self.assertEqual(list_zaaktypen_1.hostname, "catalogi-1.nl")

        self.assertEqual(list_zaken_2.hostname, "zaken-2.nl")
        self.assertEqual(list_documenten_2.hostname, "documenten-2.nl")
        self.assertEqual(list_zaaktypen_2.hostname, "catalogi-2.nl")

    def test_check_config_http_error(self, m):
        self.install_mocks(m)
        m.get("https://zaken-1.nl/api/v1/zaken", exc=HTTPError)

        plugin = ZGWRegistration("zgw")
        with self.assertRaises(InvalidPluginConfiguration):
            plugin.check_config()

    def test_check_config_random_error(self, m):
        self.install_mocks(m)
        m.get("https://zaken-1.nl/api/v1/zaken", exc=Exception)

        plugin = ZGWRegistration("zgw")
        with self.assertRaises(InvalidPluginConfiguration):
            plugin.check_config()
