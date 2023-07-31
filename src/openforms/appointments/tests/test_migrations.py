from openforms.utils.tests.test_migrations import TestMigrations


class MigrateJCCConfiguration(TestMigrations):
    app = "appointments"
    migrate_from = "0008_rename_config_path_appointmentsconfig_plugin"
    migrate_to = "0012_rename_plugin_identifiers"

    def setUpBeforeMigration(self, apps):
        AppointmentsConfig = apps.get_model("appointments", "AppointmentsConfig")
        AppointmentsConfig.objects.create(
            plugin="openforms.appointments.contrib.jcc.models.JccConfig"
        )

    def test_jcc_config_updated(self):
        AppointmentsConfig = self.apps.get_model("appointments", "AppointmentsConfig")
        config = AppointmentsConfig.objects.get()

        self.assertEqual(config.plugin, "jcc")


class MigrateQmaticConfiguration(TestMigrations):
    app = "appointments"
    migrate_from = "0008_rename_config_path_appointmentsconfig_plugin"
    migrate_to = "0012_rename_plugin_identifiers"

    def setUpBeforeMigration(self, apps):
        AppointmentsConfig = apps.get_model("appointments", "AppointmentsConfig")
        AppointmentsConfig.objects.create(
            plugin="openforms.appointments.contrib.qmatic.models.QmaticConfig"
        )

    def test_qmatic_config_updated(self):
        AppointmentsConfig = self.apps.get_model("appointments", "AppointmentsConfig")
        config = AppointmentsConfig.objects.get()

        self.assertEqual(config.plugin, "qmatic")
