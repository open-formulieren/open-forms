from django.utils.translation import gettext as _

from drf_spectacular.plumbing import build_array_type
from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from openforms.api.serializers import ExceptionSerializer
from openforms.formio.typing import Component
from openforms.submissions.api.permissions import AnyActiveSubmissionPermission

from ..models import GlobalConfiguration
from .constants import STATEMENT_CHECKBOX_SCHEMA
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


@extend_schema(
    summary=_("Submission statements configuration"),
    description=_(
        "Return the list of statements that the user may have to accept before being "
        "able to submit a form. The statements are returned as a list of Form.io "
        "checkbox components."
    ),
    responses={
        200: build_array_type(STATEMENT_CHECKBOX_SCHEMA),
        403: ExceptionSerializer,
    },
)
class StatementsInfoListView(APIView):
    permission_classes = (AnyActiveSubmissionPermission,)

    def get(self, request: Request) -> Response:
        conf = GlobalConfiguration.get_solo()
        assert isinstance(conf, GlobalConfiguration)  # type checker hint

        # TODO Generalise to configurable declarations & implement using
        # openforms.api.views.ListMixin
        privacy_policy_checkbox = Component(
            key="privacyPolicyAccepted",
            label=conf.render_privacy_policy_label(),
            validate={"required": conf.ask_privacy_consent},
            type="checkbox",
        )
        truth_declaration_checkbox = Component(
            key="statementOfTruthAccepted",
            label=conf.statement_of_truth_label,
            validate={"required": conf.ask_statement_of_truth},
            type="checkbox",
        )

        return Response([privacy_policy_checkbox, truth_declaration_checkbox])
