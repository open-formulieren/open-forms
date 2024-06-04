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
    migrate_to = "0057_migrate_to_order_id_template"
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
    migrate_to = "0057_migrate_to_order_id_template"
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

        self.assertEqual(
            config.payment_order_id_template, "{year}/{public_reference}/{uid}"
        )


class MigrateToCoSignRequestTemplateWithNoLinksOption(TestMigrations):
    app = "config"
    migrate_from = "0057_migrate_to_order_id_template"
    migrate_to = "0058_globalconfiguration_cosign_request_template_and_more"

    def setUpBeforeMigration(self, apps: StateApps):
        GlobalConfiguration = apps.get_model("config", "GlobalConfiguration")
        GlobalConfiguration.objects.create(show_form_link_in_cosign_email=False)

    def test_template_does_not_contain_form_url_var(self):
        GlobalConfiguration = self.apps.get_model("config", "GlobalConfiguration")
        config = GlobalConfiguration.objects.get()

        with self.subTest("Link setting respected"):
            self.assertNotIn(r"{{ form_url }}", config.cosign_request_template_en)
            self.assertNotIn(r"{{ form_url }}", config.cosign_request_template_nl)

        with self.subTest("Translated in migrations"):
            self.assertTrue(
                config.cosign_request_template_en.startswith(
                    "<p>This is a request to co-sign"
                )
            )
            self.assertTrue(
                config.cosign_request_template_nl.startswith("<p>Dit is een verzoek")
            )


class MigrateFeatureFlagsTests(TestMigrations):
    app = "config"
    migrate_from = "0060_merge_20240517_1517"
    migrate_to = "0061_move_feature_flags"

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
    migrate_from = "0061_move_feature_flags"
    migrate_to = "0060_merge_20240517_1517"

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
