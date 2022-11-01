from django.urls import reverse

from privates.test import temp_private_root

from openforms.utils.tests.test_migrations import TestMigrations

from .utils import TEST_FILES

BASE_URL = "https://example.com"

# Default settings from the before times.
NO_EHERKENNING = {
    "metadata_file": "",
    "key_file": "",
    "cert_file": "",
    "base_url": BASE_URL,
    "entity_id": "",
    "service_entity_id": "",
    "want_assertions_signed": True,
    "want_assertions_encrypted": False,
    "signature_algorithm": "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256",
    "oin": "",
    "artifact_resolve_content_type": "",
    "services": [
        {
            "attribute_consuming_service_index": "1",
            "service_loa": "urn:etoegang:core:assurance-class:loa3",
            "service_uuid": "",
            "service_instance_uuid": "",
            "service_url": BASE_URL,
            # Either require and return RSIN and KVKNr (set 1) or require only KvKnr (set 2). The
            # latter is needed for 'eenmanszaak'
            "entity_concerned_types_allowed": [
                {"set_number": "1", "name": "urn:etoegang:1.9:EntityConcernedID:RSIN"},
                {"set_number": "1", "name": "urn:etoegang:1.9:EntityConcernedID:KvKnr"},
                {"set_number": "2", "name": "urn:etoegang:1.9:EntityConcernedID:KvKnr"},
            ],
            "requested_attributes": [],
            "language": "nl",
        },
        {
            "attribute_consuming_service_index": "2",
            "service_loa": "urn:etoegang:core:assurance-class:loa3",
            "service_uuid": "",
            "service_instance_uuid": "",
            "service_url": BASE_URL,
            "entity_concerned_types_allowed": [
                {"set_number": "1", "name": "urn:etoegang:1.9:EntityConcernedID:KvKnr"},
            ],
            "requested_attributes": [],
            "language": "nl",
            "classifiers": ["eIDAS-inbound"],
        },
    ],
}


class EHerkenningConfigMigrationBase(TestMigrations):
    migrate_from = None
    migrate_to = "0001_convert_eherkenning_setting_to_db"
    app = "authentication_eherkenning"

    def setUpBeforeMigration(self, apps):
        EherkenningConfiguration = apps.get_model(
            "digid_eherkenning", "EherkenningConfiguration"
        )
        EherkenningConfiguration.objects.all().delete()


@temp_private_root()
class EHerkenningDisabledConfigMigrationTests(EHerkenningConfigMigrationBase):
    setting_overrides = {
        "EHERKENNING": NO_EHERKENNING,
        "EHERKENNING_LOA": "urn:etoegang:core:assurance-class:loa3",
    }

    def test_eherkenning_not_enabled(self):
        EherkenningConfiguration = self.apps.get_model(
            "digid_eherkenning", "EherkenningConfiguration"
        )

        qs = EherkenningConfiguration.objects.all()

        self.assertFalse(qs.exists())


EHERKENNING_ENABLED_WITH_IDP_METADATA = {
    "metadata_file": str(TEST_FILES / "eherkenning-metadata.xml"),
    "key_file": str(TEST_FILES / "test.key"),
    "cert_file": str(TEST_FILES / "test.certificate"),
    "base_url": BASE_URL,
    "entity_id": BASE_URL,
    "service_entity_id": "urn:etoegang:DV:00000001111111111000:entities:9000",
    "want_assertions_signed": True,
    "want_assertions_encrypted": False,
    "signature_algorithm": "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256",
    "oin": "00000000000000000000",
    "artifact_resolve_content_type": "",
    "services": [
        {
            "attribute_consuming_service_index": "1",
            "service_loa": "urn:etoegang:core:assurance-class:loa3",
            "service_uuid": "",
            "service_instance_uuid": "",
            "service_url": BASE_URL,
            # Either require and return RSIN and KVKNr (set 1) or require only KvKnr (set 2). The
            # latter is needed for 'eenmanszaak'
            "entity_concerned_types_allowed": [
                {"set_number": "1", "name": "urn:etoegang:1.9:EntityConcernedID:RSIN"},
                {"set_number": "1", "name": "urn:etoegang:1.9:EntityConcernedID:KvKnr"},
                {"set_number": "2", "name": "urn:etoegang:1.9:EntityConcernedID:KvKnr"},
            ],
            "requested_attributes": [],
            "language": "nl",
        },
        {
            "attribute_consuming_service_index": "2",
            "service_loa": "urn:etoegang:core:assurance-class:loa3",
            "service_uuid": "",
            "service_instance_uuid": "",
            "service_url": BASE_URL,
            "entity_concerned_types_allowed": [
                {"set_number": "1", "name": "urn:etoegang:1.9:EntityConcernedID:KvKnr"},
            ],
            "requested_attributes": [],
            "language": "nl",
            "classifiers": ["eIDAS-inbound"],
        },
    ],
}


