from openforms.utils.tests.test_migrations import TestMigrations


class ConvertFromExtensionTests(TestMigrations):
    app = "registration_stuf_zds"
    migrate_from = None
    migrate_to = "0001_convert_extension_to_core_plugin"

    def setUpBeforeMigration(self, apps):
        Form = apps.get_model("forms", "Form")
        FormRegistrationBackend = apps.get_model("forms", "FormRegistrationBackend")

        form = Form.objects.create(name="test form")
        FormRegistrationBackend.objects.create(
            form=form,
            key="ignore-me",
            name="Ignore me",
            backend="other-backend",
        )
        FormRegistrationBackend.objects.create(
            form=form,
            key="from-extension",
            name="From extension",
            backend="stuf-zds-create-zaak:ext-utrecht",
        )

    def test_existing_backend_is_updated_stuf_zds_core(self):
        FormRegistrationBackend = self.apps.get_model(
            "forms", "FormRegistrationBackend"
        )

        first = FormRegistrationBackend.objects.get(key="ignore-me")
        self.assertEqual(first.backend, "other-backend")

        second = FormRegistrationBackend.objects.get(key="from-extension")
        self.assertEqual(second.backend, "stuf-zds-create-zaak")
