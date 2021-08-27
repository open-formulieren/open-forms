from mozilla_django_oidc.middleware import SessionRefresh

from .mixins import SoloConfigMixin
from .models import OpenIDConnectPublicConfig


class SessionRefresh(SoloConfigMixin, SessionRefresh):
    def process_request(self, request):
        config = OpenIDConnectPublicConfig.get_solo()
        if not config.enabled:
            return

        return super().process_request(request)
