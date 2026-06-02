from django_test_migrations.contrib.unittest_case import MigratorTestCase

from openforms.registrations.contrib.objects_api.constants import (
    PLUGIN_IDENTIFIER as OBJECTS_API_PLUGIN_IDENTIFIER,
)

from ..constants import FormTypeChoices


class AddFormTypeFieldMigrationTests(MigratorTestCase):
    migrate_from = (
        "forms",
        "0125_alter_form_new_logic_evaluation_enabled",
    )
    migrate_to = (
        "forms",
        "0128_remove_form_is_appointment",
    )

    def prepare(self):
        apps = self.old_state.apps
        Form = apps.get_model("forms", "Form")

        # create an appointment and a regular form
        Form.objects.create(name="Appointment form", is_appointment=True)
        Form.objects.create(name="Regular form", is_appointment=False)

    def test_migration(self):
        Form = self.new_state.apps.get_model("forms", "Form")
        forms = Form.objects.all()

        self.assertEqual(forms.first().type, FormTypeChoices.appointment)
        self.assertEqual(forms.last().type, FormTypeChoices.regular)


class AddFormTypeFieldReverseMigrationTests(MigratorTestCase):
    migrate_from = (
        "forms",
        "0128_remove_form_is_appointment",
    )
    migrate_to = (
        "forms",
        "0125_alter_form_new_logic_evaluation_enabled",
    )

    def prepare(self):
        apps = self.old_state.apps
        Form = apps.get_model("forms", "Form")

        # create a form for all the possible types
        Form.objects.create(name="Appointment form", type=FormTypeChoices.appointment)
        Form.objects.create(name="Regular form", type=FormTypeChoices.regular)
        Form.objects.create(name="Single step form", type=FormTypeChoices.single_step)

    def test_migration(self):
        Form = self.new_state.apps.get_model("forms", "Form")
        forms = Form.objects.order_by("pk")

        self.assertTrue(forms[0].is_appointment)
        self.assertFalse(forms[1].is_appointment)
        self.assertFalse(forms[2].is_appointment)


class MoveObjectsAPIGroupConfigurationToBackendTests(MigratorTestCase):
    migrate_from = [
        ("objects_api", "0006_alter_objectsapigroupconfig_catalogue_domain"),
        ("forms", "0129_remove_form_new_renderer_enabled"),
    ]
    migrate_to = (
        "forms",
        "0131_move_api_group_configuration_to_backends",
    )

    def prepare(self):
        # uses real model, but that shouldn't matter

        apps = self.old_state.apps
        Service = apps.get_model("zgw_consumers", "Service")
        ObjectsAPIGroupConfig = apps.get_model("objects_api", "ObjectsAPIGroupConfig")
        Form = apps.get_model("forms", "Form")
        FormRegistrationBackend = apps.get_model("forms", "FormRegistrationBackend")

        # create API groups
        dummy_service = Service.objects.create(
            slug="dummy", api_type="orc", api_root="https://example.com/api/v1/"
        )
        group_1 = ObjectsAPIGroupConfig.objects.create(
            name="Ignore - no catalogue set up",
            identifier="group_1",
            objects_service=dummy_service,
            objecttypes_service=dummy_service,
            drc_service=dummy_service,
            catalogi_service=dummy_service,
            catalogue_domain="",
            catalogue_rsin="",
        )
        group_2 = ObjectsAPIGroupConfig.objects.create(
            name="Copy over",
            identifier="group_2",
            objects_service=dummy_service,
            objecttypes_service=dummy_service,
            drc_service=dummy_service,
            catalogi_service=dummy_service,
            catalogue_domain="ABCDE",
            catalogue_rsin="000111222",
            iot_submission_report="PDF",
            iot_submission_csv="",
            iot_attachment="",
        )

        form = Form.objects.create(name="Test")
        FormRegistrationBackend.objects.create(
            form=form,
            key="group-to-ignore",
            name="Should be ignored because of the group",
            backend=OBJECTS_API_PLUGIN_IDENTIFIER,
            # incomplete according to the types/serializer, but shouldn't break the
            # migration!
            options={
                "objects_api_group": group_1.identifier,
            },
        )
        FormRegistrationBackend.objects.create(
            form=form,
            key="group-to-update",
            name="Should be updated and gain all the defaults",
            backend=OBJECTS_API_PLUGIN_IDENTIFIER,
            # incomplete according to the types/serializer, but shouldn't break the
            # migration!
            options={
                "objects_api_group": group_2.identifier,
            },
        )
        FormRegistrationBackend.objects.create(
            form=form,
            key="has-local-config-already",
            name="May not be updated despite group qualifying",
            backend=OBJECTS_API_PLUGIN_IDENTIFIER,
            # incomplete according to the types/serializer, but shouldn't break the
            # migration!
            options={
                "objects_api_group": group_2.identifier,
                "catalogue": {
                    "domain": "notouch",
                    "rsin": "notouch",
                },
            },
        )

    def test_migration_processes_backends_correctly(self):
        FormRegistrationBackend = self.new_state.apps.get_model(
            "forms", "FormRegistrationBackend"
        )

        with self.subTest("group to ignore is unchanged"):
            backend_1 = FormRegistrationBackend.objects.get(key="group-to-ignore")

            self.assertEqual(backend_1.options, {"objects_api_group": "group_1"})

        with self.subTest("group to update has catalogue and document types"):
            backend_2 = FormRegistrationBackend.objects.get(key="group-to-update")

            self.assertEqual(
                backend_2.options,
                {
                    "objects_api_group": "group_2",
                    "catalogue": {
                        "domain": "ABCDE",
                        "rsin": "000111222",
                    },
                    "iot_submission_report": "PDF",
                    "iot_submission_csv": "",
                    "iot_attachment": "",
                },
            )

        with self.subTest("group with local config is not updated"):
            backend_3 = FormRegistrationBackend.objects.get(
                key="has-local-config-already"
            )

            self.assertEqual(
                backend_3.options,
                {
                    "objects_api_group": "group_2",
                    "catalogue": {
                        "domain": "notouch",
                        "rsin": "notouch",
                    },
                },
            )


