from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import BadRequest
from django.http import Http404, HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic import RedirectView, TemplateView

from rest_framework import exceptions as drf_exceptions

from openforms.emails.context import get_wrapper_context
from openforms.forms.context_processors import sdk_urls
from openforms.submissions.models import Submission

from ..api import exceptions


class ErrorDetailView(TemplateView):
    template_name = "errors/error_detail.html"

    def _get_exception_klass(self):
        klass = self.kwargs["exception_class"]

        for module in [exceptions, drf_exceptions]:
            exc_klass = getattr(module, klass, None)
            if exc_klass is not None:
                return exc_klass
        else:
            raise Http404(f"Unknown exception class '{klass}'")

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


@method_decorator(never_cache, name="dispatch")
class SDKRedirectView(RedirectView):
    permanent = False

    def get_redirect_url(self, ext: str):
        urls = sdk_urls(self.request)
        match ext:
            case "js":
                return urls["sdk_umd_url"]
            case "mjs":
                return urls["sdk_esm_url"]
            case "css":
                return urls["sdk_css_url"]
            case _:
                raise BadRequest(f"Invalid extension '{ext}'")


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

        form_theme = None
        if not kwargs.get("email_digest"):
            submission = kwargs.get("object") or Submission.objects.get(
                id=kwargs.get("submission_id")
            )

            form_theme = submission.form.theme

        ctx.update(get_wrapper_context(content, form_theme))
        ctx.update(kwargs)
        return ctx

    def render_to_response(self, context, **response_kwargs):
        mode = self._get_mode()
        if mode == "text":
            return HttpResponse(
                context["content"].encode("utf-8"), content_type="text/plain"
            )
        return super().render_to_response(context, **response_kwargs)
