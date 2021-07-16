import os

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django_sendfile import sendfile
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from ..attachments import clean_mime_type
from ..models import SubmissionFileAttachment, SubmissionReport, TemporaryFileUpload
from ..tokens import token_generator
from .renderers import PDFRenderer
from .serializers import ReportStatusSerializer, TemporaryFileUploadSerializer


class RetrieveReportBaseView(GenericAPIView):
    queryset = SubmissionReport.objects.all()
    lookup_url_kwarg = "report_id"


@extend_schema(
    summary=_("Get PDF report generation status"),
    description=_(
        "On submission completion, a PDF report is generated with the submitted form "
        "data. This is done in a background job. You can use this endpoint to check "
        "the status of this PDF generation. The endpoint requires a token which is "
        "tied to the submission from the session. Once the PDF is downloaded, this "
        "token is invalidated. The token also automatically expires after "
        "{expire_days} day(s)."
    ).format(expire_days=settings.SUBMISSION_REPORT_URL_TOKEN_TIMEOUT_DAYS),
)
class CheckReportStatusView(RetrieveReportBaseView):
    authentication_classes = ()
    serializer_class = ReportStatusSerializer

    def get(self, request, report_id: int, token: str, *args, **kwargs):
        submission_report = self.get_object()

        # Check that the token is valid
        valid = token_generator.check_token(submission_report, token)
        if not valid:
            raise PermissionDenied

        # Check if the celery task finished creating the report
        async_result = submission_report.get_celery_task()
        serializer = self.serializer_class(instance=async_result)
        return Response(serializer.data)


@extend_schema(
    summary=_("Download the PDF report"),
    description=_(
        "Download the PDF report containing the submission data. The endpoint requires "
        "a token which is tied to the submission from the session. Once the PDF is "
        "downloaded, this token is invalidated. The token also automatically expires "
        "after {expire_days} day(s)."
    ).format(expire_days=settings.SUBMISSION_REPORT_URL_TOKEN_TIMEOUT_DAYS),
    responses={200: bytes},
)
class DownloadSubmissionReportView(RetrieveReportBaseView):
    authentication_classes = ()
    # FIXME: 404s etc. are now also rendered with this, which breaks.
    renderer_classes = (PDFRenderer,)
    serializer_class = None

    # see :func:`sendfile.sendfile` for available parameters
    sendfile_options = None

    def get_sendfile_opts(self) -> dict:
        return self.sendfile_options or {}

    def get(self, request, report_id: int, token: str, *args, **kwargs):
        submission_report = self.get_object()

        # Check that the token is valid
        valid = token_generator.check_token(submission_report, token)
        if not valid:
            raise PermissionDenied

        submission_report.last_accessed = timezone.now()
        submission_report.save()

        filename = submission_report.content.path
        sendfile_options = self.get_sendfile_opts()
        return sendfile(request, filename, **sendfile_options)


# TODO api docs
class TemporaryFileUploadView(APIView):
    parser_classes = [MultiPartParser]
    serializer_class = TemporaryFileUploadSerializer
    authentication_classes = []
    # TODO enable throttle (same as elsewhere?)
    throttle_classes = []

    def post(self, request, *args, **kwargs):
        # TODO check require_valid_submission (??) and see if we are a human and active
        file = self.request.data["file"]

        # trim name part if necessary but keep the extension
        name, ext = os.path.splitext(file.name)
        name = name[: 255 - len(ext)] + ext

        upload = TemporaryFileUpload.objects.create(
            content=file,
            file_name=name,
            content_type=clean_mime_type(file.content_type),
        )
        return Response(
            self.serializer_class(instance=upload, context={"request": request}).data
        )


# TODO api docs
class TemporaryFileView(GenericAPIView):
    authentication_classes = []
    # TODO enable throttle (same as elsewhere?)
    throttle_classes = []

    queryset = TemporaryFileUpload.objects.all()
    lookup_field = "uuid"

    def get(self, request, *args, **kwargs):
        # TODO access control? uuid enough?
        upload = self.get_object()
        return sendfile(
            request,
            upload.content.path,
            attachment=True,
            attachment_filename=upload.file_name,
            mimetype=upload.content_type,
        )

    def delete(self, request, *args, **kwargs):
        # TODO access control? uuid enough?
        upload = self.get_object()
        upload.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
