from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView

from ..constants import SUBMISSIONS_SESSION_KEY


class ActiveSubmissionPermission(permissions.BasePermission):
    """
    Verify that there is at least one active submission for the user session.
    """

    submission_url_kwarg = "submission_uuid"

    def has_permission(self, request: Request, view: APIView) -> bool:
        active_submissions = request.session.get(SUBMISSIONS_SESSION_KEY)
        if not active_submissions:
            return False

        submission_id = view.kwargs[self.submission_url_kwarg]
        return submission_id in active_submissions
