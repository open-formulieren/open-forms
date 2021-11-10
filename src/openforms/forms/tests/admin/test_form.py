import json
from io import BytesIO
from unittest.mock import patch
from zipfile import ZipFile

from django.test import TestCase
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
from openforms.tests.utils import disable_2fa
from openforms.utils.admin import SubmitActions


@disable_2fa
class FormAdminImportExportTests(WebTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory.create(is_superuser=True, is_staff=True)

    def test_form_admin_export(self):
        self.client.force_login(self.user)
        form = FormFactory.create(authentication_backends=["digid"])
        admin_url = reverse("admin:forms_form_change", args=(form.pk,))

        response = self.client.post(admin_url, data={"_export": "Export"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["content-type"], "application/zip")

        zf = ZipFile(BytesIO(response.content))

        self.assertEqual(
            zf.namelist(),
            ["forms.json", "formSteps.json", "formDefinitions.json", "formLogic.json"],
        )

        forms = json.loads(zf.read("forms.json"))
        self.assertEqual(len(forms), 1)
        self.assertEqual(forms[0]["uuid"], str(form.uuid))
        self.assertEqual(forms[0]["authentication_backends"], ["digid"])

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
                                "internal_name": "Form internal",
                                "slug": "bed",
                                "product": None,
                                "authentication_backends": ["digid"],
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
        self.assertEqual(form.internal_name, "Form internal")
        self.assertEqual(form.authentication_backends, ["digid"])

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
                                "internal_name": "test internal",
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
        self.assertEqual(form_definition.internal_name, "test internal")
        self.assertEqual(form_definition.slug, "testform-2")


@disable_2fa
class FormAdminCopyTests(TestCase):
    def test_form_admin_copy(self):
        user = UserFactory.create(is_superuser=True, is_staff=True)
        self.client.force_login(user)
        form = FormFactory.create(
            authentication_backends=["digid"], internal_name="internal"
        )
        form_step = FormStepFactory.create(form=form)
        admin_url = reverse("admin:forms_form_change", args=(form.pk,))

        # React UI renders this input, so simulate it in a raw POST call
        response = self.client.post(admin_url, data={"_copy": "Copy"})

        copied_form = Form.objects.get(slug=_("{slug}-copy").format(slug=form.slug))
        new_admin_url = reverse("admin:forms_form_change", args=(copied_form.pk,))
        self.assertRedirects(response, new_admin_url, fetch_redirect_response=False)

        self.assertNotEqual(copied_form.uuid, form.uuid)
        self.assertEqual(copied_form.name, _("{name} (copy)").format(name=form.name))
        self.assertEqual(
            copied_form.internal_name,
            _("{name} (copy)").format(name=form.internal_name),
        )
        self.assertEqual(copied_form.authentication_backends, ["digid"])

        copied_form_step = FormStep.objects.last()
        self.assertNotEqual(copied_form_step.uuid, form_step.uuid)
        self.assertEqual(copied_form_step.form, copied_form)

        copied_form_step_form_definition = copied_form_step.form_definition
        self.assertEqual(copied_form_step_form_definition, form_step.form_definition)


@disable_2fa
class FormAdminActionsTests(WebTest):
    def setUp(self) -> None:
        self.form = FormFactory.create(internal_name="foo")
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


from django.test import tag


@tag("these")
@disable_2fa
class FormEditTests(WebTest):
    """
    Test admin behaviour when creating or editing forms via the React UI.

    These tests make the API calls that the React UI would make and assert that the
    expected side effects occur.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.admin_user = SuperUserFactory.create(is_staff=True)
        cls.form = FormFactory.create()
        cls.message_endpoint = reverse(
            "api:form-admin-message", kwargs={"uuid_or_slug": cls.form.uuid}
        )

    def setUp(self):
        super().setUp()

        patcher = patch(
            "rest_framework.authentication.SessionAuthentication.enforce_csrf",
            return_value=None,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_form_created_success_message(self):
        """
        Assert that a success message is displayed when a new form is created.
        """
        create_page = self.app.get(
            reverse("admin:forms_form_add"), user=self.admin_user
        )
        container_node = create_page.pyquery(".react-form-create")

        self.assertTrue(container_node)

        # finalize "transaction" as the UI does
        response = self.app.post_json(
            self.message_endpoint,
            {
                "submitAction": SubmitActions.save,
                "isCreate": True,
            },
        )

        self.assertEqual(response.status_code, 201)

        # fetch the list page again, after submit/create the frontend redirects to the list
        # page
        list_page = self.app.get(response.json["redirectUrl"])

        messagelist = list_page.pyquery(".messagelist")
        success_message = messagelist.find(".success").text()

        self.assertEqual(
            success_message,
            _('The {name} "{obj}" was added successfully.').format(
                name=_("form"),
                obj=self.form.name,
            ),
        )

    def test_form_created_edit_again_success_message(self):
        """
        Assert that a success message is displayed when a new form is created.
        """
        create_page = self.app.get(
            reverse("admin:forms_form_add"), user=self.admin_user
        )
        container_node = create_page.pyquery(".react-form-create")

        self.assertTrue(container_node)

        # finalize "transaction" as the UI does
        response = self.app.post_json(
            self.message_endpoint,
            {
                "submitAction": SubmitActions.edit_again,
                "isCreate": True,
            },
        )

        self.assertEqual(response.status_code, 201)

        # fetch the list page again, after submit/create the frontend redirects to the list
        # page
        list_page = self.app.get(response.json["redirectUrl"])

        messagelist = list_page.pyquery(".messagelist")
        success_message = messagelist.find(".success").text()

        self.assertEqual(
            success_message,
            _('The {name} "{obj}" was added successfully.').format(
                name=_("form"),
                obj=self.form.name,
            )
            + " "
            + _("You may edit it again below."),
        )

    def test_form_created_add_another_success_message(self):
        """
        Assert that a success message is displayed when a new form is created.
        """
        create_page = self.app.get(
            reverse("admin:forms_form_add"), user=self.admin_user
        )
        container_node = create_page.pyquery(".react-form-create")

        self.assertTrue(container_node)

        # finalize "transaction" as the UI does
        response = self.app.post_json(
            self.message_endpoint,
            {
                "submitAction": SubmitActions.add_another,
                "isCreate": True,
            },
        )

        self.assertEqual(response.status_code, 201)

        # fetch the list page again, after submit/create the frontend redirects to the list
        # page
        list_page = self.app.get(response.json["redirectUrl"])

        messagelist = list_page.pyquery(".messagelist")
        success_message = messagelist.find(".success").text()

        self.assertEqual(
            success_message,
            _(
                'The {name} "{obj}" was added successfully. You may add another {name} below.'
            ).format(
                name=_("form"),
                obj=self.form.name,
            ),
        )

    def test_form_edited_success_message(self):
        change_page = self.app.get(
            reverse("admin:forms_form_change", args=(self.form.pk,)),
            user=self.admin_user,
        )
        container_node = change_page.pyquery(".react-form-create")

        self.assertTrue(container_node)

        # finalize "transaction" as the UI does
        response = self.app.post_json(
            self.message_endpoint,
            {
                "submitAction": SubmitActions.save,
                "isCreate": False,
            },
        )

        self.assertEqual(response.status_code, 201)

        # fetch the list page again, after submit/create the frontend redirects to the list
        # page
        list_page = self.app.get(response.json["redirectUrl"])

        messagelist = list_page.pyquery(".messagelist")
        success_message = messagelist.find(".success").text()

        self.assertEqual(
            success_message,
            _('The {name} "{obj}" was changed successfully.').format(
                name=_("form"),
                obj=self.form.name,
            ),
        )

    def test_form_edited_edit_again_success_message(self):
        change_page = self.app.get(
            reverse("admin:forms_form_change", args=(self.form.pk,)),
            user=self.admin_user,
        )
        container_node = change_page.pyquery(".react-form-create")

        self.assertTrue(container_node)

        # finalize "transaction" as the UI does
        response = self.app.post_json(
            self.message_endpoint,
            {
                "submitAction": SubmitActions.edit_again,
                "isCreate": False,
            },
        )

        self.assertEqual(response.status_code, 201)

        # fetch the list page again, after submit/create the frontend redirects to the list
        # page
        list_page = self.app.get(response.json["redirectUrl"])

        messagelist = list_page.pyquery(".messagelist")
        success_message = messagelist.find(".success").text()

        self.assertEqual(
            success_message,
            _(
                'The {name} "{obj}" was changed successfully. You may edit it again below.'
            ).format(
                name=_("form"),
                obj=self.form.name,
            ),
        )

    def test_form_edited_add_another_success_message(self):
        """
        Assert that a success message is displayed when a new form is created.
        """
        create_page = self.app.get(
            reverse("admin:forms_form_add"), user=self.admin_user
        )
        container_node = create_page.pyquery(".react-form-create")

        self.assertTrue(container_node)

        # finalize "transaction" as the UI does
        response = self.app.post_json(
            self.message_endpoint,
            {
                "submitAction": SubmitActions.add_another,
                "isCreate": False,
            },
        )

        self.assertEqual(response.status_code, 201)

        # fetch the list page again, after submit/create the frontend redirects to the list
        # page
        list_page = self.app.get(response.json["redirectUrl"])

        messagelist = list_page.pyquery(".messagelist")
        success_message = messagelist.find(".success").text()

        self.assertEqual(
            success_message,
            _(
                'The {name} "{obj}" was changed successfully. You may add another {name} below.'
            ).format(
                name=_("form"),
                obj=self.form.name,
            ),
        )
