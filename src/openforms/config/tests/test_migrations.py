from django.db.migrations.state import StateApps

from openforms.utils.tests.test_migrations import TestMigrations


class MigrateFeatureFlagsTests(TestMigrations):
    app = "config"
    migrate_from = "0001_initial_to_v250"
    migrate_to = "0054_v250_to_v270"

    def setUpBeforeMigration(self, apps: StateApps):
        GlobalConfiguration = apps.get_model("config", "GlobalConfiguration")
        GlobalConfiguration.objects.create(
            enable_demo_plugins=True,
            display_sdk_information=False,
        )
        FlagState = apps.get_model("flags", "FlagState")
        FlagState.objects.all().delete()

    def test_feature_flags_created(self):
        FlagState = self.apps.get_model("flags", "FlagState")
        flags = FlagState.objects.all()

        self.assertEqual(len(flags), 2)
        by_name = {flag.name: flag for flag in flags}

        flag1 = by_name["ENABLE_DEMO_PLUGINS"]
        self.assertEqual(flag1.condition, "boolean")
        self.assertEqual(flag1.value, "True")

        flag2 = by_name["DISPLAY_SDK_INFORMATION"]
        self.assertEqual(flag2.condition, "boolean")
        self.assertEqual(flag2.value, "False")


class ReverseMigrateFeatureFlagsTests(TestMigrations):
    app = "config"
    migrate_from = "0054_v250_to_v270"
    migrate_to = "0001_initial_to_v250"

    def setUpBeforeMigration(self, apps: StateApps):
        FlagState = apps.get_model("flags", "FlagState")
        FlagState.objects.all().delete()
        FlagState.objects.create(
            name="ENABLE_DEMO_PLUGINS", condition="boolean", value="yes"
        )
        FlagState.objects.create(
            name="UNRELATED", condition="invalid", value="irrelevant"
        )

        GlobalConfiguration = apps.get_model("config", "GlobalConfiguration")
        GlobalConfiguration.objects.create()

    def test_feature_flags_created(self):
        GlobalConfiguration = self.apps.get_model("config", "GlobalConfiguration")
        config = GlobalConfiguration.objects.get()

        self.assertTrue(config.enable_demo_plugins)
        self.assertFalse(config.display_sdk_information)
