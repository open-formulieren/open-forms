from django.db.migrations.state import StateApps

from openforms.utils.tests.test_migrations import TestMigrations


class AddObjectsAPIGroupIdentifierTests(TestMigrations):
    app = "objects_api"
    migrate_from = "0001_initial"
    migrate_to = "0002_objectsapigroupconfig_identifier"

    def setUpBeforeMigration(self, apps: StateApps):
        ObjectsAPIGroupConfig = apps.get_model("objects_api", "ObjectsAPIGroupConfig")
        ObjectsAPIGroupConfig.objects.create(name="Group name")
        ObjectsAPIGroupConfig.objects.create(name="Duplicate name")
        ObjectsAPIGroupConfig.objects.create(name="Duplicate name")

    def test_identifiers_generated(self):
        ObjectsAPIGroupConfig = self.apps.get_model(
            "objects_api", "ObjectsAPIGroupConfig"
        )
        groups = ObjectsAPIGroupConfig.objects.all()

        self.assertEqual(groups.count(), 3)

        group1, group2, group3 = groups

        self.assertEqual(group1.identifier, "group-name")
        self.assertEqual(group2.identifier, "duplicate-name")
        self.assertEqual(group3.identifier, "duplicate-name-1")
