from django.db.migrations.state import StateApps

from zgw_consumers.constants import APITypes, AuthTypes

from openforms.registrations.contrib.objects_api.plugin import (
    PLUGIN_IDENTIFIER as OBJECTS_API_PLUGIN_IDENTIFIER,
)
from openforms.utils.tests.test_migrations import TestMigrations


class SetRequiredObjectsAPIOptionsFields(TestMigrations):
    app = "registrations_objects_api"
    migrate_from = "0011_create_objecttypesypes_service_from_url"
    migrate_to = "0012_fill_required_fields"

    def setUpBeforeMigration(self, apps: StateApps):
        ObjectsAPIConfig = apps.get_model(
            "registrations_objects_api", "ObjectsAPIConfig"
        )
        ObjectsAPIConfig.objects.create(
            objecttype="https://objecttypen.nl/path/api/v1/objecttypes/2c66dabf-a967-4057-9969-0700320d23a2",
            objecttype_version=1,
        )

        Form = apps.get_model("forms", "Form")
        form = Form.objects.create(name="test form")

        FormRegistrationBackend = apps.get_model("forms", "FormRegistrationBackend")
        FormRegistrationBackend.objects.create(
            form=form,
            key="dummy",
            name="dummy",
            backend=OBJECTS_API_PLUGIN_IDENTIFIER,
            options={},
        )

    def test_migration_sets_required_fields(self):
        FormRegistrationBackend = self.apps.get_model(
            "forms", "FormRegistrationBackend"
        )

        form_registration_backend = FormRegistrationBackend.objects.first()

        self.assertEqual(
            form_registration_backend.options["objecttype"],
            "https://objecttypen.nl/path/api/v1/objecttypes/2c66dabf-a967-4057-9969-0700320d23a2",
        )
        self.assertEqual(form_registration_backend.options["objecttype_version"], 1)


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
            objects_api_config.objecttypes_service.label,
            "Objecttypes",
        )

        self.assertEqual(
            objects_api_config.objecttypes_service.auth_type,
            AuthTypes.api_key,
        )

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
            group.objecttype, "http://objecttypesapi.nl/api/v1/objecttypes/1"
        )
        self.assertEqual(group.objecttype_version, 1)
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
        self.assertEqual(group.productaanvraag_type, "testproduct")
        self.assertEqual(group.content_json, "{{ content_json }}")
        self.assertEqual(
            group.payment_status_update_json, "{{ payment_status_update_json }}"
        )


class ReconfigureSoloModelBackwardsMigrationTests(TestMigrations):
    app = "registrations_objects_api"
    migrate_from = "0017_move_singleton_data"
    migrate_to = "0016_objectsapigroupconfig"

    def setUpBeforeMigration(self, apps: StateApps):
        ObjectsAPIGroupConfig = apps.get_model(
            "registrations_objects_api", "ObjectsAPIGroupConfig"
        )
        ObjectsAPIConfig = apps.get_model(
            "registrations_objects_api", "ObjectsAPIConfig"
        )

        ObjectsAPIConfig.objects.create()
        self.objects_api_group_1 = ObjectsAPIGroupConfig.objects.create(
            name="ZGW API 1", organisatie_rsin="100000001"
        )
        self.objects_api_group_2 = ObjectsAPIGroupConfig.objects.create(
            name="ZGW API 2", organisatie_rsin="100000002"
        )
        self.assertTrue(self.objects_api_group_1.pk < self.objects_api_group_2.pk)

    def test_solo_reconfigured_correctly(self):
        ObjectsAPIConfig = self.apps.get_model(
            "registrations_objects_api", "ObjectsAPIConfig"
        )

        solo = ObjectsAPIConfig.objects.get()

        self.assertEqual(solo.organisatie_rsin, "100000001")


class BackwardsMigrationNoObjectsAPIGroupTests(TestMigrations):
    app = "registrations_objects_api"
    migrate_from = "0017_move_singleton_data"
    migrate_to = "0016_objectsapigroupconfig"

    def setUpBeforeMigration(self, apps: StateApps):
        ObjectsAPIConfig = apps.get_model(
            "registrations_objects_api", "ObjectsAPIConfig"
        )

        ObjectsAPIConfig.objects.create()

    def test_solo_reconfigured_correctly(self):
        ObjectsAPIConfig = self.apps.get_model(
            "registrations_objects_api", "ObjectsAPIConfig"
        )

        solo = ObjectsAPIConfig.objects.get()

        self.assertIsNone(solo.objects_service)


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
