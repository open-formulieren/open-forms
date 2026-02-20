from django.urls import reverse_lazy

from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa

from openforms.accounts.tests.factories import UserFactory
from openforms.authentication.tests.factories import AttributeGroupFactory

from ..models import AttributeGroup


@disable_admin_mfa()
class AttributeGroupAdminTests(WebTest):
    admin_export_url = reverse_lazy("admin:yivi_oidc_attributegroup_export")
    admin_import_url = reverse_lazy("admin:yivi_oidc_attributegroup_import")

    def test_successful_export_attribute_groups(self):
        user = UserFactory.create(is_staff=True)

        # Create test data
        AttributeGroupFactory.create(
            name="group1",
            uuid="240d5fd5-07c6-4a7a-b5b5-27edc43af3cd",
            description="For retrieving group 1 data",
            attributes=["foo", "bar", "foo.bar"],
        )
        AttributeGroupFactory.create(
            name="group2",
            uuid="6af22687-08b3-4546-ad2e-22ed90c18a13",
            description="For retrieving group 2 data",
            attributes=["zoo", "zar"],
        )

        # Go to export page and export to json
        export_page = self.app.get(self.admin_export_url, user=user)
        export_form = export_page.forms[1]
        export_form["format"].select(text="json")
        export_response = export_form.submit()

        # Expect that the export was successful
        self.assertEqual(export_response.status_code, 200)
        self.assertEqual(export_response.content_type, "application/json")
        self.assertGreater(int(export_response["Content-Length"]), 0)

        # Expect that the export contains all attribute groups
        self.assertEqual(
            export_response.json,
            [
                {
                    "name": "group2",
                    "uuid": "6af22687-08b3-4546-ad2e-22ed90c18a13",
                    "description": "For retrieving group 2 data",
                    "attributes": "zoo,zar",
                },
                {
                    "name": "group1",
                    "uuid": "240d5fd5-07c6-4a7a-b5b5-27edc43af3cd",
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
        attributeGroup1 = AttributeGroupFactory.create(
            name="group1",
            uuid="240d5fd5-07c6-4a7a-b5b5-27edc43af3cd",
            description="For retrieving group 1 data",
            attributes=["foo", "bar", "foo.bar"],
        )
        attributeGroup2 = AttributeGroupFactory.create(
            name="group2",
            uuid="6af22687-08b3-4546-ad2e-22ed90c18a13",
            description="For retrieving group 2 data",
            attributes=["zoo", "zar"],
        )

        # Go to export page and export to json
        export_page = self.app.get(self.admin_export_url, user=user)
        export_form = export_page.forms[1]
        export_form["format"].select(text="json")
        export_response = export_form.submit()

        # Expect that the export was successful
        self.assertEqual(export_response.status_code, 200)

        # Remove local attributegroups. We will add them later via import
        attributeGroup1.delete()
        attributeGroup2.delete()
        self.assertEqual(len(AttributeGroup.objects.all()), 0)

        # Go to import page
        import_page = self.app.get(self.admin_import_url, user=user)
        import_form = import_page.forms[1]

        # Upload the data file, set the file type, and import
        import_form["import_file"] = (
            "export.json",
            export_response.body,
            "application/json",
        )
        import_form["format"].select(text="json")
        import_response = import_form.submit()

        # Assert successful import
        self.assertEqual(import_response.status_code, 200)

        # Confirm the import preview, and perform the actual import.
        confirm_form = import_response.forms[1]
        confirm_response = confirm_form.submit()
        self.assertEqual(confirm_response.status_code, 302)

        # Expect that 2 attribute groups are imported
        self.assertEqual(len(AttributeGroup.objects.all()), 2)

        # Expect that the imported attribute groups have the same content as the
        # exported attribute groups
        group1 = AttributeGroup.objects.get(uuid="240d5fd5-07c6-4a7a-b5b5-27edc43af3cd")
        self.assertEqual(group1.name, "group1")
        self.assertEqual(group1.description, "For retrieving group 1 data")
        self.assertEqual(group1.attributes, ["foo", "bar", "foo.bar"])

        group2 = AttributeGroup.objects.get(uuid="6af22687-08b3-4546-ad2e-22ed90c18a13")
        self.assertEqual(group2.name, "group2")
        self.assertEqual(group2.description, "For retrieving group 2 data")
        self.assertEqual(group2.attributes, ["zoo", "zar"])
