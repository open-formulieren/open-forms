from django.urls import reverse

from privates.test import temp_private_root

from openforms.utils.tests.test_migrations import TestMigrations

from .utils import TEST_FILES

BASE_URL = "https://example.com"

NO_DIGID = {
    "base_url": BASE_URL,
    "entity_id": BASE_URL,
    "metadata_file": "",
    "key_file": "",
    "cert_file": "",
    "service_entity_id": "https://was-preprod1.digid.nl/saml/idp/metadata",
    "attribute_consuming_service_index": "1",
    "requested_attributes": ["bsn"],
    "want_assertions_signed": True,
}


class DigiDConfigMigrationBase(TestMigrations):
    migrate_from = None
    migrate_to = "0001_convert_digid_setting_to_db"
    app = "authentication_digid"

    def setUpBeforeMigration(self, apps):
        DigidConfiguration = apps.get_model("digid_eherkenning", "DigidConfiguration")
        DigidConfiguration.objects.all().delete()


@temp_private_root()
class DigiDDisabledConfigMigrationTests(DigiDConfigMigrationBase):
    setting_overrides = {"DIGID": NO_DIGID}

    def test_digid_not_enabled(self):
        DigidConfiguration = self.apps.get_model(
            "digid_eherkenning", "DigidConfiguration"
        )

        qs = DigidConfiguration.objects.all()

        self.assertFalse(qs.exists())


DIGID_ENABLED_WITH_IDP_METADATA = {
    "base_url": BASE_URL,
    "entity_id": BASE_URL,
    "metadata_file": str(TEST_FILES / "metadata.xml"),
    "key_file": str(TEST_FILES / "test.key"),
    "cert_file": str(TEST_FILES / "test.certificate"),
    "service_entity_id": "https://example.com/saml/idp/metadata",
    "attribute_consuming_service_index": "3",
    "requested_attributes": ["bsn"],
    "want_assertions_signed": True,
}


@temp_private_root()
class DigiDEnabledConfigMigrationTests(DigiDConfigMigrationBase):
    setting_overrides = {"DIGID": DIGID_ENABLED_WITH_IDP_METADATA}

    def test_digid_enabled(self):
        DigidConfiguration = self.apps.get_model(
            "digid_eherkenning", "DigidConfiguration"
        )

        config = DigidConfiguration.objects.get()
        self.assertIsNotNone(config.certificate)

        with self.subTest("private key"):
            private_key = config.certificate.private_key
            self.assertTrue(bool(private_key))
            with (TEST_FILES / "test.key").open("rb") as infile:
                self.assertEqual(private_key.read(), infile.read())

        with self.subTest("public cert"):
            public_certificate = config.certificate.public_certificate
            self.assertTrue(bool(public_certificate))
            with (TEST_FILES / "test.certificate").open("rb") as infile:
                self.assertEqual(public_certificate.read(), infile.read())

        self.assertEqual(config.base_url, "https://example.com")
        self.assertEqual(config.entity_id, "https://example.com")
        self.assertEqual(
            config.idp_service_entity_id, "https://example.com/saml/idp/metadata"
        )
        self.assertEqual(config.attribute_consuming_service_index, "3")
        self.assertEqual(config.requested_attributes, ["bsn"])
        self.assertTrue(config.want_assertions_signed)
        self.assertFalse(config.slo)

        with (TEST_FILES / "metadata.xml").open("rb") as infile:
            self.assertEqual(config.idp_metadata_file.read(), infile.read())

        with self.subTest("fetch metadata"):
            response = self.client.get(reverse("metadata:digid"))

            self.assertEqual(response.status_code, 200)


DIGID_ENABLED_WITHOUT_IDP_METADATA = {
    "base_url": BASE_URL,
    "entity_id": BASE_URL,
    "metadata_file": "",
    "key_file": str(TEST_FILES / "test.key"),
    "cert_file": str(TEST_FILES / "test.certificate"),
    "service_entity_id": "https://example.com/saml/idp/metadata",
    "attribute_consuming_service_index": "3",
    "requested_attributes": ["bsn"],
    "want_assertions_signed": True,
}


@temp_private_root()
class DigiDEnabledNoIDPMetadataConfigMigrationTests(DigiDConfigMigrationBase):
    setting_overrides = {"DIGID": DIGID_ENABLED_WITHOUT_IDP_METADATA}

    def test_digid_enabled(self):
        DigidConfiguration = self.apps.get_model(
            "digid_eherkenning", "DigidConfiguration"
        )

        config = DigidConfiguration.objects.get()
        self.assertIsNotNone(config.certificate)

        with self.subTest("private key"):
            private_key = config.certificate.private_key
            self.assertTrue(bool(private_key))
            with (TEST_FILES / "test.key").open("rb") as infile:
                self.assertEqual(private_key.read(), infile.read())

        with self.subTest("public cert"):
            public_certificate = config.certificate.public_certificate
            self.assertTrue(bool(public_certificate))
            with (TEST_FILES / "test.certificate").open("rb") as infile:
                self.assertEqual(public_certificate.read(), infile.read())

        self.assertEqual(config.base_url, "https://example.com")
        self.assertEqual(config.entity_id, "https://example.com")
        self.assertEqual(
            config.idp_service_entity_id, "https://example.com/saml/idp/metadata"
        )
        self.assertEqual(config.attribute_consuming_service_index, "3")
        self.assertEqual(config.requested_attributes, ["bsn"])
        self.assertTrue(config.want_assertions_signed)
        self.assertFalse(config.slo)
        self.assertFalse(bool(config.idp_metadata_file))

        with self.subTest("fetch metadata"):
            response = self.client.get(reverse("metadata:digid"))

            self.assertEqual(response.status_code, 200)
