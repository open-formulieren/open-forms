from django import http
from django.http import Http404
from django.template import TemplateDoesNotExist, loader
from django.views.decorators.csrf import requires_csrf_token
from django.views.defaults import ERROR_500_TEMPLATE_NAME
from django.views.generic import TemplateView

from rest_framework import exceptions as drf_exceptions

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
