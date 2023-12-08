from openforms.utils.tests.test_migrations import TestMigrations


class ForwardMigration(TestMigrations):
    app = "config"
    migrate_from = "0063_auto_20231122_1816"
    migrate_to = "0064_auto_20231206_0921"


class TestFreshInstanceMigration(ForwardMigration):
    """
    Test themes data migration when deploying a fresh instance.
    """

    def test_no_config_or_themes_are_created(self):
        GlobalConfiguration = self.apps.get_model("config", "GlobalConfiguration")
        Theme = self.apps.get_model("config", "Theme")

        self.assertFalse(GlobalConfiguration.objects.exists())
        self.assertFalse(Theme.objects.exists())


class TestPristineConfigurationMigration(ForwardMigration):
    """
    Test themes data migration when no styling options have been configured.
    """

    def setUpBeforeMigration(self, apps):
        GlobalConfiguration = apps.get_model("config", "GlobalConfiguration")
        assert not GlobalConfiguration.objects.exists()
        # create a record as if it would have been created by calling get_solo()
        GlobalConfiguration.objects.create()

    def test_no_config_or_themes_are_created(self):
        GlobalConfiguration = self.apps.get_model("config", "GlobalConfiguration")
        Theme = self.apps.get_model("config", "Theme")

        self.assertTrue(GlobalConfiguration.objects.exists())
        self.assertFalse(Theme.objects.exists())


class TestExistingConfigIsMigrated(ForwardMigration):
    """
    Test themes data migration when some styling is configured.
    """

    def setUpBeforeMigration(self, apps):
        GlobalConfiguration = apps.get_model("config", "GlobalConfiguration")
        assert not GlobalConfiguration.objects.exists()
        # create a record as if it would have been created by calling get_solo()
        GlobalConfiguration.objects.create(
            theme_stylesheet="https://example.com/styles/foo.css"
        )

    def tests_theme_record_created_and_set_as_default(self):
        GlobalConfiguration = self.apps.get_model("config", "GlobalConfiguration")
        Theme = self.apps.get_model("config", "Theme")

        self.assertEqual(Theme.objects.count(), 1)
        config = GlobalConfiguration.objects.get()
        self.assertIsNotNone(config.default_theme)
        theme = config.default_theme
        self.assertEqual(theme.stylesheet, "https://example.com/styles/foo.css")
        self.assertNotEqual(theme.name, "")


class ReverseMigration(TestMigrations):
    app = "config"
    migrate_from = "0064_auto_20231206_0921"
    migrate_to = "0063_auto_20231122_1816"


class TestNoDefaultThemeReverseMigration(ReverseMigration):
    def setUpBeforeMigration(self, apps):
        GlobalConfiguration = apps.get_model("config", "GlobalConfiguration")
        Theme = apps.get_model("config", "Theme")
        assert not GlobalConfiguration.objects.exists()
        # create a record as if it would have been created by calling get_solo()
        GlobalConfiguration.objects.create()
        assert not Theme.objects.exists()

    def test_style_fields_have_empty_defaults(self):
        GlobalConfiguration = self.apps.get_model("config", "GlobalConfiguration")
        config = GlobalConfiguration.objects.get()

        self.assertEqual(config.logo, "")
        self.assertEqual(config.theme_classname, "")
        self.assertEqual(config.theme_stylesheet, "")
        self.assertEqual(config.theme_stylesheet_file, "")
        self.assertEqual(config.design_token_values, {})


class DefaultThemeConvertedBackTests(ReverseMigration):
    def setUpBeforeMigration(self, apps):
        GlobalConfiguration = apps.get_model("config", "GlobalConfiguration")
        Theme = apps.get_model("config", "Theme")
        Theme.objects.create(
            name="not default", stylesheet="https://example.com/first.css"
        )
        theme2 = Theme.objects.create(
            name="default",
            classname="foo",
            stylesheet="https://example.com/second.css",
            design_token_values={"utrecht": {"link": {"color": {"value": "red"}}}},
        )
        GlobalConfiguration.objects.create(default_theme=theme2)

    def test_style_fields_have_empty_defaults(self):
        GlobalConfiguration = self.apps.get_model("config", "GlobalConfiguration")
        config = GlobalConfiguration.objects.get()

        self.assertEqual(config.logo, "")
        self.assertEqual(config.theme_classname, "foo")
        self.assertEqual(config.theme_stylesheet, "https://example.com/second.css")
        self.assertEqual(config.theme_stylesheet_file, "")
        self.assertEqual(
            config.design_token_values,
            {"utrecht": {"link": {"color": {"value": "red"}}}},
        )
