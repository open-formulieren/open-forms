import json
from io import BytesIO
from zipfile import ZipFile

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.translation import ugettext as _

from django_webtest import WebTest

from ..models import Form, FormStep
from .factories import FormFactory, FormStepFactory


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
        self.assertEqual(forms[0]["fields"]["uuid"], str(form.uuid))

        form_definitions = json.loads(zf.read("formDefinitions.json"))
        self.assertEqual(len(form_definitions), 0)

        form_steps = json.loads(zf.read("formSteps.json"))
        self.assertEqual(len(form_steps), 0)

    def test_form_admin_import_button(self):
        response = self.app.get(reverse("admin:forms_form_changelist"), user=self.user)

        import_button = response.html("a", {"class": "addlink"})[-1]
        self.assertEqual(import_button.attrs["href"], reverse("admin:forms_import"))

    def test_form_admin_import(self):
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
                                    "slug": "bed",
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


class FormAdminCopyTests(WebTest):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="john",
            password="secret",
            email="john@example.com",
            is_superuser=True,
            is_staff=True,
        )

    def test_form_admin_copy(self):
        form = FormFactory.create()
        form_step = FormStepFactory.create(form=form)
        response = self.app.get(
            reverse("admin:forms_form_change", args=(form.pk,)), user=self.user
        )

        self.assertEqual(response.status_code, 200)

        response = response.form.submit("_copy")

        copied_form = Form.objects.get(slug=f"{form.slug}-kopie")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.location,
            reverse("admin:forms_form_change", args=(copied_form.pk,)),
        )

        self.assertNotEqual(copied_form.uuid, form.uuid)
        self.assertEqual(copied_form.name, f"{form.name} (kopie)")

        copied_form_step = FormStep.objects.last()
        self.assertNotEqual(copied_form_step.uuid, form_step.uuid)
        self.assertEqual(copied_form_step.form, copied_form)

        copied_form_definition = copied_form_step.form_definition
        self.assertNotEqual(copied_form_definition.uuid, form_step.form_definition.uuid)
        self.assertEqual(
            copied_form_definition.name, f"{form_step.form_definition.name} (kopie)"
        )
        self.assertEqual(
            copied_form_definition.slug, f"{form_step.form_definition.slug}-kopie"
        )

    def test_form_admin_copy_error_duplicate(self):
        form = FormFactory.create()
        FormFactory.create(slug=f"{form.slug}-kopie")
        form_step = FormStepFactory.create(form=form)
        response = self.app.get(
            reverse("admin:forms_form_change", args=(form.pk,)), user=self.user
        )

        self.assertEqual(response.status_code, 200)

        response = response.form.submit("_copy")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.location, reverse("admin:forms_form_change", args=(form.pk,))
        )

        response = response.follow()

        error = response.html.find("li", {"class": "error"})
        self.assertIn(_("Error occurred while copying: duplicate key"), error.text)
