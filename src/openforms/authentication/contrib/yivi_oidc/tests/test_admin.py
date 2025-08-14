import json

from django.contrib.postgres.fields import ArrayField
from django.test import override_settings
from django.urls import reverse_lazy

from django_jsonform.models.fields import JSONField
from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa

from openforms.accounts.tests.factories import SuperUserFactory, UserFactory
from openforms.authentication.tests.factories import AttributeGroupFactory
from openforms.forms.tests.factories import FormFactory

from ..models import AttributeGroup, YiviOpenIDConnectConfig


def _set_arrayfields(form, config: YiviOpenIDConnectConfig) -> None:
    """
    Set the field values manually, normally this is done through JS in the admin.
    """
    fields = [
        f.name
        for f in config._meta.get_fields()
        if isinstance(f, (ArrayField | JSONField)) and f.name in form.fields
    ]
    for field in fields:
        form[field] = json.dumps(getattr(config, field))


# disable django solo cache to prevent test isolation breakage
@override_settings(SOLO_CACHE=None)
@disable_admin_mfa()
class YiviConfigAdminTests(WebTest):
    CHANGE_PAGE_URL = reverse_lazy("admin:yivi_oidc_yiviopenidconnectconfig_change")

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # minimal configuration to pass form validation & not do network IO
        cls.config = config = YiviOpenIDConnectConfig(
            enabled=True,
            oidc_rp_client_id="testclient",
            oidc_rp_client_secret="secret",
            oidc_op_authorization_endpoint="http://localhost/oidc/auth",
            oidc_op_token_endpoint="http://localhost/oidc/token",
            oidc_op_user_endpoint="http://localhost/oidc/userinfo",
            oidc_op_logout_endpoint="http://localhost/oidc/logout",
        )
        config.save()
        cls.user = SuperUserFactory.create()

    def test_can_disable_backend_if_unused_in_forms(self):
        FormFactory.create(authentication_backend="other-backend")
        change_page = self.app.get(self.CHANGE_PAGE_URL, user=self.user)

        form = change_page.forms["yiviopenidconnectconfig_form"]
        _set_arrayfields(form, self.config)

        # disable the backend
        form["enabled"] = False
        response = form.submit()

        self.assertEqual(response.status_code, 302)
        self.config.refresh_from_db()
        self.assertFalse(self.config.enabled)

    def test_cannot_disable_backend_if_used_in_any_form(self):
        FormFactory.create(authentication_backend="yivi_oidc")
        change_page = self.app.get(self.CHANGE_PAGE_URL, user=self.user)

        form = change_page.forms["yiviopenidconnectconfig_form"]
        _set_arrayfields(form, self.config)

        # disable the backend
        form["enabled"] = False
        response = form.submit()

        self.assertEqual(response.status_code, 200)  # there are validation errors
        self.config.refresh_from_db()
        self.assertTrue(self.config.enabled)

    def test_leave_enabled(self):
        FormFactory.create(authentication_backend="other-backend")
        change_page = self.app.get(self.CHANGE_PAGE_URL, user=self.user)

        form = change_page.forms["yiviopenidconnectconfig_form"]
        _set_arrayfields(form, self.config)

        # enable the backend
        form["enabled"] = True
        response = form.submit()

        self.assertEqual(response.status_code, 302)
        self.config.refresh_from_db()
        self.assertTrue(self.config.enabled)


