from django.db.migrations.state import StateApps

from openforms.utils.tests.test_migrations import TestMigrations


class AddZGWApiGroupConfigIdentifierTests(TestMigrations):
    app = "zgw_apis"
    migrate_from = "0015_explicit_objects_api_groups"
    migrate_to = "0016_zgwapigroupconfig_identifier"

    def setUpBeforeMigration(self, apps: StateApps):
        ZGWApiGroupConfig = apps.get_model("zgw_apis", "ZGWApiGroupConfig")
        ZGWApiGroupConfig.objects.create(name="Group name")
        ZGWApiGroupConfig.objects.create(name="Duplicate name")
        ZGWApiGroupConfig.objects.create(name="Duplicate name")

    def test_identifiers_generated(self):
        ZGWApiGroupConfig = self.apps.get_model("zgw_apis", "ZGWApiGroupConfig")
        groups = ZGWApiGroupConfig.objects.order_by("pk")

        self.assertEqual(groups.count(), 3)

        group1, group2, group3 = groups

        self.assertEqual(group1.identifier, "group-name")
        self.assertEqual(group2.identifier, "duplicate-name")
        self.assertEqual(group3.identifier, "duplicate-name-1")
