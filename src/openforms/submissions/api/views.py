from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django_sendfile import sendfile
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.generics import DestroyAPIView, GenericAPIView

from openforms.api.authentication import AnonCSRFSessionAuthentication
from openforms.api.serializers import ExceptionSerializer

from ..models import SubmissionReport, TemporaryFileUpload
from .permissions import (
    DownloadSubmissionReportPermission,
    OwnsTemporaryUploadPermission,
)
from .renderers import FileRenderer, PDFRenderer


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
        # delete files from disc as well if they had been already
        # saved when trying to access the next form step
        instance.attachments.all().delete()
        instance.delete()
