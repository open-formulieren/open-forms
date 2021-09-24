from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse_lazy

from openforms.accounts.tests.factories import StaffUserFactory, UserFactory


class AuditLogListViewTests(TestCase):

    url = reverse_lazy("admin:audit-log")

    def test_non_staff_user(self):
        user = UserFactory.create()
        self.client.force_login(user=user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)  # redirect to login page

    def test_staff_user_insufficinet_perms(self):
        user = StaffUserFactory.create()
        self.client.force_login(user=user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_with_sufficient_permissions(self):
        user = StaffUserFactory.create()
        permission = Permission.objects.get(
            content_type__app_label="logging", codename="view_timelinelogproxy"
        )
        user.user_permissions.add(permission)
        self.client.force_login(user=user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
