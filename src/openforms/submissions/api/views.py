from django.core.exceptions import PermissionDenied
from django.utils import timezone

from django_sendfile import sendfile
from rest_framework.response import Response
from rest_framework.views import APIView

from openforms.submissions.models import SubmissionReport
from openforms.submissions.tokens import token_generator


class CheckReportStatusView(APIView):
    def get(self, request, report_id: int, token: str, *args, **kwargs):
        submission_report = SubmissionReport.objects.get(id=report_id)

        # Check that the token is valid
        valid = token_generator.check_token(submission_report, token)
        if not valid:
            raise PermissionDenied

        # Check if the celery task finished creating the report
        status = submission_report.check_content_status()
        return Response({"status": status})


class DownloadSubmissionReportView(APIView):

    # see :func:`sendfile.sendfile` for available parameters
    sendfile_options = None
    model = SubmissionReport

    def get_sendfile_opts(self) -> dict:
        return self.sendfile_options or {}

    def get(self, request, report_id: int, token: str, *args, **kwargs):
        submission_report = SubmissionReport.objects.get(id=report_id)

        # Check that the token is valid
        valid = token_generator.check_token(submission_report, token)
        if not valid:
            raise PermissionDenied

        submission_report.last_accessed = timezone.now()
        submission_report.save()

        filename = submission_report.content.path
        sendfile_options = self.get_sendfile_opts()
        return sendfile(request, filename, **sendfile_options)
