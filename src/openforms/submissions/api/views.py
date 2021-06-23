from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django_sendfile import sendfile
from drf_spectacular.utils import extend_schema
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from ..models import SubmissionReport
from ..tokens import token_generator
from .renderers import PDFRenderer
from .serializers import ReportStatusSerializer


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
