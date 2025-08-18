from zgw_consumers.constants import APITypes, AuthTypes

from openforms.utils.tests.test_migrations import TestMigrations


class ObjectsApiGroupMigrationTest(TestMigrations):
    migrate_from = "0108_form_internal_remarks"
    migrate_to = "0109_data_migrate_objects_api_group"
    app = "forms"

    def setUpBeforeMigration(self, apps):
        Service = apps.get_model("zgw_consumers", "Service")
        ObjectsAPIGroupConfig = apps.get_model("objects_api", "ObjectsAPIGroupConfig")
        Form = apps.get_model("forms", "Form")
        FormRegistrationBackend = apps.get_model("forms", "FormRegistrationBackend")

        objects_service = Service.objects.create(
            slug="objects-api",
            api_root="http://example.org/objects-api/api/v2/",
            api_type=APITypes.orc,
            auth_type=AuthTypes.no_auth,
        )
        objecttypes_service = Service.objects.create(
            slug="objecttypes-api",
            api_root="http://example.org/objecttypes-api/api/v2/",
            api_type=APITypes.orc,
            auth_type=AuthTypes.no_auth,
        )
        objects_api_group = ObjectsAPIGroupConfig.objects.create(
            name="Group 1",
            identifier="group-1",
            objects_service=objects_service,
            objecttypes_service=objecttypes_service,
        )
        form = Form.objects.create(name="test")
        FormRegistrationBackend.objects.create(
            form=form,
            key="objects_backend",
            name="objects backend",
            backend="objects_api",
            options={"objects_api_group": objects_api_group.pk, "version": 2},
        )

    def test_copy_data_api_setting_to_global_config(self):
        FormRegistrationBackend = self.apps.get_model(
            "forms", "FormRegistrationBackend"
        )
        registration_backend = FormRegistrationBackend.objects.get()

        self.assertEqual(
            registration_backend.options, {"objects_api_group": "group-1", "version": 2}
        )
