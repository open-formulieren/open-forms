from django.urls import reverse

from django_webtest import WebTest
from furl import furl
from rest_framework.serializers import Serializer

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.config.models import GlobalConfiguration
from openforms.registrations.registry import Registry
from openforms.registrations.tests.utils import patch_registry
from openforms.tests.utils import disable_2fa

from ...registrations.base import BasePlugin
from ..models import Form
from .factories import FormFactory

model_field = Form._meta.get_field("registration_backend")

register = Registry()


class OptionsSerializer(Serializer):
    pass


@register("plugin")
class Plugin(BasePlugin):
    verbose_name = "A demo plugin"
    configuration_options = OptionsSerializer

    def register_submission(self, submission, options):
        pass

    def get_reference_from_result(self, result) -> str:
        return "foo"


@disable_2fa
class FormAdminTests(WebTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.superuser = SuperUserFactory.create()

    def test_form_list_view_filters_on_soft_delete(self):
        form_available = FormFactory.create(deleted_=False)
        form_deleted = FormFactory.create(deleted_=True)

        url = reverse("admin:forms_form_changelist")

        with self.subTest("default"):
            response = self.app.get(url, user=self.superuser, status=200)
            visible = list(response.context["cl"].result_list.all())
            self.assertEqual(visible, [form_available])

        with self.subTest("available"):
            f = furl(url)
            f.args["deleted"] = "available"
            response = self.app.get(f.url, user=self.superuser, status=200)

            visible = list(response.context["cl"].result_list.all())
            self.assertEqual(visible, [form_available])

        with self.subTest("deleted"):
            f = furl(url)
            f.args["deleted"] = "deleted"
            response = self.app.get(f.url, user=self.superuser, status=200)

            visible = list(response.context["cl"].result_list.all())
            self.assertEqual(visible, [form_deleted])

    def test_form_list_view_delete_action_soft_deletes(self):
        form_delete = FormFactory.create()
        form_keep = FormFactory.create()

        url = reverse("admin:forms_form_changelist")
        response = self.app.get(url, user=self.superuser, status=200)

        form = response.forms["changelist-form"]
        form["action"] = "delete_selected"
        form["_selected_action"] = [str(form_delete.pk)]

        response = form.submit(status=200)

        # deletion confirmation
        response.form.submit()

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
        response.form.submit()

        form.refresh_from_db()
        self.assertTrue(form._is_deleted)