class MoveZGWAPIGroupConfigurationToBackendTests(MigratorTestCase):
    migrate_from = [
        ("zgw_apis", "0003_alter_zgwapigroupconfig_use_generated_zaaknummer"),
        ("forms", "0129_remove_form_new_renderer_enabled"),
    ]
    migrate_to = (
        "forms",
        "0131_move_api_group_configuration_to_backends",
    )

    def prepare(self):
        # uses real model, but that shouldn't matter

        apps = self.old_state.apps
        Service = apps.get_model("zgw_consumers", "Service")
        ZGWApiGroupConfig = apps.get_model("zgw_apis", "ZGWApiGroupConfig")
        Form = apps.get_model("forms", "Form")
        FormRegistrationBackend = apps.get_model("forms", "FormRegistrationBackend")

        # create API groups
        dummy_service = Service.objects.create(
            slug="dummy", api_type="orc", api_root="https://example.com/api/v1/"
        )
        group_1 = ZGWApiGroupConfig.objects.create(
            name="Ignore - no catalogue set up",
            identifier="group_1",
            zrc_service=dummy_service,
            drc_service=dummy_service,
            ztc_service=dummy_service,
            catalogue_domain="",
            catalogue_rsin="",
        )
        group_2 = ZGWApiGroupConfig.objects.create(
            name="Copy over",
            identifier="group_2",
            zrc_service=dummy_service,
            drc_service=dummy_service,
            ztc_service=dummy_service,
            catalogue_domain="ABCDE",
            catalogue_rsin="000111222",
        )

        form = Form.objects.create(name="Test")
        FormRegistrationBackend.objects.create(
            form=form,
            key="group-to-ignore",
            name="Should be ignored because of the group",
            backend="zgw-create-zaak",
            # incomplete according to the types/serializer, but shouldn't break the
            # migration!
            options={
                "zgw_api_group": group_1.pk,
            },
        )
        FormRegistrationBackend.objects.create(
            form=form,
            key="group-to-update",
            name="Should be updated",
            backend="zgw-create-zaak",
            # incomplete according to the types/serializer, but shouldn't break the
            # migration!
            options={
                "zgw_api_group": group_2.pk,
            },
        )
        FormRegistrationBackend.objects.create(
            form=form,
            key="has-local-config-already",
            name="May not be updated despite group qualifying",
            backend="zgw-create-zaak",
            # incomplete according to the types/serializer, but shouldn't break the
            # migration!
            options={
                "zgw_api_group": group_2.pk,
                "catalogue": {
                    "domain": "notouch",
                    "rsin": "notouch",
                },
            },
        )

    def test_migration_processes_backends_correctly(self):
        FormRegistrationBackend = self.new_state.apps.get_model(
            "forms", "FormRegistrationBackend"
        )
        ZGWApiGroupConfig = self.new_state.apps.get_model(
            "zgw_apis", "ZGWApiGroupConfig"
        )
        group_1 = ZGWApiGroupConfig.objects.get(identifier="group_1")
        group_2 = ZGWApiGroupConfig.objects.get(identifier="group_2")

        with self.subTest("group to ignore is unchanged"):
            backend_1 = FormRegistrationBackend.objects.get(key="group-to-ignore")

            self.assertEqual(backend_1.options, {"zgw_api_group": group_1.pk})

        with self.subTest("group to update has catalogue"):
            backend_2 = FormRegistrationBackend.objects.get(key="group-to-update")

            self.assertEqual(
                backend_2.options,
                {
                    "zgw_api_group": group_2.pk,
                    "catalogue": {
                        "domain": "ABCDE",
                        "rsin": "000111222",
                    },
                },
            )

        with self.subTest("group with local config is not updated"):
            backend_3 = FormRegistrationBackend.objects.get(
                key="has-local-config-already"
            )

            self.assertEqual(
                backend_3.options,
                {
                    "zgw_api_group": group_2.pk,
                    "catalogue": {
                        "domain": "notouch",
                        "rsin": "notouch",
                    },
                },
            )