@temp_private_root()
class EHerkenningEnabledConfigMigrationTests(EHerkenningConfigMigrationBase):
    setting_overrides = {
        "EHERKENNING": EHERKENNING_ENABLED_WITH_IDP_METADATA,
        "EHERKENNING_LOA": "urn:etoegang:core:assurance-class:loa3",
    }

    def test_eherkenning_and_eidas_enabled(self):
        EherkenningConfiguration = self.apps.get_model(
            "digid_eherkenning", "EherkenningConfiguration"
        )

        config = EherkenningConfiguration.objects.get()
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
            config.idp_service_entity_id,
            "urn:etoegang:DV:00000001111111111000:entities:9000",
        )
        self.assertTrue(config.want_assertions_signed)
        self.assertFalse(config.want_assertions_encrypted)
        self.assertEqual(
            config.signature_algorithm,
            "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256",
        )
        self.assertEqual(config.oin, "00000000000000000000")
        self.assertEqual(config.artifact_resolve_content_type, "")
        self.assertEqual(config.service_language, "nl")
        self.assertFalse(config.no_eidas)

        with self.subTest("eHerkenning"):
            self.assertEqual(config.eh_attribute_consuming_service_index, "1")
            self.assertEqual(config.eh_requested_attributes, [])
            self.assertIsNotNone(config.eh_service_uuid)
            self.assertIsNotNone(config.eh_service_instance_uuid)

        with self.subTest("eIDAS"):
            self.assertEqual(config.eidas_attribute_consuming_service_index, "2")
            self.assertEqual(config.eidas_requested_attributes, [])
            self.assertIsNotNone(config.eidas_service_uuid)
            self.assertIsNotNone(config.eidas_service_instance_uuid)

        with (TEST_FILES / "eherkenning-metadata.xml").open("rb") as infile:
            self.assertEqual(config.idp_metadata_file.read(), infile.read())

        with self.subTest("fetch metadata"):
            response = self.client.get(reverse("metadata:eherkenning"))

            self.assertEqual(response.status_code, 200)

        with self.subTest("fetch dienstcatalogus"):
            response = self.client.get(reverse("metadata:eh-dienstcatalogus"))

            self.assertEqual(response.status_code, 200)


EHERKENNING_ENABLED_WITHOUT_IDP_METADATA = {
    "key_file": str(TEST_FILES / "test.key"),
    "cert_file": str(TEST_FILES / "test.certificate"),
    "metadata_file": "",
    "base_url": BASE_URL,
    "entity_id": BASE_URL,
    "service_entity_id": "urn:etoegang:DV:00000001111111111000:entities:9000",
    "want_assertions_signed": True,
    "want_assertions_encrypted": False,
    "signature_algorithm": "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256",
    "oin": "00000000000000000000",
    "artifact_resolve_content_type": "",
    "services": [
        {
            "attribute_consuming_service_index": "1",
            "service_loa": "urn:etoegang:core:assurance-class:loa3",
            "service_uuid": "",
            "service_instance_uuid": "",
            "service_url": BASE_URL,
            # Either require and return RSIN and KVKNr (set 1) or require only KvKnr (set 2). The
            # latter is needed for 'eenmanszaak'
            "entity_concerned_types_allowed": [
                {"set_number": "1", "name": "urn:etoegang:1.9:EntityConcernedID:RSIN"},
                {"set_number": "1", "name": "urn:etoegang:1.9:EntityConcernedID:KvKnr"},
                {"set_number": "2", "name": "urn:etoegang:1.9:EntityConcernedID:KvKnr"},
            ],
            "requested_attributes": [],
            "language": "nl",
        },
        {
            "attribute_consuming_service_index": "2",
            "service_loa": "urn:etoegang:core:assurance-class:loa3",
            "service_uuid": "",
            "service_instance_uuid": "",
            "service_url": BASE_URL,
            "entity_concerned_types_allowed": [
                {"set_number": "1", "name": "urn:etoegang:1.9:EntityConcernedID:KvKnr"},
            ],
            "requested_attributes": [],
            "language": "nl",
            "classifiers": ["eIDAS-inbound"],
        },
    ],
}


