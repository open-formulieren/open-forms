from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from mozilla_django_oidc.views import OIDCAuthenticationCallbackView

OIDC_ERROR_SESSION_KEY = "oidc-error"


class OIDCCallbackView(OIDCAuthenticationCallbackView):
    """
    Intercept errors raised by the authentication backend and display them.
    """

    failure_url = reverse_lazy("admin-oidc-error")

    def get(self, request):
        try:
            # ensure errors don't lead to half-created users
            with transaction.atomic():
                response = super().get(request)
        except IntegrityError as exc:
            request.session[OIDC_ERROR_SESSION_KEY] = exc.args[0]
            return self.login_failure()
        else:
            if OIDC_ERROR_SESSION_KEY in request.session:
                del request.session[OIDC_ERROR_SESSION_KEY]
        return response


class AdminLoginFailure(TemplateView):
    """
    Template view in admin style to display OIDC login errors
    """

    template_name = "admin/oidc_failure.html"

    def dispatch(self, request, *args, **kwargs):
        if OIDC_ERROR_SESSION_KEY not in request.session:
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(admin.site.each_context(self.request))
        context["oidc_error"] = self.request.session[OIDC_ERROR_SESSION_KEY]
        return context
