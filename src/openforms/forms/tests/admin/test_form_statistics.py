from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _

from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa

from openforms.accounts.tests.factories import UserFactory


@disable_admin_mfa()
class FormStatisticsExportAdminTests(WebTest):

    admin_url = reverse_lazy("admin:formstatistics_export")

    def test_access_control_no_access(self):
        # various flavours of users do not have access, only if the right permissions
        # are set are you allowed in
        invalid_users = (
            (
                "plain user",
                UserFactory.create(),
                302,
            ),
            (
                "staff user without perms",
                UserFactory.create(is_staff=True),
                403,
            ),
            (
                "user with perms no staff",
                UserFactory.create(
                    is_staff=False, user_permissions=["forms.view_formstatistics"]
                ),
                302,
            ),
        )

        for label, user, expected_status in invalid_users:
            with self.subTest(label, expected_status=expected_status):
                response = self.app.get(
                    self.admin_url,
                    user=user,
                    auto_follow=False,
                    status=expected_status,
                )

                self.assertEqual(response.status_code, expected_status)

    def test_navigate_from_changelist(self):
        user = UserFactory.create(
            is_staff=True, user_permissions=["forms.view_formstatistics"]
        )
        changelist = self.app.get(
            reverse("admin:forms_formstatistics_changelist"), user=user
        )

        export_page = changelist.click(_("Export submission statistics"))

        self.assertEqual(export_page.request.path, self.admin_url)
