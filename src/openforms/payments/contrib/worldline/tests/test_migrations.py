from openforms.payments.contrib.ogone.constants import HashAlgorithm, OgoneEndpoints
from openforms.utils.tests.test_migrations import TestMigrations

from ..constants import WorldlineEndpoints


class WorldlineMigrationTest(TestMigrations):
    migrate_from = "0006_worldlinewebhookconfiguration_and_more"
    migrate_to = "0007_migrate_ogone_to_worldline"
    app = "payments_worldline"

    def setUpBeforeMigration(self, apps):
        OgoneMerchant = apps.get_model("payments_ogone", "OgoneMerchant")
        OgoneWebhookConfiguration = apps.get_model(
            "payments_ogone", "OgoneWebhookConfiguration"
        )
        OgoneMerchant.objects.create(
            label="Merchant 1",
            pspid="merchant-1",
            hash_algorithm=HashAlgorithm.sha512,
            sha_in_passphrase="SHA-IN-PASSPHRASE",
            sha_out_passphrase="SHA-OUT-PASSPHRASE",
            api_key="merchant-1-api-key",
            api_secret="merchant-1-api-secret",
            endpoint_preset=OgoneEndpoints.live,
        )
        OgoneMerchant.objects.create(
            label="Merchant 2",
            pspid="merchant-2",
            hash_algorithm=HashAlgorithm.sha512,
            sha_in_passphrase="SHA-IN-PASSPHRASE",
            sha_out_passphrase="SHA-OUT-PASSPHRASE",
            api_key="merchant-2-api-key",
            api_secret="merchant-2-api-secret",
            endpoint_preset=OgoneEndpoints.live,
        )
        OgoneMerchant.objects.create(
            label="Merchant 3",
            pspid="merchant-3",
            hash_algorithm=HashAlgorithm.sha512,
            sha_in_passphrase="SHA-IN-PASSPHRASE",
            sha_out_passphrase="SHA-OUT-PASSPHRASE",
            api_key="merchant-3-api-key",
            api_secret="merchant-3-api-secret",
            endpoint_preset=OgoneEndpoints.test,
        )

        OgoneWebhookConfiguration.objects.update_or_create(
            webhook_key_id="",
            defaults={
                "webhook_key_id": "webhook-key",
                "webhook_key_secret": "webhook-key-secret",
            },
        )

    def test_migrate_merchants(self):
        WorldlineMerchant = self.apps.get_model(
            "payments_worldline", "WorldlineMerchant"
        )
        merchants = WorldlineMerchant.objects.order_by("label")

        self.assertEqual(merchants[0].label, "Merchant 1")
        self.assertEqual(merchants[0].pspid, "merchant-1")
        self.assertEqual(merchants[0].api_key, "merchant-1-api-key")
        self.assertEqual(merchants[0].api_secret, "merchant-1-api-secret")
        self.assertEqual(merchants[0].endpoint, WorldlineEndpoints.live)

        self.assertEqual(merchants[1].label, "Merchant 2")
        self.assertEqual(merchants[1].pspid, "merchant-2")
        self.assertEqual(merchants[1].api_key, "merchant-2-api-key")
        self.assertEqual(merchants[1].api_secret, "merchant-2-api-secret")
        self.assertEqual(merchants[1].endpoint, WorldlineEndpoints.live)

        self.assertEqual(merchants[2].label, "Merchant 3")
        self.assertEqual(merchants[2].pspid, "merchant-3")
        self.assertEqual(merchants[2].api_key, "merchant-3-api-key")
        self.assertEqual(merchants[2].api_secret, "merchant-3-api-secret")
        self.assertEqual(merchants[2].endpoint, WorldlineEndpoints.test)

    def test_migrate_webhook_configuration(self):
        WorldlineWebhookConfiguration = self.apps.get_model(
            "payments_worldline", "WorldlineWebhookConfiguration"
        )
        webhook_configuration = WorldlineWebhookConfiguration.objects.get()

        self.assertEqual(webhook_configuration.webhook_key_id, "webhook-key")
        self.assertEqual(webhook_configuration.webhook_key_secret, "webhook-key-secret")


