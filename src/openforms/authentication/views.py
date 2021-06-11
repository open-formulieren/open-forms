from django.http import HttpResponseBadRequest, HttpResponseNotAllowed
from django.views import View
from django.views.generic.detail import SingleObjectMixin

from openforms.authentication.registry import register
from openforms.forms.models import Form


class AuthenticationStartView(SingleObjectMixin, View):
    queryset = Form.objects.filter(_is_deleted=False)
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
        # TODO check whitelist from CORS
        if not form_url:
            return HttpResponseBadRequest("missing 'next' parameter")

        response = plugin.start_login(request, form, form_url)
        return response


class AuthenticationReturnView(SingleObjectMixin, View):
    queryset = Form.objects.filter(_is_deleted=False)
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
        # TODO check whitelist from CORS (again)
        return response
