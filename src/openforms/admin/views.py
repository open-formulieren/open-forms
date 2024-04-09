from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.shortcuts import resolve_url
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import RedirectView

from maykin_2fa.views import AdminLoginView


class ClassicAdminLoginView(AdminLoginView):
    def get_prefix(self, request, *args, **kwargs):
        # The subclass causes this to become ``classic_admin_login_view``, which is
        # misaligned with :meth:`maykin_2fa.views.RecoveryTokenView.get_prefix` and
        # results in being sent to the login screen again.
        return "admin_login_view"

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form, **kwargs)
        redirect_to = self.request.GET.get(self.redirect_field_name, "")
        context.setdefault(self.redirect_field_name, redirect_to)
        return context


class AdminLoginRedirectView(RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs) -> str:
        default = reverse("admin:index")
        redirect_to = self.request.GET.get(REDIRECT_FIELD_NAME, default)
        url_is_safe = url_has_allowed_host_and_scheme(
            url=redirect_to,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        )
        redirect_to = redirect_to if url_is_safe else default

        # user already logged in and MFA verified -> send to the final destination
        if self.request.user.is_authenticated and self.request.user.is_verified():
            return redirect_to

        redirect_to_name = (
            "oidc_authentication_init"
            if settings.USE_OIDC_FOR_ADMIN_LOGIN
            else "admin-mfa-login"
        )
        query = urlencode({REDIRECT_FIELD_NAME: redirect_to}, safe="/")
        return f"{resolve_url(redirect_to_name)}?{query}"