class WorldlineExistingMerchantMigrationTest(TestMigrations):
    migrate_from = "0006_worldlinewebhookconfiguration_and_more"
    migrate_to = "0007_migrate_ogone_to_worldline"
    app = "payments_worldline"

    def setUpBeforeMigration(self, apps):
        OgoneMerchant = apps.get_model("payments_ogone", "OgoneMerchant")
        WorldlineMerchant = apps.get_model("payments_worldline", "WorldlineMerchant")

        OgoneMerchant.objects.create(
            label="Merchant 1",
            pspid="merchant-1",
            hash_algorithm=HashAlgorithm.sha512,
            sha_in_passphrase="SHA-IN-PASSPHRASE",
            sha_out_passphrase="SHA-OUT-PASSPHRASE",
            api_key="merchant-1-api-key",
            api_secret="merchant-1-api-secret",
            endpoint_preset=OgoneEndpoints.live,
        )
        WorldlineMerchant.objects.create(
            label="Existing merchant",
            pspid="merchant-1",
            api_key="worldline-api-key",
            api_secret="worldline-api-secret",
            endpoint=WorldlineEndpoints.live,
        )
        OgoneMerchant.objects.create(
            label="Merchant 2 test",
            pspid="merchant-2",
            hash_algorithm=HashAlgorithm.sha512,
            sha_in_passphrase="SHA-IN-PASSPHRASE",
            sha_out_passphrase="SHA-OUT-PASSPHRASE",
            api_key="merchant-2-test-api-key",
            api_secret="merchant-2-test-api-secret",
            endpoint_preset=OgoneEndpoints.test,
        )

    def test_existing_worldline_merchant(self):
        WorldlineMerchant = self.apps.get_model(
            "payments_worldline", "WorldlineMerchant"
        )
        merchants = WorldlineMerchant.objects.order_by("label")
        self.assertEqual(len(merchants), 2)

        self.assertEqual(merchants[0].label, "Existing merchant")
        self.assertEqual(merchants[0].pspid, "merchant-1")
        self.assertEqual(merchants[0].api_key, "worldline-api-key")
        self.assertEqual(merchants[0].api_secret, "worldline-api-secret")
        self.assertEqual(merchants[0].endpoint, WorldlineEndpoints.live)

        self.assertEqual(merchants[1].label, "Merchant 2 test")
        self.assertEqual(merchants[1].pspid, "merchant-2")
        self.assertEqual(merchants[1].api_key, "merchant-2-test-api-key")
        self.assertEqual(merchants[1].api_secret, "merchant-2-test-api-secret")
        self.assertEqual(merchants[1].endpoint, WorldlineEndpoints.test)


class WorldlineIncompleteWebhookMigrationTest(TestMigrations):
    migrate_from = "0006_worldlinewebhookconfiguration_and_more"
    migrate_to = "0007_migrate_ogone_to_worldline"
    app = "payments_worldline"

    def setUpBeforeMigration(self, apps):
        OgoneWebhookConfiguration = apps.get_model(
            "payments_ogone", "OgoneWebhookConfiguration"
        )
        OgoneWebhookConfiguration.objects.create(
            webhook_key_id="webhook-key",
            webhook_key_secret="",
        )

    def test_incomplete_webhook_configuration(self):
        WorldlineWebhookConfiguration = self.apps.get_model(
            "payments_worldline", "WorldlineWebhookConfiguration"
        )
        webhook_configuration = WorldlineWebhookConfiguration.objects.get()

        self.assertEqual(webhook_configuration.webhook_key_id, "")
        self.assertEqual(webhook_configuration.webhook_key_secret, "")


class WorldlineExistingWebhookMigrationTest(TestMigrations):
    migrate_from = "0006_worldlinewebhookconfiguration_and_more"
    migrate_to = "0007_migrate_ogone_to_worldline"
    app = "payments_worldline"

    def setUpBeforeMigration(self, apps):
        OgoneWebhookConfiguration = apps.get_model(
            "payments_ogone", "OgoneWebhookConfiguration"
        )
        OgoneWebhookConfiguration.objects.create(
            webhook_key_id="webhook-key",
            webhook_key_secret="webhook-key-secret",
        )
        WorldlineWebhookConfiguration = apps.get_model(
            "payments_worldline", "WorldlineWebhookConfiguration"
        )
        WorldlineWebhookConfiguration.objects.create(
            webhook_key_id="existing-webhook-key",
            webhook_key_secret="existing-webhook-key-secret",
        )

    def test_existing_webhook_configuration(self):
        WorldlineWebhookConfiguration = self.apps.get_model(
            "payments_worldline", "WorldlineWebhookConfiguration"
        )
        webhook_configuration = WorldlineWebhookConfiguration.objects.get()

        self.assertEqual(webhook_configuration.webhook_key_id, "existing-webhook-key")
        self.assertEqual(
            webhook_configuration.webhook_key_secret, "existing-webhook-key-secret"
        )
