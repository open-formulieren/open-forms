from django.test import TestCase

import requests
import requests_mock
from zgw_consumers.constants import APITypes
from zgw_consumers.test.factories import ServiceFactory

from openforms.plugins.exceptions import InvalidPluginConfiguration

from ..models import ObjectsAPIGroupConfig
from ..plugin import PLUGIN_IDENTIFIER, ObjectsAPIRegistration


class ConfigCheckTests(TestCase):
    def setUp(self):
        super().setUp()

        self.config = ObjectsAPIGroupConfig.objects.create(
            objects_service=ServiceFactory.create(
                api_root="https://objects.example.com/api/v1/",
            ),
            objecttypes_service=ServiceFactory.create(
                api_root="https://objecttypes.example.com/api/v1/",
            ),
            drc_service=ServiceFactory.create(
                api_root="https://documents.example.com/api/v1/",
                api_type=APITypes.drc,
            ),
            catalogi_service=None,
            productaanvraag_type="Productaanvraag",
            objecttype_version=42,
            organisatie_rsin="123456782",
        )

    def _mockForValidServiceConfiguration(self, m: requests_mock.Mocker) -> None:
        m.get(
            "https://objects.example.com/api/v1/objects?pageSize=1",
            json={"results": []},
        )
        m.get(
            "https://objecttypes.example.com/api/v1/objecttypes?pageSize=1",
            json={"results": []},
        )
        m.get(
            "https://documents.example.com/api/v1/enkelvoudiginformatieobjecten",
            json={"results": []},
        )

    def test_no_objects_service_configured(self):
        self.config.objects_service = None
        self.config.save()
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        with self.assertRaises(InvalidPluginConfiguration):
            plugin.check_config()

    @requests_mock.Mocker()
    def test_no_objecttypes_service_configured(self, m: requests_mock.Mocker):
        # Objects API needs to be set up as services are checked in a certain order
        m.get(
            "https://objects.example.com/api/v1/objects?pageSize=1",
            json={"results": []},
        )
        self.config.objecttypes_service = None
        self.config.save()
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        with self.assertRaises(InvalidPluginConfiguration):
            plugin.check_config()

    @requests_mock.Mocker()
    def test_objects_service_misconfigured_connection_error(self, m):
        m.get(
            "https://objects.example.com/api/v1/objects?pageSize=1",
            exc=requests.ConnectionError,
        )
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        with self.assertRaises(InvalidPluginConfiguration):
            plugin.check_config()

    @requests_mock.Mocker()
    def test_objects_service_misconfigured_http_error(self, m):
        m.get(
            "https://objects.example.com/api/v1/objects?pageSize=1",
            status_code=400,
        )
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        with self.assertRaises(InvalidPluginConfiguration):
            plugin.check_config()

    @requests_mock.Mocker()
    def test_objects_service_misconfigured_redirect(self, m):
        m.get(
            "https://objects.example.com/api/v1/objects?pageSize=1",
            status_code=302,
        )
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        with self.assertRaises(InvalidPluginConfiguration):
            plugin.check_config()

    @requests_mock.Mocker()
    def test_objecttypes_service_misconfigured_redirect(self, m):
        m.get(
            "https://objects.example.com/api/v1/objects?pageSize=1",
            json={"results": []},
        )
        m.get(
            "https://objecttypes.example.com/api/v1/objecttypes?pageSize=1",
            status_code=302,
        )
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        with self.assertRaises(InvalidPluginConfiguration):
            plugin.check_config()

    @requests_mock.Mocker()
    def test_no_documents_service_configured(self, m):
        self.config.drc_service = None
        self.config.save()
        m.get(
            "https://objects.example.com/api/v1/objects?pageSize=1",
            json={"results": []},
        )
        m.get(
            "https://objecttypes.example.com/api/v1/objecttypes?pageSize=1",
            json={"results": []},
        )
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        with self.assertRaises(InvalidPluginConfiguration):
            plugin.check_config()

    @requests_mock.Mocker()
    def test_invalid_url_references_with_error(self, m):
        self._mockForValidServiceConfiguration(m)
        m.get("https://example.com", exc=requests.RequestException)
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)
        fields = (
            "objecttype",
            "informatieobjecttype_submission_report",
            "informatieobjecttype_submission_csv",
            "informatieobjecttype_attachment",
        )
        for field in fields:
            with self.subTest(field=field):
                assert not getattr(self.config, field, "")
                setattr(self.config, field, "https://example.com")
                self.config.save()

                with self.assertRaises(InvalidPluginConfiguration):
                    plugin.check_config()

    @requests_mock.Mocker()
    def test_invalid_url_references_with_unexpected_status(self, m):
        self._mockForValidServiceConfiguration(m)
        m.get("https://example.com", status_code=404)
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)
        fields = (
            "objecttype",
            "informatieobjecttype_submission_report",
            "informatieobjecttype_submission_csv",
            "informatieobjecttype_attachment",
        )
        for field in fields:
            with self.subTest(field=field):
                assert not getattr(self.config, field, "")
                setattr(self.config, field, "https://example.com")
                self.config.save()

                with self.assertRaises(InvalidPluginConfiguration):
                    plugin.check_config()

    @requests_mock.Mocker()
    def test_valid_url_references(self, m):
        self._mockForValidServiceConfiguration(m)
        # these APIs typically require authentication, so HTTP 403 is 'success' for the
        # config check.
        m.get(
            "https://example.com",
            status_code=403,
            json={"status": 403, "detail": "Permission denied"},
        )
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)
        fields = (
            "objecttype",
            "informatieobjecttype_submission_report",
            "informatieobjecttype_submission_csv",
            "informatieobjecttype_attachment",
        )
        for field in fields:
            with self.subTest(field=field):
                assert not getattr(self.config, field, "")
                setattr(self.config, field, "https://example.com")
                self.config.save()

                try:
                    plugin.check_config()
                except InvalidPluginConfiguration as exc:
                    raise self.failureException(
                        "Configuration should be considered valid"
                    ) from exc
