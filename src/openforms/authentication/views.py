from urllib.parse import urlparse, urlunparse

from django.http import HttpResponseBadRequest, HttpResponseNotAllowed
from django.views import View
from django.views.generic.detail import SingleObjectMixin

from corsheaders.conf import conf as cors_conf
from corsheaders.middleware import CorsMiddleware

from openforms.authentication.registry import register
from openforms.forms.models import Form


def origin_from_url(url):
    parts = urlparse(url)
    new = [parts[0], parts[1], "", "", "", ""]
    return urlunparse(new)


def allow_redirect_url(url):
    cors = CorsMiddleware()
    origin = origin_from_url(url)
    parts = urlparse(url)

    if not cors_conf.CORS_ALLOW_ALL_ORIGINS and not cors.origin_found_in_white_lists(
        origin, parts
    ):
        return False
    else:
        return True


class AuthenticationStartView(SingleObjectMixin, View):
    queryset = Form.objects.live()
    register = register

    def get(self, request, slug, plugin_id):
        form = self.get_object()
        try:
            plugin = self.register[plugin_id]
        except KeyError:
            return HttpResponseBadRequest("unknown plugin")

        if not form.login_required:
            return HttpResponseBadRequest("login not required")

        if plugin_id not in form.authentication_backends:
            return HttpResponseBadRequest("plugin not allowed")

        form_url = request.GET.get("next")
        if not form_url:
            return HttpResponseBadRequest("missing 'next' parameter")

        if not allow_redirect_url(form_url):
            return HttpResponseBadRequest("redirect not allowed")

        response = plugin.start_login(request, form, form_url)
        return response


class AuthenticationReturnView(SingleObjectMixin, View):
    queryset = Form.objects.live()
    register = register

    def dispatch(self, request, slug, plugin_id):
        form = self.get_object()
        try:
            plugin = self.register[plugin_id]
        except KeyError:
            return HttpResponseBadRequest("unknown plugin")

        if not form.login_required:
            return HttpResponseBadRequest("login not required")

        if plugin_id not in form.authentication_backends:
            return HttpResponseBadRequest("plugin not allowed")

        if plugin.return_method.upper() != request.method.upper():
            return HttpResponseNotAllowed([plugin.return_method])

        response = plugin.handle_return(request, form)

        if response.status_code in (301, 302):
            location = response.get("Location", "")
            if location and not allow_redirect_url(location):
                return HttpResponseBadRequest("redirect not allowed")

        return response
