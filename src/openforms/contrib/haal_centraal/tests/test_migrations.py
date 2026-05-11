from django_test_migrations.contrib.unittest_case import MigratorTestCase


class HCVersionMigrationTests(MigratorTestCase):
    migrate_from = (
        "haalcentraal",
        "0004_haalcentraalconfig_brp_personen_oin_header_name",
    )
    migrate_to = (
        "haalcentraal",
        "0005_update_version",
    )

    def prepare(self):
        apps = self.old_state.apps
        HC_config = apps.get_model("haalcentraal", "HaalCentraalConfig")
        hc_config, _ = HC_config.objects.get_or_create()

        assert hc_config.brp_personen_version, "1.3"

    def test_migration_with_new_version(self):
        """
        Ensure that the data migration succeeds and we have the new version set.
        """
        HC_config = self.new_state.apps.get_model("haalcentraal", "HaalCentraalConfig")

        config = HC_config.objects.first()

        self.assertEqual(config.brp_personen_version, "2.0")
