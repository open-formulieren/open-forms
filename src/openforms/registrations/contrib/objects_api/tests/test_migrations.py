from django.db.migrations.state import StateApps

from zgw_consumers.constants import APITypes

from openforms.utils.tests.test_migrations import TestMigrations


class MoveExistingObjectsAPIConfigMigrationTests(TestMigrations):
    app = "registrations_objects_api"
    migrate_from = "0016_objectsapigroupconfig"
    migrate_to = "0017_move_singleton_data"

    def setUpBeforeMigration(self, apps: StateApps):
        ObjectsAPIConfig = apps.get_model(
            "registrations_objects_api", "ObjectsAPIConfig"
        )
        Service = apps.get_model("zgw_consumers", "Service")

        objects_api = Service.objects.create(
            label="Objects API",
            api_root="http://objectsapi.nl/api/v1/",
            api_type=APITypes.orc,
        )
        objecttypes_api = Service.objects.create(
            label="Objecttypes API",
            api_root="http://objecttypesapi.nl/api/v1/",
            api_type=APITypes.orc,
        )
        documents_api = Service.objects.create(
            label="Documents API",
            api_root="http://documentsapi.nl/api/v1/",
            api_type=APITypes.drc,
        )
        catalogi_api = Service.objects.create(
            label="Catalogi API",
            api_root="http://catalogiapi.nl/api/v1/",
            api_type=APITypes.ztc,
        )

        ObjectsAPIConfig.objects.create(
            objects_service=objects_api,
            objecttypes_service=objecttypes_api,
            drc_service=documents_api,
            catalogi_service=catalogi_api,
            objecttype="http://objecttypesapi.nl/api/v1/objecttypes/1",
            objecttype_version=1,
            informatieobjecttype_attachment="https://catalogiapi.nl/api/v1/informatieobjecttypen/1",
            informatieobjecttype_submission_csv="https://catalogiapi.nl/api/v1/informatieobjecttypen/2",
            informatieobjecttype_submission_report="https://catalogiapi.nl/api/v1/informatieobjecttypen/3",
            organisatie_rsin="100000009",
            productaanvraag_type="testproduct",
            content_json="{{ content_json }}",
            payment_status_update_json="{{ payment_status_update_json }}",
        )

    def test_services_migrated_correctly(self):
        ObjectsAPIGroupConfig = self.apps.get_model(
            "registrations_objects_api", "ObjectsAPIGroupConfig"
        )

        migrated_services = ObjectsAPIGroupConfig.objects.all()

        self.assertEqual(1, migrated_services.count())

        group = migrated_services.get()

        self.assertEqual(group.objects_service.label, "Objects API")
        self.assertEqual(group.objecttypes_service.label, "Objecttypes API")
        self.assertEqual(group.drc_service.label, "Documents API")
        self.assertEqual(group.catalogi_service.label, "Catalogi API")
        self.assertEqual(
            group.informatieobjecttype_attachment,
            "https://catalogiapi.nl/api/v1/informatieobjecttypen/1",
        )
        self.assertEqual(
            group.informatieobjecttype_submission_csv,
            "https://catalogiapi.nl/api/v1/informatieobjecttypen/2",
        )
        self.assertEqual(
            group.informatieobjecttype_submission_report,
            "https://catalogiapi.nl/api/v1/informatieobjecttypen/3",
        )
        self.assertEqual(group.organisatie_rsin, "100000009")


class NoObjectsAPIConfigDoesntCreateObjectsAPIGroupMigrationTest(TestMigrations):
    app = "registrations_objects_api"
    migrate_from = "0016_objectsapigroupconfig"
    migrate_to = "0017_move_singleton_data"

    def setUpBeforeMigration(self, apps: StateApps):
        ObjectsAPIConfig = apps.get_model(
            "registrations_objects_api", "ObjectsAPIConfig"
        )

        self.assertFalse(ObjectsAPIConfig.objects.exists())

    def test_no_zgw_api_group_created(self):
        ObjectsAPIGroupConfig = self.apps.get_model(
            "registrations_objects_api", "ObjectsAPIGroupConfig"
        )

        self.assertFalse(ObjectsAPIGroupConfig.objects.exists())


