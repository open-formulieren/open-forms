from collections.abc import Sequence

from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

import structlog
from drf_spectacular.utils import extend_schema
from rest_framework import authentication, views

from openforms.api.views import ListMixin
from openforms.forms.models import FormVariable
from openforms.submissions.api.permissions import ActiveSubmissionPermission
from openforms.submissions.models import Submission
from openforms.typing import VariableValue
from openforms.variables.constants import FormVariableSources

from .serializers import CommunicationPreferencesSerializer

logger = structlog.stdlib.get_logger(__name__)


@extend_schema(
    summary=_("Get communication preferences for Customer Interactions"),
)
class CommunicationPreferencesView(ListMixin[VariableValue], views.APIView):
    """
    Get prefilled communication preferences for a particular submission
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = [ActiveSubmissionPermission]
    serializer_class = CommunicationPreferencesSerializer
    lookup_url_kwarg = "submission_uuid"

    def get_submission(self) -> Submission:
        submission = get_object_or_404(
            Submission, uuid=self.kwargs[self.lookup_url_kwarg]
        )

        self.check_object_permissions(self.request, submission)
        return submission

    def get_objects(self):
        submission = self.get_submission()

        profile_variable = self.kwargs["profile_component"]
        # get prefill variable name
        try:
            form_variable = submission.form.formvariable_set.get(
                source=FormVariableSources.user_defined,
                prefill_plugin="communication_preferences",
                prefill_options__profile_form_variable=profile_variable,
            )
        except FormVariable.DoesNotExist:
            # it's possible to use profile component without prefill, so no warning
            return []

        state = submission.load_submission_value_variables_state()
        value = state.get_data()[form_variable.key]
        assert isinstance(value, Sequence)
        return value
