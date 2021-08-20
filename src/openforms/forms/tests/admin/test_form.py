import json
from io import BytesIO
from zipfile import ZipFile

from django.urls import reverse
from django.utils.translation import ugettext as _

from django_webtest import WebTest

from openforms.accounts.tests.factories import SuperUserFactory, UserFactory
from openforms.forms.models import Form, FormDefinition, FormStep
from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
)


class FormAdminImportExportTests(WebTest):
    def setUp(self):
        self.user = UserFactory.create(is_superuser=True, is_staff=True, app=self.app)

    def test_form_admin_export(self):
        form = FormFactory.create(authentication_backends=["demo"])
        response = self.app.get(
            reverse("admin:forms_form_change", args=(form.pk,)), user=self.user
        )

        self.assertEqual(response.status_code, 200)

        response = response.form.submit("_export")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "application/zip")

        zf = ZipFile(BytesIO(response.content))

        self.assertEqual(
            zf.namelist(),
            ["forms.json", "formSteps.json", "formDefinitions.json", "formLogic.json"],
        )

        forms = json.loads(zf.read("forms.json"))
        self.assertEqual(len(forms), 1)
        self.assertEqual(forms[0]["uuid"], str(form.uuid))
        self.assertEqual(forms[0]["authentication_backends"], ["demo"])

        form_definitions = json.loads(zf.read("formDefinitions.json"))
        self.assertEqual(len(form_definitions), 0)

        form_steps = json.loads(zf.read("formSteps.json"))
        self.assertEqual(len(form_steps), 0)

    def test_form_admin_import_button(self):
        response = self.app.get(reverse("admin:forms_form_changelist"), user=self.user)

        response = response.click(_("Import form"))

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
                                "authentication_backends": ["demo"],
                            }
                        ]
                    ).encode("utf-8")
                )

            with zf.open("formSteps.json", "w") as f:
                f.write(b"[]")

            with zf.open("formDefinitions.json", "w") as f:
                f.write(b"[]")

            with zf.open("formLogic.json", "w") as f:
                f.write(b"[]")

        response = self.app.get(reverse("admin:forms_import"), user=self.user)

        file.seek(0)

        html_form = response.form
        html_form["file"] = (
            "file.zip",
            file.read(),
        )

        response = html_form.submit("_import")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, reverse("admin:forms_form_changelist"))

        self.assertEqual(Form.objects.count(), 1)

        form = Form.objects.get()
        self.assertNotEqual(form.uuid, "b8315e1d-3134-476f-8786-7661d8237c51")
        self.assertEqual(form.name, "Form 000")
        self.assertEqual(form.authentication_backends, ["demo"])

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

        html_form = response.form
        html_form["file"] = (
            "file.zip",
            file.read(),
        )

        response = html_form.submit("_import")

        self.assertEqual(response.status_code, 200)

        error_message = response.html.find("li", {"class": "error"})
        self.assertTrue(
            error_message.text.startswith(
                _("Something went wrong while importing form: {}").format("")
            )
        )

    def test_form_admin_import_warning_created_form_definitions(self):
        form = FormFactory.create(slug="test")
        form_definition = FormDefinitionFactory.create(slug="testform")

        file = BytesIO()
        with ZipFile(file, mode="w") as zf:
            with zf.open("forms.json", "w") as f:
                f.write(
                    json.dumps(
                        [
                            {
                                "uuid": "2a231070-89c9-45dc-9ff8-ffd80ef15343",
                                "name": "testform",
                                "login_required": False,
                                "product": None,
                                "slug": "testform_old",
                                "url": "http://testserver/api/v1/forms/2a231070-89c9-45dc-9ff8-ffd80ef15343",
                                "steps": [
                                    {
                                        "uuid": "a44c90c5-d0ba-4783-8201-0094a0e44885",
                                        "form_definition": "testform",
                                        "index": 0,
                                        "url": "http://testserver/api/v1/forms/2a231070-89c9-45dc-9ff8-ffd80ef15343/steps/a44c90c5-d0ba-4783-8201-0094a0e44885",
                                    }
                                ],
                            }
                        ]
                    ).encode("utf-8")
                )

            with zf.open("formDefinitions.json", "w") as f:
                f.write(
                    json.dumps(
                        [
                            {
                                "url": "http://testserver/api/v1/form-definitions/78a18366-f9c0-47f2-8fd6-a6c31920440e",
                                "uuid": "78a18366-f9c0-47f2-8fd6-a6c31920440e",
                                "name": "testform",
                                "slug": "testform",
                                "configuration": {
                                    "components": [
                                        {
                                            "id": "eer6qln",
                                            "key": "email",
                                        }
                                    ]
                                },
                            }
                        ]
                    ).encode("utf-8")
                )

            with zf.open("formSteps.json", "w") as f:
                f.write(
                    json.dumps(
                        [
                            {
                                "index": 0,
                                "configuration": {
                                    "components": [
                                        {
                                            "id": "eer6qln",
                                            "key": "email",
                                        }
                                    ]
                                },
                                "form_definition": "http://testserver/api/v1/form-definitions/78a18366-f9c0-47f2-8fd6-a6c31920440e",
                            }
                        ]
                    ).encode("utf-8")
                )

            with zf.open("formLogic.json", "w") as f:
                f.write(b"[]")

        response = self.app.get(reverse("admin:forms_import"), user=self.user)

        file.seek(0)

        html_form = response.form
        html_form["file"] = (
            "file.zip",
            file.read(),
        )

        response = html_form.submit("_import")

        self.assertEqual(response.status_code, 302)

        response = response.follow()

        warning_message = response.html.find("li", {"class": "warning"})
        self.assertEqual(
            warning_message.text,
            _("Form definitions were created with the following slugs: {}").format(
                "['testform-2']"
            ),
        )

        success_message = response.html.find("li", {"class": "success"})
        self.assertEqual(success_message.text, _("Form successfully imported"))

        self.assertEqual(Form.objects.count(), 2)

        form = Form.objects.last()
        self.assertNotEqual(form.uuid, "b8315e1d-3134-476f-8786-7661d8237c51")
        self.assertEqual(form.name, "testform")

        self.assertEqual(FormDefinition.objects.count(), 2)

        form_definition = FormDefinition.objects.last()
        self.assertNotEqual(
            form_definition.uuid, "b8315e1d-3134-476f-8786-7661d8237c51"
        )
        self.assertEqual(form_definition.name, "testform")
        self.assertEqual(form_definition.slug, "testform-2")


