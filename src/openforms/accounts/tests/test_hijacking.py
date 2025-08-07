"""
Assert that the hijack funtionality works even with 2FA.
"""

from django.contrib.auth import SESSION_KEY
from django.test import TestCase, override_settings, tag
from django.urls import NoReverseMatch, reverse

from django_webtest import WebTest
from maykin_2fa.test import get_valid_totp_token

from openforms.logging.models import TimelineLogProxy

from .factories import StaffUserFactory, SuperUserFactory


@override_settings(
    USE_OIDC_FOR_ADMIN_LOGIN=False,
    MAYKIN_2FA_ALLOW_MFA_BYPASS_BACKENDS=[],  # enforce MFA
)
class HijackTests(WebTest):
    csrf_checks = False

    def _hijack_user(self, hijacked):
        url = reverse("hijack:acquire")
        response = self.app.post(
            url, {"user_pk": hijacked.pk, "next": reverse("admin:index")}
        )
        return response

    def _login_with_mfa(self, user):
        login_page = self.app.get(reverse("admin:login"), auto_follow=True)
        login_page.form["auth-username"] = user.username
        login_page.form["auth-password"] = "secret"
        token_page = login_page.form.submit()

        token_page.form["token-otp_token"] = get_valid_totp_token(user)
        token_page.form.submit().follow()

    def test_can_hijack_and_release_with_2fa(self):
        staff_user = StaffUserFactory.create(with_totp_device=True)
        superuser = SuperUserFactory.create(with_totp_device=True)
        admin_dashboard_url = reverse("admin:index")
        self._login_with_mfa(superuser)

        with self.subTest("superuser admin index page"):
            admin_dashboard = self.app.get(admin_dashboard_url, user=superuser)

            self.assertEqual(admin_dashboard.status_code, 200)
            user_tools = admin_dashboard.pyquery("#user-tools").text()
            self.assertIn(superuser.username, user_tools)

        with self.subTest("superuser hijacks other user"):
            user_list = self.app.get(
                reverse("admin:accounts_user_changelist"), user=superuser
            )

            self.assertEqual(user_list.status_code, 200)

            hijack_buttons = user_list.pyquery(".field-hijack_field button")
            self.assertEqual(len(hijack_buttons), 2)  # one for each user
            # webtest button clicks are not possible, since they are handled by JS
            admin_dashboard = self._hijack_user(staff_user).follow()

            self.assertEqual(admin_dashboard.status_code, 200)
            user_tools = admin_dashboard.pyquery("#user-tools").text()
            self.assertIn(staff_user.username, user_tools)

        with self.subTest("release hijacked staff user"):
            djhj_message = admin_dashboard.pyquery(".djhj")
            self.assertEqual(len(djhj_message), 1)

            release_form = admin_dashboard.forms["hijack-release"]

            response = release_form.submit()
            self.assertRedirects(
                response, reverse("admin:index"), fetch_redirect_response=False
            )
            # webtest has its own injected auth backend, and hijack trips on that for
            # follow-up requests. This is a robust way to check the hijacked user is released.
            self.assertEqual(
                self.app.session[SESSION_KEY],
                str(superuser.id),
                "Superuser is not restored after release",
            )

    def test_auditlog_entries_on_hijack_and_release(self):
        staff_user = StaffUserFactory.create(with_totp_device=True)
        superuser = SuperUserFactory.create(with_totp_device=True)
        self._login_with_mfa(superuser)

        with self.subTest("hijack user"):
            self.app.get(reverse("admin:index"), user=superuser)

            admin_dashboard = self._hijack_user(staff_user).follow()

            self.assertEqual(TimelineLogProxy.objects.count(), 1)
            log_hijack = TimelineLogProxy.objects.get()
            self.assertEqual(
                log_hijack.extra_data["hijacker"],
                {
                    "id": superuser.id,
                    "full_name": superuser.get_full_name(),
                    "username": superuser.username,
                },
            )
            self.assertEqual(
                log_hijack.extra_data["hijacked"],
                {
                    "id": staff_user.id,
                    "full_name": staff_user.get_full_name(),
                    "username": staff_user.username,
                },
            )

        with self.subTest("release user"):
            release_form = admin_dashboard.forms["hijack-release"]
            release_form.submit()

            self.assertEqual(TimelineLogProxy.objects.count(), 2)
            log_release = TimelineLogProxy.objects.order_by("-id").first()
            assert log_release is not None
            self.assertEqual(
                log_release.extra_data["hijacker"],
                {
                    "id": superuser.id,
                    "full_name": superuser.get_full_name(),
                    "username": superuser.username,
                },
            )
            self.assertEqual(
                log_release.extra_data["hijacked"],
                {
                    "id": staff_user.id,
                    "full_name": staff_user.get_full_name(),
                    "username": staff_user.username,
                },
            )


@override_settings(MAYKIN_2FA_ALLOW_MFA_BYPASS_BACKENDS=[])  # enforce MFA
class HijackSecurityTests(TestCase):
    @tag("security-28", "CVE-2024-24771")
    def test_cannot_hijack_without_second_factor(self):
        staff_user = StaffUserFactory.create(with_totp_device=True)
        superuser = SuperUserFactory.create(with_totp_device=True)
        superuser.totpdevice_set.create()
        self.client.force_login(superuser)

        # sanity check - MFA is being enforced
        admin_index_response = self.client.get(reverse("admin:index"))
        assert admin_index_response.status_code == 302, (
            "Non-verified user unexpected has access to the admin"
        )

        # try the hijack
        acquire = self.client.post(
            reverse("hijack:acquire"),
            data={"user_pk": staff_user.pk},
        )

        with self.subTest("hijack blocked"):
            # bad request due to SuspiciousOperation or 403 from PermissionDenied
            self.assertIn(acquire.status_code, [400, 403])

        with self.subTest("release does not allow gaining verified state"):
            # release the user
            release = self.client.post(reverse("hijack:release"))

            with self.subTest("release blocked due to hijack not being acquired"):
                self.assertEqual(release.status_code, 403)

            with self.subTest("no access to admin gained"):
                # due to bypass via release action which sets up a device
                admin_response = self.client.get(reverse("admin:index"))

                self.assertNotEqual(admin_response.status_code, 200)

    def test_drf_login_url_not_enabled(self):
        """
        The DRF login view may not be enabled, as this bypasses MFA.
        """
        try:
            reverse("rest_framework:login")
        except NoReverseMatch:
            pass
        else:
            self.fail("The DRF login view is exposed, which bypasses MFA!")
