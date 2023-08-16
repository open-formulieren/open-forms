from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView

from openforms.forms.constants import SubmissionAllowedChoices
from openforms.submissions.api.permissions import owns_submission
from openforms.submissions.models import Submission


class AppointmentCreatePermission(permissions.BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        # the view needs to implement a `extract_submission` method.
        submission: Submission | None = view.extract_submission()  # type: ignore
        if submission is None or not owns_submission(request, submission.uuid):
            return False
        # is submission allowed on the form?
        return submission.form.submission_allowed == SubmissionAllowedChoices.yes
