from django.utils.translation import gettext_lazy as _

import structlog
from drf_spectacular.utils import extend_schema
from rest_framework import authentication
from rest_framework.generics import GenericAPIView

from openforms.api.views import ListMixin
from openforms.forms.models import FormVariable
from openforms.submissions.api.permissions import ActiveSubmissionPermission
from openforms.submissions.models import Submission
from openforms.variables.constants import FormVariableSources

from ..typing import CommunicationChannel
from .serializers import CommunicationPreferencesSerializer

logger = structlog.stdlib.get_logger(__name__)


@extend_schema(
    summary=_("Get communication preferences for Customer Interactions"),
)
class CommunicationPreferencesView(ListMixin, GenericAPIView):
    """
    Get prefilled communication preferences for a particular submission
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = [ActiveSubmissionPermission]
    serializer_class = CommunicationPreferencesSerializer
    queryset = Submission.objects.all()
    lookup_url_kwarg = "submission_uuid"
    lookup_field = "uuid"

    def get_objects(self) -> list[CommunicationChannel]:
        submission = self.get_object()

        profile_variable = self.kwargs["profile_component"]
        # get prefill variable name
        try:
            form_variable = submission.form.formvariable_set.get(
                source=FormVariableSources.user_defined,
                prefill_plugin="communication_preferences",
                prefill_options__profile_form_variable=profile_variable,
            )
        except (FormVariable.DoesNotExist, FormVariable.MultipleObjectsReturned) as exc:
            logger.warning(
                "invalid_prefill_configuration",
                submission_id=submission.uuid,
                profile_variable=profile_variable,
                exc=exc,
            )
            return []

        state = submission.load_submission_value_variables_state()
        submission_variable = state.variables[form_variable.key]

        if not submission_variable.is_initially_prefilled:
            return []

        return submission_variable.value
