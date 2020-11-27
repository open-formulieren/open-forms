from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView

from ..constants import SUBMISSIONS_SESSION_KEY


class ActiveSubmissionPermission(permissions.BasePermission):
    """
    Verify that there is at least one active submission for the user session.
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        if getattr(view, "action", None) in ("create",):
            return True

        active_submissions = request.session.get(SUBMISSIONS_SESSION_KEY)
        if not active_submissions:
            return False

        return True

        default_url_kwarg = view.lookup_url_kwarg or view.lookup_field
        submission_url_kwarg = getattr(view, "submission_url_kwarg", default_url_kwarg)

        submission_id = view.kwargs[submission_url_kwarg]
        return submission_id in active_submissions

    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        active_submissions = request.session.get(SUBMISSIONS_SESSION_KEY)

        default_url_kwarg = view.lookup_url_kwarg or view.lookup_field
        submission_url_kwarg = getattr(view, "submission_url_kwarg", default_url_kwarg)

        submission_id = view.kwargs[submission_url_kwarg]
        return submission_id in active_submissions
