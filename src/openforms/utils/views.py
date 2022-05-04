from django import http
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import Http404, HttpResponse
from django.template import TemplateDoesNotExist, loader
from django.views.decorators.csrf import requires_csrf_token
from django.views.defaults import ERROR_500_TEMPLATE_NAME
from django.views.generic import TemplateView

from rest_framework import exceptions as drf_exceptions

from openforms.emails.context import get_wrapper_context

from ..api import exceptions


@requires_csrf_token
def server_error(request, template_name=ERROR_500_TEMPLATE_NAME):
    """
    500 error handler.

    Templates: :template:`500.html`
    Context: None
    """
    try:
        template = loader.get_template(template_name)
    except TemplateDoesNotExist:
        if template_name != ERROR_500_TEMPLATE_NAME:
            # Reraise if it's a missing custom template.
            raise
        return http.HttpResponseServerError(
            "<h1>Server Error (500)</h1>", content_type="text/html"
        )
    context = {"request": request}
    return http.HttpResponseServerError(template.render(context))


class ErrorDetailView(TemplateView):
    template_name = "errors/error_detail.html"

    def _get_exception_klass(self):
        klass = self.kwargs["exception_class"]

        for module in [exceptions, drf_exceptions]:
            exc_klass = getattr(module, klass, None)
            if exc_klass is not None:
                return exc_klass
        else:
            raise Http404("Unknown exception class '{}'".format(klass))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exc_klass = self._get_exception_klass()
        context.update(
            {
                "type": exc_klass.__name__,
                "status_code": exc_klass.status_code,
                "default_detail": exc_klass.default_detail,
                "default_code": exc_klass.default_code,
            }
        )
        return context


class DevViewMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to allow view access only in dev mode.
    """

    def test_func(self):
        return settings.DEBUG and self.request.user.is_superuser


class EmailDebugViewMixin:  # pragma: nocover
    """
    Mixin to view the contents of an e-mail as they would be sent out.

    This view supports ?mode=html|text querystring param, defaulting to HTML.
    """

    template_name = "emails/wrapper.html"

    def _get_mode(self) -> str:
        mode = self.request.GET.get("mode", "html")
        assert mode in ("html", "text"), f"Unknown mode: {mode}"
        return mode

    def get_email_content(self):
        raise NotImplementedError()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data()
        content = self.get_email_content()
        ctx.update(get_wrapper_context(content))
        ctx.update(kwargs)
        return ctx

    def render_to_response(self, context, **response_kwargs):
        mode = self._get_mode()
        if mode == "text":
            return HttpResponse(
                context["content"].encode("utf-8"), content_type="text/plain"
            )
        return super().render_to_response(context, **response_kwargs)
