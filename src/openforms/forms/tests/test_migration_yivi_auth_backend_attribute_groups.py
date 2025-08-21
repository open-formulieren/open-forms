from openforms.utils.tests.test_migrations import TestMigrations


class YiviAuthBackendAttributeGroupMigrationTest(TestMigrations):
    migrate_from = "0112_data_migrate_objects_api_group"
    migrate_to = "0113_data_migrate_yivi_form_authentication_attribute_groups"
    app = "forms"

    def setUpBeforeMigration(self, apps):
        AttributeGroup = apps.get_model("yivi_oidc", "AttributeGroup")
        Form = apps.get_model("forms", "Form")
        FormAuthenticationBackend = apps.get_model("forms", "FormAuthenticationBackend")

        AttributeGroup.objects.create(
            name="Personal data",
            uuid="9865fdd4-c141-4692-9449-ba3838749595",
            description="Attributes for personal data",
            attributes=[
                "irma-demo.gemeente.personalData.firstnames",
                "irma-demo.gemeente.personalData.familyname",
            ],
        )
        AttributeGroup.objects.create(
            name="Date of birth data",
            uuid="9c31eddb-b659-4cf7-9cce-f4f5a028e676",
            description="Attributes for date of birth data",
            attributes=[
                "irma-demo.gemeente.personalData.dateofbirth",
            ],
        )
        form = Form.objects.create(name="test")
        FormAuthenticationBackend.objects.create(
            form=form,
            backend="yivi_oidc",
            options={
                "bsn_loa": "urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport",
                "kvk_loa": "urn:etoegang:core:assurance-class:loa3",
                "authentication_options": ["bsn"],
                "additional_attributes_groups": [
                    # Using the attributesGroup's names
                    "Personal data",
                    "Date of birth data",
                ],
            },
        )

    def test_migrate_forward(self):
        FormAuthenticationBackend = self.apps.get_model(
            "forms", "FormAuthenticationBackend"
        )
        authentication_backend = FormAuthenticationBackend.objects.get()

        self.assertEqual(
            authentication_backend.options,
            {
                "bsn_loa": "urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport",
                "kvk_loa": "urn:etoegang:core:assurance-class:loa3",
                "authentication_options": ["bsn"],
                "additional_attributes_groups": [
                    "9865fdd4-c141-4692-9449-ba3838749595",
                    "9c31eddb-b659-4cf7-9cce-f4f5a028e676",
                ],
            },
        )


class YiviAuthBackendAttributeGroupMigrationBackwardTest(TestMigrations):
    migrate_from = "0113_data_migrate_yivi_form_authentication_attribute_groups"
    migrate_to = "0112_data_migrate_objects_api_group"
    app = "forms"

    def setUpBeforeMigration(self, apps):
        AttributeGroup = apps.get_model("yivi_oidc", "AttributeGroup")
        Form = apps.get_model("forms", "Form")
        FormAuthenticationBackend = apps.get_model("forms", "FormAuthenticationBackend")

        AttributeGroup.objects.create(
            name="Personal data",
            uuid="9865fdd4-c141-4692-9449-ba3838749595",
            description="Attributes for personal data",
            attributes=[
                "irma-demo.gemeente.personalData.firstnames",
                "irma-demo.gemeente.personalData.familyname",
            ],
        )
        AttributeGroup.objects.create(
            name="Date of birth data",
            uuid="9c31eddb-b659-4cf7-9cce-f4f5a028e676",
            description="Attributes for date of birth data",
            attributes=[
                "irma-demo.gemeente.personalData.dateofbirth",
            ],
        )
        form = Form.objects.create(name="test")
        FormAuthenticationBackend.objects.create(
            form=form,
            backend="yivi_oidc",
            options={
                "bsn_loa": "urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport",
                "kvk_loa": "urn:etoegang:core:assurance-class:loa3",
                "authentication_options": ["bsn"],
                "additional_attributes_groups": [
                    # Using the attributesGroup's uuids
                    "9865fdd4-c141-4692-9449-ba3838749595",
                    "9c31eddb-b659-4cf7-9cce-f4f5a028e676",
                ],
            },
        )

    def test_migrate_backward(self):
        FormAuthenticationBackend = self.apps.get_model(
            "forms", "FormAuthenticationBackend"
        )
        authentication_backend = FormAuthenticationBackend.objects.get()

        self.assertEqual(
            authentication_backend.options,
            {
                "bsn_loa": "urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport",
                "kvk_loa": "urn:etoegang:core:assurance-class:loa3",
                "authentication_options": ["bsn"],
                "additional_attributes_groups": ["Personal data", "Date of birth data"],
            },
        )
