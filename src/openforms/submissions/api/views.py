from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django_sendfile import sendfile
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import serializers
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.generics import DestroyAPIView, GenericAPIView
from rest_framework.response import Response

from openforms.api.authentication import AnonCSRFSessionAuthentication
from openforms.api.serializers import ExceptionSerializer
from openforms.authentication.constants import FORM_AUTH_SESSION_KEY

from ..models import Submission, SubmissionReport, TemporaryFileUpload
from ..utils import add_submmission_to_session, remove_upload_from_session
from .permissions import (
    DownloadSubmissionReportPermission,
    OwnsTemporaryUploadPermission,
)
from .renderers import FileRenderer, PDFRenderer
from .serializers import SubmissionSerializer


@extend_schema(
    summary=_("Download the PDF report"),
    description=_(
        "Download the PDF report containing the submission data. The endpoint requires "
        "a token which is tied to the submission from the session. The token automatically expires "
        "after {expire_days} day(s)."
    ).format(expire_days=settings.SUBMISSION_REPORT_URL_TOKEN_TIMEOUT_DAYS),
    responses={200: bytes},
)
class DownloadSubmissionReportView(GenericAPIView):
    queryset = SubmissionReport.objects.all()
    lookup_url_kwarg = "report_id"
    authentication_classes = ()
    permission_classes = (DownloadSubmissionReportPermission,)
    # FIXME: 404s etc. are now also rendered with this, which breaks.
    renderer_classes = (PDFRenderer,)
    serializer_class = None

    # see :func:`sendfile.sendfile` for available parameters
    sendfile_options = None

    def get_sendfile_opts(self) -> dict:
        return self.sendfile_options or {}

    def get(self, request, report_id: int, token: str, *args, **kwargs):
        submission_report = self.get_object()

        submission_report.last_accessed = timezone.now()
        submission_report.save()

        filename = submission_report.content.path
        sendfile_options = self.get_sendfile_opts()
        return sendfile(request, filename, **sendfile_options)


@extend_schema(
    summary=_("View/delete temporary upload."),
)
@extend_schema_view(
    get=extend_schema(
        summary=_("Retrieve temporary file upload"),
        description=_(
            "Retrieve temporary file upload for review by the uploader. \n\n"
            "This is called by the default Form.io file upload widget. \n\n"
            "Access to this view requires an active form submission. "
            "Unclaimed temporary files automatically expire after {expire_days} day(s). "
        ).format(expire_days=settings.TEMPORARY_UPLOADS_REMOVED_AFTER_DAYS),
        responses={
            (200, "application/octet-stream"): bytes,
        },
    ),
    delete=extend_schema(
        summary=_("Delete temporary file upload"),
        description=_(
            "Delete temporary file upload by the uploader. \n\n"
            "This is called by the default Form.io file upload widget. \n\n"
            "Access to this view requires an active form submission. "
            "Unclaimed temporary files automatically expire after {expire_days} day(s). "
        ),
        responses={
            204: None,
            ("4XX", CamelCaseJSONRenderer.media_type): ExceptionSerializer,
            ("5XX", CamelCaseJSONRenderer.media_type): ExceptionSerializer,
        },
    ),
)
class TemporaryFileView(DestroyAPIView):
    authentication_classes = (AnonCSRFSessionAuthentication,)
    permission_classes = [OwnsTemporaryUploadPermission]
    renderer_classes = [FileRenderer, CamelCaseJSONRenderer]

    queryset = TemporaryFileUpload.objects.all()
    lookup_field = "uuid"

    def get(self, request, *args, **kwargs):
        upload = self.get_object()
        return sendfile(
            request,
            upload.content.path,
            attachment=True,
            attachment_filename=upload.file_name,
            mimetype=upload.content_type,
        )

    def perform_destroy(self, instance):
        remove_upload_from_session(instance, self.request.session)
        instance.delete()


class RetrieveSubmissionSerializer(serializers.Serializer):
    form_slug = serializers.CharField()
    # TODO validate code is valid, the submission exists and needs cosign, the submission is for the right form
    submission_reference_code = serializers.CharField()


class RetrieveSubmissionForCosignView(GenericAPIView):
    authentication_classes = (AnonCSRFSessionAuthentication,)
    serializer_class = RetrieveSubmissionSerializer

    def post(self, request, *args, **kwargs):
        # TODO add permissions to view?
        # Check that the person is logged in through an authentication backend
        auth_info = request.session.get(FORM_AUTH_SESSION_KEY)
        if not auth_info:
            raise PermissionDenied

        serializer = RetrieveSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            submission = Submission.objects.get(
                public_registration_reference=serializer.validated_data[
                    "submission_reference_code"
                ]
            )
        except Submission.DoesNotExist:
            raise NotFound

        add_submmission_to_session(submission, self.request.session)

        submission_serializer = SubmissionSerializer(
            instance=submission, context={"request": request}
        )

        return Response(submission_serializer.data)
