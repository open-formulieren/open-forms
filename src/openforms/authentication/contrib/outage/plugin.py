from django.utils.translation import gettext_lazy as _

from openforms.authentication.base import BasePlugin
from openforms.authentication.constants import AuthAttribute
from openforms.authentication.registry import register


@register("demo-outage")
class OutageAuthentication(BasePlugin):
    """
    Simulate an outage in a generic authentication backend
    """

    verbose_name = _("Demo Outage")
    is_demo_plugin = True
    provides_auth = (AuthAttribute.bsn,)

    def start_login(self, request, form, form_url, options):
        raise Exception("simulated backend failure")

    def handle_return(self, request, form, options):
        raise Exception("simulated backend failure")


@register("bsn-outage")
class BSNOutageAuthentication(OutageAuthentication):
    """
    Simulate an outage in a backend that provides BSN
    """

    verbose_name = _("BSN Outage")
    provides_auth = (AuthAttribute.bsn,)


@register("kvk-outage")
class KVKOutageAuthentication(OutageAuthentication):
    """
    Simulate an outage in a backend that provides KvK number
    """

    verbose_name = _("KvK Outage")
    provides_auth = (AuthAttribute.kvk,)
