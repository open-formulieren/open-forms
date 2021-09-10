from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView

from openforms.api.permissions import TimestampedTokenPermission

from ..constants import SUBMISSIONS_SESSION_KEY, UPLOADS_SESSION_KEY
from ..tokens import submission_report_token_generator


class AnyActiveSubmissionPermission(permissions.BasePermission):
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


class ActiveSubmissionPermission(AnyActiveSubmissionPermission):
    """
    Verify that there is at least one active submission for the user session.
    """

    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        active_submissions = request.session.get(SUBMISSIONS_SESSION_KEY)

        default_url_kwarg = view.lookup_url_kwarg or view.lookup_field
        submission_url_kwarg = getattr(view, "submission_url_kwarg", default_url_kwarg)

        submission_id = view.kwargs[submission_url_kwarg]
        return submission_id in active_submissions

    def filter_queryset(self, request: Request, view: APIView, queryset):
        active_submissions = request.session.get(SUBMISSIONS_SESSION_KEY)
        if not active_submissions:
            return queryset.none()
        return queryset.filter(uuid__in=active_submissions)


class OwnsTemporaryUploadPermission(permissions.BasePermission):
    """
    Verify the upload is registered in the users session
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        active_uploads = request.session.get(UPLOADS_SESSION_KEY)
        if not active_uploads:
            return False
        return True

    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        active_uploads = request.session.get(UPLOADS_SESSION_KEY)

        upload_url_kwarg = view.lookup_url_kwarg or view.lookup_field
        upload_uuid = view.kwargs[upload_url_kwarg]

        return str(upload_uuid) in active_uploads

    def filter_queryset(self, request: Request, view: APIView, queryset):
        active_uploads = request.session.get(UPLOADS_SESSION_KEY)
        if not active_uploads:
            return queryset.none()
        return queryset.filter(uuid__in=active_uploads)


class DownloadSubmissionReportPermission(TimestampedTokenPermission):
    token_generator = submission_report_token_generator
