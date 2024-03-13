from zgw_consumers.constants import APITypes, AuthTypes

from openforms.utils.tests.test_migrations import TestMigrations


class KVKZoekenServicesMigrationTests(TestMigrations):
    app = "kvk"
    migrate_from = "0006_remove_refactored_service_config_fields"
    migrate_to = "0008_remove_kvkconfig_service"

    def setUpBeforeMigration(self, apps):
        Service = apps.get_model("zgw_consumers", "Service")
        _service, _ = Service.objects.get_or_create(
            api_root="https://developers.kvk.nl/test/api/v2/zoeken/",
            defaults={
                "label": "KVK API",
                "oas": "https://developers.kvk.nl/test/api/v2/zoeken/",
                "api_type": APITypes.orc,
                "auth_type": AuthTypes.api_key,
                "header_key": "apikey",
                "header_value": "",
                "client_certificate": None,
                "server_certificate": None,
            },
        )

        KVKConfiguration = apps.get_model("kvk", "KVKConfig")
        KVKConfiguration.objects.create(service=_service)

    def test_kvk_service_set_with_zoeken_preset(self):
        Service = self.apps.get_model("zgw_consumers", "Service")
        service = Service.objects.get()

        KVKConfiguration = self.apps.get_model("kvk", "KVKConfig")
        config = KVKConfiguration.objects.get()

        self.assertIsNone(config.profile_service)
        self.assertEqual(config.search_service, service)


class KVKBasisprofielenServicesMigrationTests(TestMigrations):
    app = "kvk"
    migrate_from = "0006_remove_refactored_service_config_fields"
    migrate_to = "0008_remove_kvkconfig_service"

    def setUpBeforeMigration(self, apps):
        Service = apps.get_model("zgw_consumers", "Service")
        _service, _ = Service.objects.get_or_create(
            api_root="https://developers.kvk.nl/test/api/v1/basisprofielen/",
            defaults={
                "label": "KVK API",
                "oas": "https://developers.kvk.nl/test/api/v1/basisprofielen/",
                "api_type": APITypes.orc,
                "auth_type": AuthTypes.api_key,
                "header_key": "apikey",
                "header_value": "",
                "client_certificate": None,
                "server_certificate": None,
            },
        )

        KVKConfiguration = apps.get_model("kvk", "KVKConfig")
        KVKConfiguration.objects.create(service=_service)

    def test_kvk_service_set_with_zoeken_preset(self):
        Service = self.apps.get_model("zgw_consumers", "Service")
        service = Service.objects.get()

        KVKConfiguration = self.apps.get_model("kvk", "KVKConfig")
        config = KVKConfiguration.objects.get()

        self.assertIsNone(config.search_service)
        self.assertEqual(config.profile_service, service)


class KVKGenericServicesMigrationTests(TestMigrations):
    app = "kvk"
    migrate_from = "0006_remove_refactored_service_config_fields"
    migrate_to = "0008_remove_kvkconfig_service"

    def setUpBeforeMigration(self, apps):
        Service = apps.get_model("zgw_consumers", "Service")
        _service, _ = Service.objects.get_or_create(
            api_root="https://developers.kvk.nl/test/api/",
            defaults={
                "label": "KVK API",
                "oas": "https://developers.kvk.nl/test/api/",
                "api_type": APITypes.orc,
                "auth_type": AuthTypes.api_key,
                "header_key": "apikey",
                "header_value": "",
                "client_certificate": None,
                "server_certificate": None,
            },
        )

        KVKConfiguration = apps.get_model("kvk", "KVKConfig")
        KVKConfiguration.objects.create(service=_service)

    def test_kvk_service_set_with_zoeken_preset(self):
        Service = self.apps.get_model("zgw_consumers", "Service")
        service = Service.objects.get()

        KVKConfiguration = self.apps.get_model("kvk", "KVKConfig")
        config = KVKConfiguration.objects.get()

        self.assertEqual(config.search_service, service)
        self.assertEqual(config.profile_service, service)
