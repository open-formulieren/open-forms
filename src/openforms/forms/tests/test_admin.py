import json
from io import BytesIO
from zipfile import ZipFile

from django.contrib.auth import get_user_model
from django.urls import reverse

from django_webtest import WebTest

from ..models import Form
from .factories import FormFactory


class FormAdminImportExportTests(WebTest):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="john",
            password="secret",
            email="john@example.com",
            is_superuser=True,
            is_staff=True,
        )

    def test_form_admin_export(self):
        form = FormFactory.create()
        response = self.app.get(
            reverse("admin:forms_form_change", args=(form.pk,)), user=self.user
        )

        self.assertEqual(response.status_code, 200)

        response = response.form.submit("_export")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "application/zip")

        zf = ZipFile(BytesIO(response.content))

        self.assertEqual(
            zf.namelist(), ["forms.json", "formSteps.json", "formDefinitions.json"]
        )

        forms = json.loads(zf.read("forms.json"))
        self.assertEqual(len(forms), 1)
        self.assertEqual(forms[0]["uuid"], str(form.uuid))

        form_definitions = json.loads(zf.read("formDefinitions.json"))
        self.assertEqual(len(form_definitions), 0)

        form_steps = json.loads(zf.read("formSteps.json"))
        self.assertEqual(len(form_steps), 0)

    def test_form_admin_import_button(self):
        response = self.app.get(reverse("admin:forms_form_changelist"), user=self.user)

        response = response.click("Import")

        self.assertEqual(response.status_code, 200)

        # Page should have the import form
        self.assertIn("file", response.form.fields)

    def test_form_admin_import(self):
        file = BytesIO()
        with ZipFile(file, mode="w") as zf:
            with zf.open("forms.json", "w") as f:
                f.write(
                    json.dumps(
                        [
                            {
                                "uuid": "b8315e1d-3134-476f-8786-7661d8237c51",
                                "name": "Form 000",
                                "slug": "bed",
                                "product": None,
                                "loginRequired": False,
                            }
                        ]
                    ).encode("utf-8")
                )

            with zf.open("formSteps.json", "w") as f:
                f.write(b"[]")

            with zf.open("formDefinitions.json", "w") as f:
                f.write(b"[]")

        response = self.app.get(reverse("admin:forms_import"), user=self.user)

        file.seek(0)

        form = response.form
        form["file"] = (
            "file.zip",
            file.read(),
        )

        response = form.submit("_import")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, reverse("admin:forms_form_changelist"))

        self.assertEqual(Form.objects.count(), 1)

        form = Form.objects.get()
        self.assertNotEqual(form.uuid, "b8315e1d-3134-476f-8786-7661d8237c51")
        self.assertEqual(form.name, "Form 000")

    def test_form_admin_import_staff_required(self):
        self.user.is_superuser = False
        self.user.save()

        response = self.app.get(
            reverse("admin:forms_import"), user=self.user, status=403
        )

        self.assertEqual(response.status_code, 403)

    def test_form_admin_import_error(self):
        form = FormFactory.create(slug="test")

        file = BytesIO()
        with ZipFile(file, mode="w") as zf:
            with zf.open("forms.json", "w") as f:
                f.write(
                    json.dumps(
                        [
                            {
                                "model": "forms.form",
                                "pk": 1,
                                "fields": {
                                    "uuid": "b8315e1d-3134-476f-8786-7661d8237c51",
                                    "name": "Form 000",
                                    "slug": "test",
                                    "active": True,
                                    "product": None,
                                    "backend": "",
                                },
                            }
                        ]
                    ).encode("utf-8")
                )

            with zf.open("formSteps.json", "w") as f:
                f.write(b"[]")

            with zf.open("formDefinitions.json", "w") as f:
                f.write(b"[]")

        response = self.app.get(reverse("admin:forms_import"), user=self.user)

        file.seek(0)

        form = response.form
        form["file"] = (
            "file.zip",
            file.read(),
        )

        response = form.submit("_import")

        self.assertEqual(response.status_code, 200)

        error_message = response.html.find("li", {"class": "error"})
        self.assertIn("Something went wrong while importing", error_message.text)