class AddDefaultObjectsAPIGroupMigrationTests(TestMigrations):
    app = "registrations_objects_api"
    migrate_from = "0018_remove_objectsapiconfig_catalogi_service_and_more"
    migrate_to = "0019_add_default_objects_api_group"

    def setUpBeforeMigration(self, apps: StateApps) -> None:
        Form = apps.get_model("forms", "Form")
        FormRegistrationBackend = apps.get_model("forms", "FormRegistrationBackend")
        ObjectsAPIGroupConfig = apps.get_model(
            "registrations_objects_api", "ObjectsAPIGroupConfig"
        )

        form = Form.objects.create(name="test form")
        ObjectsAPIGroupConfig.objects.create(name="Objects API Group")

        FormRegistrationBackend.objects.create(
            form=form,
            name="Objects API backend",
            key="backend",
            backend="objects_api",
        )

    def test_sets_default_objects_api_group(self) -> None:
        FormRegistrationBackend = self.apps.get_model(
            "forms", "FormRegistrationBackend"
        )
        ObjectsAPIGroupConfig = self.apps.get_model(
            "registrations_objects_api", "ObjectsAPIGroupConfig"
        )

        backend = FormRegistrationBackend.objects.get()
        self.assertEqual(
            backend.options["objects_api_group"], ObjectsAPIGroupConfig.objects.get().pk
        )


class AddDefaultObjectsAPIGroupWithBrokenStateMigrationTests(TestMigrations):
    app = "registrations_objects_api"
    migrate_from = "0018_remove_objectsapiconfig_catalogi_service_and_more"
    migrate_to = "0019_add_default_objects_api_group"

    def setUpBeforeMigration(self, apps: StateApps) -> None:
        Form = apps.get_model("forms", "Form")
        FormRegistrationBackend = apps.get_model("forms", "FormRegistrationBackend")
        ObjectsAPIGroupConfig = apps.get_model(
            "registrations_objects_api", "ObjectsAPIGroupConfig"
        )

        form = Form.objects.create(name="test form")
        FormRegistrationBackend.objects.create(
            form=form,
            name="Objects API backend",
            key="backend",
            backend="objects_api",
        )
        assert not ObjectsAPIGroupConfig.objects.exists()

    def test_sets_default_objects_api_group(self) -> None:
        FormRegistrationBackend = self.apps.get_model(
            "forms", "FormRegistrationBackend"
        )
        ObjectsAPIGroupConfig = self.apps.get_model(
            "registrations_objects_api", "ObjectsAPIGroupConfig"
        )
        auto_created_config = ObjectsAPIGroupConfig.objects.get()

        backend = FormRegistrationBackend.objects.get()
        self.assertEqual(backend.options["objects_api_group"], auto_created_config.pk)


class ObjecttypeUrltoUuidMigrationTests(TestMigrations):
    app = "registrations_objects_api"
    migrate_from = "0019_add_default_objects_api_group"
    migrate_to = "0020_objecttype_url_to_uuid"

    def setUpBeforeMigration(self, apps: StateApps) -> None:
        Form = apps.get_model("forms", "Form")
        FormRegistrationBackend = apps.get_model("forms", "FormRegistrationBackend")

        form = Form.objects.create(name="test form")

        FormRegistrationBackend.objects.create(
            form=form,
            name="Objects API backend",
            key="backend",
            backend="objects_api",
            options={
                "objecttype": "http://objecttypen.nl/api/v1/objecttypes/8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
            },
        )

    def test_changes_objecttype_key_name(self) -> None:
        FormRegistrationBackend = self.apps.get_model(
            "forms", "FormRegistrationBackend"
        )

        backend = FormRegistrationBackend.objects.get()
        self.assertEqual(
            backend.options["objecttype"],
            "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
        )