@temp_private_root()
class EHerkenningEnabledNoIDPMetadataConfigMigrationTests(
    EHerkenningConfigMigrationBase
):
    setting_overrides = {
        "EHERKENNING": EHERKENNING_ENABLED_WITHOUT_IDP_METADATA,
        "EHERKENNING_LOA": "urn:etoegang:core:assurance-class:loa3",
    }

    def test_eherkenning_and_eidas_enabled(self):
        EherkenningConfiguration = self.apps.get_model(
            "digid_eherkenning", "EherkenningConfiguration"
        )

        config = EherkenningConfiguration.objects.get()
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
            config.idp_service_entity_id,
            "urn:etoegang:DV:00000001111111111000:entities:9000",
        )
        self.assertTrue(config.want_assertions_signed)
        self.assertFalse(config.want_assertions_encrypted)
        self.assertEqual(
            config.signature_algorithm,
            "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256",
        )
        self.assertEqual(config.oin, "00000000000000000000")
        self.assertEqual(config.artifact_resolve_content_type, "")
        self.assertEqual(config.service_language, "nl")
        self.assertFalse(config.no_eidas)

        with self.subTest("eHerkenning"):
            self.assertEqual(config.eh_attribute_consuming_service_index, "1")
            self.assertEqual(config.eh_requested_attributes, [])
            self.assertIsNotNone(config.eh_service_uuid)
            self.assertIsNotNone(config.eh_service_instance_uuid)

        with self.subTest("eIDAS"):
            self.assertEqual(config.eidas_attribute_consuming_service_index, "2")
            self.assertEqual(config.eidas_requested_attributes, [])
            self.assertIsNotNone(config.eidas_service_uuid)
            self.assertIsNotNone(config.eidas_service_instance_uuid)

        self.assertFalse(bool(config.idp_metadata_file))

        with self.subTest("fetch metadata"):
            response = self.client.get(reverse("metadata:eherkenning"))

            self.assertEqual(response.status_code, 200)

        with self.subTest("fetch dienstcatalogus"):
            response = self.client.get(reverse("metadata:eh-dienstcatalogus"))

            self.assertEqual(response.status_code, 200)


EHERKENNING_ENABLED_WITHOUT_EIDAS = {
    "metadata_file": "",
    "key_file": str(TEST_FILES / "test.key"),
    "cert_file": str(TEST_FILES / "test.certificate"),
    "base_url": BASE_URL,
    "entity_id": BASE_URL,
    "service_entity_id": "urn:etoegang:DV:00000001111111111000:entities:9000",
    "want_assertions_signed": True,
    "want_assertions_encrypted": False,
    "signature_algorithm": "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256",
    "oin": "00000000000000000000",
    "artifact_resolve_content_type": "",
    "services": [
        {
            "attribute_consuming_service_index": "1",
            "service_loa": "urn:etoegang:core:assurance-class:loa3",
            "service_uuid": "",
            "service_instance_uuid": "",
            "service_url": BASE_URL,
            # Either require and return RSIN and KVKNr (set 1) or require only KvKnr (set 2). The
            # latter is needed for 'eenmanszaak'
            "entity_concerned_types_allowed": [
                {"set_number": "1", "name": "urn:etoegang:1.9:EntityConcernedID:RSIN"},
                {"set_number": "1", "name": "urn:etoegang:1.9:EntityConcernedID:KvKnr"},
                {"set_number": "2", "name": "urn:etoegang:1.9:EntityConcernedID:KvKnr"},
            ],
            "requested_attributes": [],
            "language": "nl",
        },
    ],
}


@temp_private_root()
class EHerkenningEnabledWithoutEIDASConfigMigrationTests(
    EHerkenningConfigMigrationBase
):
    setting_overrides = {
        "EHERKENNING": EHERKENNING_ENABLED_WITHOUT_EIDAS,
        "EHERKENNING_LOA": "urn:etoegang:core:assurance-class:loa3",
    }

    def test_eherkenning_enabled_eidas_disabled(self):
        EherkenningConfiguration = self.apps.get_model(
            "digid_eherkenning", "EherkenningConfiguration"
        )

        config = EherkenningConfiguration.objects.get()
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
            config.idp_service_entity_id,
            "urn:etoegang:DV:00000001111111111000:entities:9000",
        )
        self.assertTrue(config.want_assertions_signed)
        self.assertFalse(config.want_assertions_encrypted)
        self.assertEqual(
            config.signature_algorithm,
            "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256",
        )
        self.assertEqual(config.oin, "00000000000000000000")
        self.assertEqual(config.artifact_resolve_content_type, "")
        self.assertEqual(config.service_language, "nl")
        self.assertTrue(config.no_eidas)

        with self.subTest("eHerkenning"):
            self.assertEqual(config.eh_attribute_consuming_service_index, "1")
            self.assertEqual(config.eh_requested_attributes, [])
            self.assertIsNotNone(config.eh_service_uuid)
            self.assertIsNotNone(config.eh_service_instance_uuid)

        with self.subTest("eIDAS"):
            self.assertEqual(config.eidas_attribute_consuming_service_index, "9053")
            self.assertEqual(config.eidas_requested_attributes, [])
            self.assertIsNotNone(config.eidas_service_uuid)
            self.assertIsNotNone(config.eidas_service_instance_uuid)

        self.assertFalse(bool(config.idp_metadata_file))

        with self.subTest("fetch metadata"):
            response = self.client.get(reverse("metadata:eherkenning"))

            self.assertEqual(response.status_code, 200)

        with self.subTest("fetch dienstcatalogus"):
            response = self.client.get(reverse("metadata:eh-dienstcatalogus"))

            self.assertEqual(response.status_code, 200)