@disable_admin_mfa()
class AttributeGroupAdminTests(WebTest):
    admin_export_url = reverse_lazy("admin:yivi_oidc_attributegroup_export")
    admin_import_url = reverse_lazy("admin:yivi_oidc_attributegroup_import")

    def _get_value_for_select_field(self, field, file_type):
        json_option = next((t for t in field.options if file_type in t), None)
        assert json_option is not None

        return json_option[0]

    def test_successful_export_attribute_groups(self):
        user = UserFactory.create(
            is_staff=True,
        )

        # Create test data
        AttributeGroupFactory(
            name="group1",
            slug="group-1",
            description="For retrieving group 1 data",
            attributes=["foo", "bar", "foo.bar"],
        )
        AttributeGroupFactory(
            name="group2",
            slug="group-2",
            description="For retrieving group 2 data",
            attributes=["zoo", "zar"],
        )

        # Go to export page
        export_page = self.app.get(self.admin_export_url, user=user)
        form = export_page.forms["export-attributegroups"]

        # Select json file format, and export
        form["file_format"] = self._get_value_for_select_field(
            form["file_format"], "json"
        )
        response = form.submit()

        # Expect that the export was successful
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "application/json")
        self.assertGreater(int(response["Content-Length"]), 0)

        # Expect that the export contains all attribute groups
        decoded_response = json.loads(response.body.decode())
        self.assertEqual(
            decoded_response,
            [
                {
                    "name": "group2",
                    "slug": "group-2",
                    "description": "For retrieving group 2 data",
                    "attributes": "zoo,zar",
                },
                {
                    "name": "group1",
                    "slug": "group-1",
                    "description": "For retrieving group 1 data",
                    "attributes": "foo,bar,foo.bar",
                },
            ],
        )

    def test_successful_import_attribute_groups(self):
        user = UserFactory.create(
            is_staff=True,
        )

        # Create test data
        attributeGroup1 = AttributeGroupFactory(
            name="group1",
            slug="group-1",
            description="For retrieving group 1 data",
            attributes=["foo", "bar", "foo.bar"],
        )
        attributeGroup2 = AttributeGroupFactory(
            name="group2",
            slug="group-2",
            description="For retrieving group 2 data",
            attributes=["zoo", "zar"],
        )
        self.assertEqual(len(AttributeGroup.objects.all()), 2)

        with self.subTest("Export attributegroups"):
            # Go to export page
            export_page = self.app.get(self.admin_export_url, user=user)
            export_form = export_page.forms["export-attributegroups"]

            # Select json file format, and export
            export_form["file_format"] = self._get_value_for_select_field(
                export_form["file_format"], "json"
            )
            export_response = export_form.submit()

            # Expect that the export was successful
            self.assertEqual(export_response.status_code, 200)

        with self.subTest("Remove local attributegroups"):
            # Remove local attributegroups, so we can add them via import
            attributeGroup1.delete()
            attributeGroup2.delete()
            self.assertEqual(len(AttributeGroup.objects.all()), 0)

        with self.subTest("Import attributegroups"):
            # Go to import page
            import_page = self.app.get(self.admin_import_url, user=user)
            import_form = import_page.forms[1]

            # Upload the data file, set the file type, and import
            import_form["import_file"] = (
                "testfile.json",
                export_response.body,
                "application/json",
            )
            import_form["input_format"] = self._get_value_for_select_field(
                import_form["input_format"], "json"
            )
            import_response = import_form.submit()
            self.assertEqual(import_response.status_code, 200)

        with self.subTest("Confirm import of attributegroups"):
            # After submitting the import form, we are send to a confirmation form.
            # This confirmation form includes a preview of the data being imported.
            import_preview = import_response.pyquery(".import-preview")
            self.assertEqual(len(import_preview), 1)

            # The `.import-preview` contains both attribute groups that we are importing.
            import_preview_rows = import_response.pyquery(".import-preview tr.new")
            self.assertEqual(len(import_preview_rows), 2)

            # Confirm the import preview, and perform the actual import.
            confirm_form = import_response.forms[1]
            confirm_response = confirm_form.submit()
            self.assertEqual(confirm_response.status_code, 302)

        with self.subTest("Check imported data"):
            # Expect that 2 attribute groups are imported
            self.assertEqual(len(AttributeGroup.objects.all()), 2)

            # Expect that the imported attribute groups have the same content as the
            # exported attribute groups
            group1 = AttributeGroup.objects.get(slug="group-1")
            self.assertEqual(group1.name, "group1")
            self.assertEqual(group1.description, "For retrieving group 1 data")
            self.assertEqual(group1.attributes, ["foo", "bar", "foo.bar"])

            group2 = AttributeGroup.objects.get(slug="group-2")
            self.assertEqual(group2.name, "group2")
            self.assertEqual(group2.description, "For retrieving group 2 data")
            self.assertEqual(group2.attributes, ["zoo", "zar"])

    def test_successful_update_attribute_group_using_import(self):
        user = UserFactory.create(
            is_staff=True,
        )

        # Create test data
        attributeGroup1 = AttributeGroupFactory(
            name="group1",
            slug="group-1",
            description="For retrieving group 1 data",
            attributes=["foo", "bar", "foo.bar"],
        )
        attributeGroup2 = AttributeGroupFactory(
            name="group2",
            slug="group-2",
            description="For retrieving group 2 data",
            attributes=["zoo", "zar"],
        )
        self.assertEqual(len(AttributeGroup.objects.all()), 2)

        with self.subTest("Export attributegroups"):
            # Go to export page
            export_page = self.app.get(self.admin_export_url, user=user)
            export_form = export_page.forms["export-attributegroups"]

            # Select json file format, and export
            export_form["file_format"] = self._get_value_for_select_field(
                export_form["file_format"], "json"
            )
            export_response = export_form.submit()

            # Expect that the export was successful
            self.assertEqual(export_response.status_code, 200)

        with self.subTest("Update attributegroup2"):
            # Update attributeGroup2. This change should be reverted when we later import
            # the attributegroups.
            attributeGroup2.attributes = ["replacing_the_old_attributes"]
            attributeGroup2.save()

            # Attribute group 2 is updated and saved
            self.assertEqual(
                AttributeGroup.objects.get(slug="group-2").attributes,
                ["replacing_the_old_attributes"],
            )

        with self.subTest("Import attributegroups"):
            # Go to import page
            import_page = self.app.get(self.admin_import_url, user=user)
            import_form = import_page.forms[1]

            # Upload the data file, set the file type, and import
            import_form["import_file"] = (
                "testfile.json",
                export_response.body,
                "application/json",
            )
            import_form["input_format"] = self._get_value_for_select_field(
                import_form["input_format"], "json"
            )
            import_response = import_form.submit()
            self.assertEqual(import_response.status_code, 200)

        with self.subTest("Confirm import of attributegroups"):
            import_preview_rows = import_response.pyquery(".import-preview tr.update")
            self.assertEqual(len(import_preview_rows), 2)

            # The preview shows which values will be updated
            self.assertIn(
                '<td><del style="background:#ffe6e6;">replacing_the_old_attributes</del>'
                '<ins style="background:#e6ffe6;">zoo,zar</ins></td>',
                import_preview_rows.html(),
            )

            # Confirm the import preview, and perform the actual import.
            confirm_form = import_response.forms[1]
            confirm_response = confirm_form.submit()
            self.assertEqual(confirm_response.status_code, 302)

        with self.subTest("Check imported data"):
            # Expect that we still have 2 attribute groups
            self.assertEqual(len(AttributeGroup.objects.all()), 2)

            # attributeGroup1 shouldn't be updated
            group1 = AttributeGroup.objects.get(slug="group-1")
            self.assertEqual(group1, attributeGroup1)

            # Only the attributes of attributeGroup2 should be updated
            group2 = AttributeGroup.objects.get(slug="group-2")
            self.assertEqual(group2.name, attributeGroup2.name)
            self.assertEqual(group2.description, attributeGroup2.description)
            self.assertEqual(group2.attributes, ["zoo", "zar"])
