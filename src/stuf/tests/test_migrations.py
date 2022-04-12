from pathlib import Path

from django.core.files import File

from openforms.utils.tests.test_migrations import TestMigrations

from ..constants import SOAPVersion

TEST_CERTIFICATES = Path(__file__).parent / "data"

CERTIFICATE_FILE = TEST_CERTIFICATES / "test.certificate"
KEY_FILE = TEST_CERTIFICATES / "test.key"


class SOAPServiceWithCertificatesForwardMigrationTests(TestMigrations):
    migrate_from = "0009_auto_20220404_1050"
    migrate_to = "0010_auto_20220404_1053"
    app = "stuf"

    def setUpBeforeMigration(self, apps):
        SoapService = apps.get_model("stuf", "SoapService")
        StufService = apps.get_model("stuf", "StufService")

        self.soap_service = SoapService.objects.create(
            url="http://test.api.nl", label="Test SOAP Service"
        )

        with CERTIFICATE_FILE.open("r") as f_certificate, KEY_FILE.open("r") as f_key:
            self.stuf_service = StufService.objects.create(
                soap_service=self.soap_service,
                ontvanger_applicatie="Test application",
                zender_applicatie="Open Forms",
                soap_version=SOAPVersion.soap11,
                user="user123",
                password="password123",
                certificate=File(f_certificate, name="test.certificate"),
                certificate_key=File(f_key, name="test.key"),
            )

    def test_certificates_in_new_model(self):
        SoapService = self.apps.get_model("stuf", "SoapService")

        updated_soap_service = SoapService.objects.get(id=self.soap_service.id)

        self.assertIsNotNone(updated_soap_service.client_certificate)
        self.assertIsNone(updated_soap_service.server_certificate)
        self.assertEqual("user123", updated_soap_service.user)
        self.assertEqual("password123", updated_soap_service.password)
        self.assertEqual(SOAPVersion.soap11, updated_soap_service.soap_version)


class SOAPServiceWithoutCertificatesForwardMigrationTests(TestMigrations):
    migrate_from = "0009_auto_20220404_1050"
    migrate_to = "0010_auto_20220404_1053"
    app = "stuf"

    def setUpBeforeMigration(self, apps):
        SoapService = apps.get_model("stuf", "SoapService")
        StufService = apps.get_model("stuf", "StufService")

        self.soap_service = SoapService.objects.create(
            url="http://test.api.nl", label="Test SOAP Service"
        )

        self.stuf_service = StufService.objects.create(
            soap_service=self.soap_service,
            ontvanger_applicatie="Test application",
            zender_applicatie="Open Forms",
            soap_version=SOAPVersion.soap11,
            user="user123",
            password="password123",
        )

    def test_fields_in_new_model(self):
        SoapService = self.apps.get_model("stuf", "SoapService")

        updated_soap_service = SoapService.objects.get(id=self.soap_service.id)

        self.assertIsNone(updated_soap_service.client_certificate)
        self.assertIsNone(updated_soap_service.server_certificate)
        self.assertEqual("user123", updated_soap_service.user)
        self.assertEqual("password123", updated_soap_service.password)
        self.assertEqual(SOAPVersion.soap11, updated_soap_service.soap_version)


class SOAPServiceWithCertificatesBackwardMigrationTests(TestMigrations):
    migrate_to = "0009_auto_20220404_1050"
    migrate_from = "0010_auto_20220404_1053"
    app = "stuf"

    def setUpBeforeMigration(self, apps):
        SoapService = apps.get_model("stuf", "SoapService")
        StufService = apps.get_model("stuf", "StufService")
        Certificate = apps.get_model("zgw_consumers", "Certificate")

        with CERTIFICATE_FILE.open("r") as f_certificate, KEY_FILE.open("r") as f_key:
            client_certificate = Certificate.objects.create(
                public_certificate=File(f_certificate, name="test.certificate"),
                private_key=File(f_key, name="test.key"),
            )

        self.soap_service = SoapService.objects.create(
            url="http://test.api.nl",
            label="Test SOAP Service",
            client_certificate=client_certificate,
            soap_version=SOAPVersion.soap11,
            user="user123",
            password="password123",
        )

        self.stuf_service = StufService.objects.create(
            soap_service=self.soap_service,
            ontvanger_applicatie="Test application",
            zender_applicatie="Open Forms",
        )

    def test_fields_in_old_model(self):
        StufService = self.apps.get_model("stuf", "StufService")

        service = StufService.objects.get(id=self.stuf_service.id)

        self.assertTrue(bool(service.certificate))
        self.assertFalse(bool(service.certificate_key))
        self.assertEqual("user123", service.user)
        self.assertEqual("password123", service.password)
        self.assertEqual(SOAPVersion.soap11, service.soap_version)


class SOAPServiceWithoutCertificatesBackwardMigrationTests(TestMigrations):
    migrate_to = "0009_auto_20220404_1050"
    migrate_from = "0010_auto_20220404_1053"
    app = "stuf"

    def setUpBeforeMigration(self, apps):
        SoapService = apps.get_model("stuf", "SoapService")
        StufService = apps.get_model("stuf", "StufService")

        self.soap_service = SoapService.objects.create(
            url="http://test.api.nl",
            label="Test SOAP Service",
            soap_version=SOAPVersion.soap11,
            user="user123",
            password="password123",
        )

        self.stuf_service = StufService.objects.create(
            soap_service=self.soap_service,
            ontvanger_applicatie="Test application",
            zender_applicatie="Open Forms",
        )

    def test_fields_in_old_model(self):
        StufService = self.apps.get_model("stuf", "StufService")

        service = StufService.objects.get(id=self.stuf_service.id)

        self.assertFalse(bool(service.certificate))
        self.assertFalse(bool(service.certificate_key))
        self.assertEqual("user123", service.user)
        self.assertEqual("password123", service.password)
        self.assertEqual(SOAPVersion.soap11, service.soap_version)
