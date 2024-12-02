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
        form1 = Form.objects.create(name="form1")
        form2 = Form.objects.create(name="form2")
        self.objects_api_group = ObjectsAPIGroupConfig.objects.create(
            identifier="group-1", name="Group 1"
        )
        ObjectsAPIGroupConfig.objects.create(identifier="group-2", name="Group 2")
        self.backend_without_api_group = FormRegistrationBackend.objects.create(
            form=form1, backend="zgw-create-zaak", options={}
        )
        self.backend_with_api_group = FormRegistrationBackend.objects.create(
            form=form2,
            backend="zgw-create-zaak",
            options={"objecttype": "https://objecttypes.com/foo/bar"},
        )

    def test_set_explicit_objects_api_groups_on_zgw_api_group_configs(self):
        FormRegistrationBackend = self.apps.get_model(
            "forms", "FormRegistrationBackend"
        )
        backend_without_api_group = FormRegistrationBackend.objects.get(
            pk=self.backend_without_api_group.pk
        )
        backend_with_api_group = FormRegistrationBackend.objects.get(
            pk=self.backend_with_api_group.pk
        )

        self.assertIsNone(backend_without_api_group.options["objects_api_group"])
        self.assertEqual(
            backend_with_api_group.options["objects_api_group"],
            self.objects_api_group.pk,
        )


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
        groups = ZGWApiGroupConfig.objects.all()

        self.assertEqual(groups.count(), 3)

        group1, group2, group3 = groups

        self.assertEqual(group1.identifier, "group-name")
        self.assertEqual(group2.identifier, "duplicate-name")
        self.assertEqual(group3.identifier, "duplicate-name-1")
