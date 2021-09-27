from mozilla_django_oidc.views import (
    OIDCAuthenticationRequestView as _OIDCAuthenticationRequestView,
)

from .mixins import SoloConfigMixin


class OIDCAuthenticationRequestView(SoloConfigMixin, _OIDCAuthenticationRequestView):
    pass
