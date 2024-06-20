from django.urls import reverse

from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa

from openforms.accounts.tests.factories import UserFactory

from ..models import ObjectsAPIGroupConfig


@disable_admin_mfa()
class ObjectsAPIGroupConfigAdminTest(WebTest):
    def test_name(self):
        ObjectsAPIGroupConfig.objects.create(name="test group")
        user = UserFactory.create(is_superuser=True, is_staff=True)

        response = self.app.get(
            reverse("admin:registrations_objects_api_objectsapigroupconfig_changelist"),
            user=user,
        )

        table = response.html.find("table", {"id": "result_list"})
        row = table.find("tbody").find("tr")

        self.assertEqual(row.find("th").string, "test group")
