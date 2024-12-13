from django.test import override_settings
from django.urls import reverse

from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa
from rest_framework.serializers import Serializer

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.registrations.registry import Registry

from ...registrations.base import BasePlugin
from ..models import Form
from .admin.mixins import FormListAjaxMixin
from .factories import FormFactory

register = Registry()


class OptionsSerializer(Serializer):
    pass


@register("plugin")
class Plugin(BasePlugin):
    verbose_name = "A demo plugin"
    configuration_options = OptionsSerializer

    def register_submission(self, submission, options):
        pass


@disable_admin_mfa()
class FormAdminTests(FormListAjaxMixin, WebTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.superuser = SuperUserFactory.create()

    def test_form_list_view_filters_on_soft_delete(self):
        form_available = FormFactory.create(deleted_=False)
        form_deleted = FormFactory.create(deleted_=True)

        with self.subTest("default"):
            response = self._get_form_changelist(user=self.superuser, status=200)
            visible = list(response.context["cl"].result_list.all())
            self.assertEqual(visible, [form_available])

        with self.subTest("available"):
            response = self._get_form_changelist(
                query={"deleted": "available"}, user=self.superuser, status=200
            )

            visible = list(response.context["cl"].result_list.all())
            self.assertEqual(visible, [form_available])

        with self.subTest("deleted"):
            response = self._get_form_changelist(
                query={"deleted": "deleted"}, user=self.superuser, status=200
            )

            visible = list(response.context["cl"].result_list.all())
            self.assertEqual(visible, [form_deleted])

    def test_form_list_view_delete_action_soft_deletes(self):
        form_delete = FormFactory.create()
        form_keep = FormFactory.create()

        response = self._get_form_changelist(user=self.superuser, status=200)

        form = response.forms["changelist-form"]
        form["action"] = "delete_selected"
        form["_selected_action"] = [str(form_delete.pk)]

        response = form.submit(status=200)

        # deletion confirmation
        delete_confirmation_form = response.forms[1]
        delete_confirmation_form.submit()

        form_delete.refresh_from_db()
        form_keep.refresh_from_db()

        self.assertTrue(form_delete._is_deleted)
        self.assertFalse(form_keep._is_deleted)

    def test_form_change_view_allows_access_to_soft_deleted(self):
        form = FormFactory.create(deleted_=True)

        url = reverse("admin:forms_form_change", kwargs={"object_id": form.id})
        response = self.app.get(url, user=self.superuser)
        self.assertEqual(response.status_code, 200)

    def test_form_change_view_delete_action_soft_deletes(self):
        form = FormFactory.create()

        url = reverse("admin:forms_form_delete", kwargs={"object_id": form.id})
        response = self.app.get(url, user=self.superuser)

        # deletion confirmation
        delete_confirmation_form = response.forms[1]
        delete_confirmation_form.submit()

        form.refresh_from_db()
        self.assertTrue(form._is_deleted)

    @override_settings(LANGUAGE_CODE="en")
    def test_copy_saves_translated_name_for_all_the_languages(self):
        form = FormFactory.create(
            name="A name for the form",
            name_nl="A Dutch name for the form",
            name_en="A name for the form",
        )
        form.copy()

        form_copy = Form.objects.order_by("pk").last()

        self.assertEqual(form_copy.name, "A name for the form (copy)")
        self.assertEqual(form_copy.name_en, "A name for the form (copy)")
        self.assertEqual(form_copy.name_nl, "A Dutch name for the form (kopie)")
