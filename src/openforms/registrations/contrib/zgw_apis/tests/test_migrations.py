from django.db.migrations.state import StateApps

from openforms.utils.tests.test_migrations import TestMigrations


class MigrateToExplicitObjectsAPIGroupsTests(TestMigrations):
    app = "zgw_apis"
    migrate_from = "0014_zgwapigroupconfig_catalogue_domain_and_more"
    migrate_to = "0015_explicit_objects_api_groups"

    def setUpBeforeMigration(self, apps: StateApps):
        ObjectsAPIGroupConfig = apps.get_model("objects_api", "ObjectsAPIGroupConfig")
        Form = apps.get_model("forms", "Form")
        FormRegistrationBackend = apps.get_model("forms", "FormRegistrationBackend")
        form1 = Form.objects.create()
        form2 = Form.objects.create()
        self.objects_api_group = ObjectsAPIGroupConfig.objects.create(name="Group 1")
        ObjectsAPIGroupConfig.objects.create(name="Group 2")
        self.backend_without_api_group = FormRegistrationBackend.objects.create(
            form=form1, backend="zgw-create-zaak", options={}
        )
        self.backend_with_api_group = FormRegistrationBackend.objects.create(
            form=form2,
            backend="zgw-create-zaak",
            options={"objecttype": "https://objecttypes.com/foo/bar"},
        )

    def test_set_explicit_objects_api_groups_on_zgw_api_group_configs(self):
        self.backend_without_api_group.refresh_from_db()
        self.backend_with_api_group.refresh_from_db()

        self.assertEqual(
            self.backend_without_api_group.options["objects_api_group"], None
        )
        self.assertEqual(
            self.backend_with_api_group.options["objects_api_group"],
            self.objects_api_group.pk,
        )
