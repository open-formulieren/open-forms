from django.db.migrations.state import StateApps

from openforms.utils.tests.test_migrations import TestMigrations


class EnableNewBuilderMigrationTests(TestMigrations):
    app = "config"
    migrate_from = "0001_initial_to_v250"
    migrate_to = "0054_enable_new_builder"

    def setUpBeforeMigration(self, apps):
        GlobalConfiguration = apps.get_model("config", "GlobalConfiguration")
        GlobalConfiguration.objects.create(enable_react_formio_builder=False)

    def test_builder_enabled(self):
        GlobalConfiguration = self.apps.get_model("config", "GlobalConfiguration")
        config = GlobalConfiguration.objects.get()

        self.assertTrue(config.enable_react_formio_builder)


class MigrateToOrderIdTemplateExistingMigrationTests(TestMigrations):
    app = "config"
    migrate_from = "0056_globalconfiguration_enable_backend_formio_validation"
    migrate_to = "0059_remove_globalconfiguration_payment_order_id_prefix"
    setting_overrides = {"RELEASE": "a_new_release"}

    def setUpBeforeMigration(self, apps: StateApps) -> None:
        GlobalConfiguration = apps.get_model("config", "GlobalConfiguration")
        VersionInfo = apps.get_model("upgrades", "VersionInfo")

        GlobalConfiguration.objects.create(payment_order_id_prefix="{year}CUSTOM")
        version_info = VersionInfo.objects.first()
        assert version_info is not None
        version_info.current = "some_existing_version"
        version_info.save()

    def test_template_from_prefix(self) -> None:
        GlobalConfiguration = self.apps.get_model("config", "GlobalConfiguration")
        config = GlobalConfiguration.objects.get()

        self.assertEqual(config.payment_order_id_template, "{year}CUSTOM{uid}")


class MigrateToOrderIdTemplateNewMigrationTests(TestMigrations):
    app = "config"
    migrate_from = "0056_globalconfiguration_enable_backend_formio_validation"
    migrate_to = "0059_remove_globalconfiguration_payment_order_id_prefix"
    setting_overrides = {"RELEASE": "dev"}

    def setUpBeforeMigration(self, apps: StateApps) -> None:
        GlobalConfiguration = apps.get_model("config", "GlobalConfiguration")
        VersionInfo = apps.get_model("upgrades", "VersionInfo")

        GlobalConfiguration.objects.create()

        # For some reason, `current` isn't set to `"dev"` on CI:
        version_info = VersionInfo.objects.first()
        assert version_info is not None
        version_info.current = "dev"
        version_info.save()

    def test_template_default_value(self) -> None:
        GlobalConfiguration = self.apps.get_model("config", "GlobalConfiguration")
        config = GlobalConfiguration.objects.get()

        self.assertEqual(config.payment_order_id_template, "{year}/{reference}/{uid}")
