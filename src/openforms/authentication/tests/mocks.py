from django.http import HttpResponse, HttpResponseRedirect

from ..base import BasePlugin


class Plugin(BasePlugin):
    verbose_name = "some human readable label"

    def start_login(self, request, form, form_url):
        return HttpResponse("start")

    def handle_return(self, request, form):
        return HttpResponseRedirect(request.GET.get("next"))


class FailingPlugin(BasePlugin):
    verbose_name = "some human readable label"

    def start_login(self, request, form, form_url):
        raise Exception("start")

    def handle_return(self, request, form):
        raise Exception("return")
