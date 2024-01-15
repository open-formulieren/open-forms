from django.utils.translation import gettext as _

from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from openforms.submissions.api.permissions import AnyActiveSubmissionPermission

from ..models import GlobalConfiguration
from .serializers import PrivacyPolicyInfo, PrivacyPolicyInfoSerializer


@extend_schema(
    deprecated=True,
    summary=_("Privacy policy info"),
    responses={200: PrivacyPolicyInfoSerializer},
)
class PrivacyPolicyInfoView(APIView):
    permission_classes = (AnyActiveSubmissionPermission,)

    def get(self, request: Request) -> Response:
        conf = GlobalConfiguration.get_solo()
        if not conf.ask_privacy_consent:
            info = PrivacyPolicyInfo(requires_privacy_consent=False)
        else:
            info = PrivacyPolicyInfo(
                requires_privacy_consent=True,
                privacy_label=conf.render_privacy_policy_label(),
            )

        serializer = PrivacyPolicyInfoSerializer(
            instance=info, context={"request": request, "view": self}
        )

        return Response(serializer.data)
