import io
import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

import requests
from django_sendfile import sendfile
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from drf_spectacular.utils import extend_schema, extend_schema_view
from furl import furl
from rest_framework.generics import DestroyAPIView, GenericAPIView
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from ..attachments import clean_mime_type
from ..models import SubmissionReport, TemporaryFileUpload
from ..utils import add_upload_to_session, remove_upload_from_session
from .permissions import (
    AnyActiveSubmissionPermission,
    DownloadSubmissionReportPermission,
    OwnsTemporaryUploadPermission,
)
from .renderers import FileRenderer, PDFRenderer
from .serializers import (
    AssessmentReCaptchaOutcome,
    AssessmentReCaptchaOutcomeSerializer,
    AssessmentReCaptchaSerializer,
    SubmissionReCaptchaSerializer,
    TemporaryFileUploadSerializer,
)


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
        "Unclaimed temporary files automatically expire after {expire_days} day(s). "
    ).format(expire_days=settings.TEMPORARY_UPLOADS_REMOVED_AFTER_DAYS),
)
class TemporaryFileUploadView(GenericAPIView):
    parser_classes = [MultiPartParser]
    serializer_class = TemporaryFileUploadSerializer
    authentication_classes = []
    permission_classes = [AnyActiveSubmissionPermission]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data["file"]

        # trim name part if necessary but keep the extension
        name, ext = os.path.splitext(file.name)
        name = name[: 255 - len(ext)] + ext

        upload = TemporaryFileUpload.objects.create(
            content=file,
            file_name=name,
            content_type=clean_mime_type(file.content_type),
        )
        add_upload_to_session(upload, self.request.session)

        return Response(
            self.serializer_class(instance=upload, context={"request": request}).data
        )


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


@extend_schema(
    summary=_("reCAPTCHA assessment"),
    description=_(
        "Endpoint used by the SDK to get the risk assessment for an action performed by the user."
    ),
    responses={200: AssessmentReCaptchaOutcomeSerializer},
)
class SubmissionCaptchaView(APIView):
    permission_classes = [AnyActiveSubmissionPermission]
    serializer_class = SubmissionReCaptchaSerializer
    authentication_classes = ()

    def _generate_assessment(self, token, action):
        captcha_endpoint = furl(
            f"https://recaptchaenterprise.googleapis.com/v1beta1/projects/{settings.RECAPTCHA_PROJECT_ID}/assessments"
        )
        captcha_endpoint.args["key"] = settings.RECAPTCHA_API_KEY

        captcha_response = requests.post(
            captcha_endpoint.url,
            json={
                "event": {
                    "token": token,
                    "siteKey": settings.RECAPTCHA_SITE_KEY,
                    "expectedAction": action,
                }
            },
        )
        captcha_response.raise_for_status()

        parser = CamelCaseJSONParser()
        assessment_data = parser.parse(io.BytesIO(captcha_response.content))

        assessment_serializer = AssessmentReCaptchaSerializer(data=assessment_data)
        assessment_serializer.is_valid(raise_exception=True)
        return assessment_serializer.validated_data

    def post(self, request: Request) -> Response:
        serializer = SubmissionReCaptchaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        assessment = self._generate_assessment(**serializer.validated_data)

        outcome = AssessmentReCaptchaOutcome(allow_submission=assessment["score"] > 0.5)
        serializer = AssessmentReCaptchaOutcomeSerializer(instance=outcome)
        return Response(serializer.data)
