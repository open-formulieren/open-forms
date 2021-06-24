from django.utils.translation import gettext_lazy as _

from openforms.authentication.base import BasePlugin
from openforms.authentication.registry import register


@register("demo-outage")
class OutageAuthentication(BasePlugin):
    verbose_name = _("Demo Outage")

    def start_login(self, request, form, form_url):
        raise Exception("simulated backend failure")

    def handle_return(self, request, form):
        raise Exception("simulated backend failure")
