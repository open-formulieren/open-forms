import os

from django.conf import settings
from django.template.defaultfilters import filesizeformat
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django_sendfile import sendfile
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.generics import DestroyAPIView, GenericAPIView
from rest_framework.response import Response

from openforms.api.parsers import MaxFilesizeMultiPartParser

from ..attachments import clean_mime_type
from ..models import SubmissionReport, TemporaryFileUpload
from ..utils import add_upload_to_session, remove_upload_from_session
from .permissions import (
    AnyActiveSubmissionPermission,
    DownloadSubmissionReportPermission,
    OwnsTemporaryUploadPermission,
)
from .renderers import FileRenderer, PDFRenderer, PlainTextErrorRenderer
from .serializers import TemporaryFileUploadSerializer


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
    summary=_("Create temporary file upload"),
    description=_(
        'File upload handler for the Form.io file upload "url" storage type.\n\n'
        "The uploads are stored temporarily and have to be claimed by the form submission "
        "using the returned JSON data. \n\n"
        "Access to this view requires an active form submission. "
        "Unclaimed temporary files automatically expire after {expire_days} day(s). \n\n"
        "The maximum upload size for this instance is `{max_upload_size}`. Note that "
        "this includes the multipart metadata and boundaries, so the actual maximum "
        "file upload size is slightly smaller."
    ).format(
        expire_days=settings.TEMPORARY_UPLOADS_REMOVED_AFTER_DAYS,
        max_upload_size=filesizeformat(settings.MAX_FILE_UPLOAD_SIZE),
    ),
    responses={
        200: TemporaryFileUploadSerializer,
        400: bytes,
    },
    deprecated=True,
)
class TemporaryFileUploadView(GenericAPIView):
    parser_classes = [MaxFilesizeMultiPartParser]
    serializer_class = TemporaryFileUploadSerializer
    authentication_classes = []
    permission_classes = [AnyActiveSubmissionPermission]
    renderer_classes = [CamelCaseJSONRenderer]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
        )
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
                content_type="text/plain",
            )

        file = serializer.validated_data["file"]

        # trim name part if necessary but keep the extension
        name, ext = os.path.splitext(file.name)
        name = name[: 255 - len(ext)] + ext

        upload = TemporaryFileUpload.objects.create(
            content=file,
            file_name=name,
            content_type=clean_mime_type(file.content_type),
            file_size=file.size,
        )
        add_upload_to_session(upload, self.request.session)

        return Response(
            self.serializer_class(instance=upload, context={"request": request}).data
        )

    def finalize_response(self, request, response, *args, **kwargs):
        """
        Override renderer to support JSON for success and text for error response
        """
        if response.status_code == 400:
            request.accepted_renderer = PlainTextErrorRenderer()
            request.accepted_media_type = "text/plain"
        response = super().finalize_response(request, response, *args, **kwargs)
        return response


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
        responses={200: bytes},
    ),
    delete=extend_schema(
        summary=_("Delete temporary file upload"),
        description=_(
            "Delete temporary file upload by the uploader. \n\n"
            "This is called by the default Form.io file upload widget. \n\n"
            "Access to this view requires an active form submission. "
            "Unclaimed temporary files automatically expire after {expire_days} day(s). "
        ),
        responses={204: None},
    ),
)
class TemporaryFileView(DestroyAPIView):
    authentication_classes = []
    permission_classes = [OwnsTemporaryUploadPermission]
    renderer_classes = [FileRenderer]

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