class FormAdminCopyTests(WebTest):
    def setUp(self):
        self.user = UserFactory.create(is_superuser=True, is_staff=True, app=self.app)

    def test_form_admin_copy(self):
        form = FormFactory.create(authentication_backends=["demo"])
        form_step = FormStepFactory.create(form=form)
        response = self.app.get(
            reverse("admin:forms_form_change", args=(form.pk,)), user=self.user
        )

        self.assertEqual(response.status_code, 200)

        response = response.form.submit("_copy")

        copied_form = Form.objects.get(slug=_("{slug}-copy").format(slug=form.slug))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.location,
            reverse("admin:forms_form_change", args=(copied_form.pk,)),
        )

        self.assertNotEqual(copied_form.uuid, form.uuid)
        self.assertEqual(copied_form.name, _("{name} (copy)").format(name=form.name))
        self.assertEqual(copied_form.authentication_backends, ["demo"])

        copied_form_step = FormStep.objects.last()
        self.assertNotEqual(copied_form_step.uuid, form_step.uuid)
        self.assertEqual(copied_form_step.form, copied_form)

        copied_form_step_form_definition = copied_form_step.form_definition
        self.assertEqual(copied_form_step_form_definition, form_step.form_definition)


class FormAdminActionsTests(WebTest):
    def setUp(self) -> None:
        self.form = FormFactory.create()
        self.user = SuperUserFactory.create(app=self.app)

    def test_make_copies_action_makes_copy_of_a_form(self):
        response = self.app.get(reverse("admin:forms_form_changelist"), user=self.user)

        html_form = response.forms["changelist-form"]
        html_form["action"] = "make_copies"
        html_form["_selected_action"] = [str(form.pk) for form in Form.objects.all()]
        html_form.submit()

        self.assertEqual(Form.objects.count(), 2)
        copied_form = Form.objects.exclude(pk=self.form.pk).first()
        self.assertEqual(
            copied_form.name, _("{name} (copy)").format(name=self.form.name)
        )
        self.assertEqual(copied_form.slug, _("{slug}-copy").format(slug=self.form.slug))

    def test_set_to_maintenance_mode_sets_form_maintenance_mode_field_to_True(self):
        response = self.app.get(reverse("admin:forms_form_changelist"), user=self.user)

        html_form = response.forms["changelist-form"]
        html_form["action"] = "set_to_maintenance_mode"
        html_form["_selected_action"] = [self.form.pk]
        html_form.submit()

        self.form.refresh_from_db()
        self.assertTrue(self.form.maintenance_mode)

    def test_remove_from_maintenance_mode_sets_form_maintenance_mode_field_to_False(
        self,
    ):
        self.form.maintenance_mode = True
        self.form.save()

        response = self.app.get(reverse("admin:forms_form_changelist"), user=self.user)

        html_form = response.forms["changelist-form"]
        html_form["action"] = "remove_from_maintenance_mode"
        html_form["_selected_action"] = [self.form.pk]
        html_form.submit()

        self.form.refresh_from_db()
        self.assertFalse(self.form.maintenance_mode)
