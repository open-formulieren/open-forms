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
