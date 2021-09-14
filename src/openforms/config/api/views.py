from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from openforms.submissions.api.permissions import AnyActiveSubmissionPermission

from ..models import GlobalConfiguration


class PrivacyPolicyInfoView(APIView):
    permission_classes = (AnyActiveSubmissionPermission,)

    def get(self, request: Request) -> Response:
        conf = GlobalConfiguration.get_solo()
        if not conf.ask_privacy_consent:
            return Response({"requires_privacy_consent": False})

        return Response(
            {
                "requires_privacy_consent": True,
                "privacy_label": conf.render_privacy_policy_label(),
            }
        )
