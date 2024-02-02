from django.db.migrations.state import StateApps

from openforms.registrations.contrib.objects_api.plugin import (
    PLUGIN_IDENTIFIER as OBJECTS_API_PLUGIN_IDENTIFIER,
)
from openforms.utils.tests.test_migrations import TestMigrations


class ObjecttypesServiceFromDefaultUrlMigrationTests(TestMigrations):
    app = "registrations_objects_api"
    migrate_from = "0010_objectsapiconfig_objecttypes_service"
    migrate_to = "0011_create_objecttypesypes_service_from_url"

    def setUpBeforeMigration(self, apps: StateApps):
        ObjectsAPIConfig = apps.get_model(
            "registrations_objects_api", "ObjectsAPIConfig"
        )

        ObjectsAPIConfig.objects.create(
            objecttype="https://objecttypen.nl/path/api/v1/objecttypes/2c66dabf-a967-4057-9969-0700320d23a2",
        )

    def test_migration_sets_service_from_default_url(self):
        ObjectsAPIConfig = self.apps.get_model(
            "registrations_objects_api", "ObjectsAPIConfig"
        )

        objects_api_config = ObjectsAPIConfig.objects.get()

        self.assertEqual(
            objects_api_config.objecttypes_service.api_root,
            "https://objecttypen.nl/path/api/v1/",
        )

        self.assertEqual(
            objects_api_config.objecttypes_service.oas,
            "https://objecttypen.nl/path/api/v1/schema/openapi.yaml",
        )


class ObjecttypesServiceInvalidUrlMigrationTests(TestMigrations):
    app = "registrations_objects_api"
    migrate_from = "0010_objectsapiconfig_objecttypes_service"
    migrate_to = "0011_create_objecttypesypes_service_from_url"

    def setUpBeforeMigration(self, apps: StateApps):
        ObjectsAPIConfig = apps.get_model(
            "registrations_objects_api", "ObjectsAPIConfig"
        )

        ObjectsAPIConfig.objects.create(
            objecttype="https://objecttypen.nl/bad/url",
        )

    def test_migration_skips_invalid_url(self):
        ObjectsAPIConfig = self.apps.get_model(
            "registrations_objects_api", "ObjectsAPIConfig"
        )
        objects_api_config = ObjectsAPIConfig.objects.get()
        self.assertIsNone(objects_api_config.objecttypes_service)


class ObjecttypesServiceFromFormMigrationTests(TestMigrations):
    app = "registrations_objects_api"
    migrate_from = "0010_objectsapiconfig_objecttypes_service"
    migrate_to = "0011_create_objecttypesypes_service_from_url"

    def setUpBeforeMigration(self, apps: StateApps):

        ObjectsAPIConfig = apps.get_model(
            "registrations_objects_api", "ObjectsAPIConfig"
        )
        ObjectsAPIConfig.objects.create()

        FormRegistrationBackend = apps.get_model("forms", "FormRegistrationBackend")
        Form = apps.get_model("forms", "Form")

        form = Form.objects.create(name="test form")

        # This one shouldn't be used
        FormRegistrationBackend.objects.create(
            form=form,
            key="dummy",
            name="dummy",
            backend="unrelated",
            options={
                "objecttype": "https://example.com/api/v1/objecttypes/a62257f8-6357-4626-96b7-fd6025517ff7"
            },
        )

        FormRegistrationBackend.objects.create(
            form=form,
            key="dummy2",
            name="dummy2",
            backend=OBJECTS_API_PLUGIN_IDENTIFIER,
            options={
                "objecttype": "https://objecttypen.nl/api/v1/objecttypes/2c66dabf-a967-4057-9969-0700320d23a2"
            },
        )

    def test_migration_sets_service_from_form_registration_url(self):
        ObjectsAPIConfig = self.apps.get_model(
            "registrations_objects_api", "ObjectsAPIConfig"
        )
        objects_api_config = ObjectsAPIConfig.objects.get()

        self.assertEqual(
            objects_api_config.objecttypes_service.api_root,
            "https://objecttypen.nl/api/v1/",
        )

        self.assertEqual(
            objects_api_config.objecttypes_service.oas,
            "https://objecttypen.nl/api/v1/schema/openapi.yaml",
        )


class NoObjecttypesServiceMigrationTests(TestMigrations):
    app = "registrations_objects_api"
    migrate_from = "0010_objectsapiconfig_objecttypes_service"
    migrate_to = "0011_create_objecttypesypes_service_from_url"

    def test_migration_does_nothing_if_no_objects_api_config(self):
        ObjectsAPIConfig = self.apps.get_model(
            "registrations_objects_api", "ObjectsAPIConfig"
        )
        self.assertRaises(ObjectsAPIConfig.DoesNotExist, ObjectsAPIConfig.objects.get)
