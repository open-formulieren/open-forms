from rest_framework import permissions, serializers
from rest_framework.request import Request
from rest_framework.views import APIView

from openforms.forms.constants import SubmissionAllowedChoices
from openforms.submissions.api.permissions import owns_submission
from openforms.submissions.models import Submission


class PermissionSerializer(serializers.Serializer):
    submission = serializers.HyperlinkedRelatedField(
        required=True,
        queryset=Submission.objects.all(),
        view_name="api:submission-detail",
        lookup_field="uuid",
    )


class AppointmentCreatePermission(permissions.BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        serializer = PermissionSerializer(data=request.data)
        if not serializer.is_valid():
            return False

        submission = serializer.validated_data["submission"]
        if not owns_submission(request, submission.uuid):
            return False

        # is submission allowed on the form?
        return submission.form.submission_allowed == SubmissionAllowedChoices.yes
