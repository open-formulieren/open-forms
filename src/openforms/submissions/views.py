import uuid
from pathlib import Path

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, RedirectView
from django.views.generic.base import TemplateResponseMixin

import structlog
from furl import furl
from privates.views import PrivateMediaView
from rest_framework.reverse import reverse

from openforms.authentication.constants import FORM_AUTH_SESSION_KEY
from openforms.authentication.service import check_user_is_submission_initiator
from openforms.authentication.utils import (
    get_authentication_plugin,
    is_authenticated_with_plugin,
    meets_plugin_requirements,
)
from openforms.forms.models import Form
from openforms.frontend import get_frontend_redirect_url
from openforms.tokens import BaseTokenGenerator

from .constants import RegistrationStatuses
from .exceptions import FormDeactivated, FormMaintenance, FormMaximumSubmissions
from .forms import SearchSubmissionForCosignForm
from .models import Submission, SubmissionFileAttachment, SubmissionReport
from .signals import submission_resumed
from .tokens import submission_report_token_generator, submission_resume_token_generator
from .utils import (
    add_submmission_to_session,
    check_form_status,
)

logger = structlog.stdlib.get_logger(__name__)


class ResumeFormMixin(TemplateResponseMixin):
    request: HttpRequest
    token_generator: BaseTokenGenerator
    template_name = "submissions/resume_form_error.html"

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except (FormDeactivated, FormMaintenance, FormMaximumSubmissions) as exc:
            return self.render_to_response(
                context={"error": exc},
                status=(exc.status_code if isinstance(exc, FormMaintenance) else 200),
            )

    def validate_url_and_get_submission(
        self, submission_uuid: uuid.UUID, token: str
    ) -> Submission:
        log = logger.bind(submission_uuid=str(submission_uuid), token=token)
        try:
            submission = Submission.objects.get(uuid=submission_uuid)
        except Submission.DoesNotExist:
            log.debug("invalid_submission_lookup")
            raise PermissionDenied("Url is not valid")

        # Check that the token is valid
        valid = self.token_generator.check_token(submission, token)
        if not valid:
            log.debug("invalid_token_for_submission")
            raise PermissionDenied("Url is not valid")

        check_form_status(self.request, submission.form, include_safe_methods=True)

        return submission

    def get_form_resume_url(self, submission: Submission) -> str:
        raise NotImplementedError(
            "You must implement the 'get_form_resume_url' method."
        )

    def get_login_url(self, submission: Submission, token: str) -> str:
        auth_start_url = reverse(
            "authentication:start",
            request=self.request,
            kwargs={
                "slug": submission.form.slug,
                "plugin_id": submission.auth_info.plugin,
            },
        )

        redirect_url = furl(auth_start_url)
        redirect_url.args["next"] = reverse(
            self.request.resolver_match.view_name,
            request=self.request,
            kwargs={"submission_uuid": submission.uuid, "token": token},
        )

        return redirect_url.url

    def is_auth_data_correct(self, submission: Submission) -> bool:
        if not submission.is_authenticated:
            return False

        try:
            is_auth_plugin_correct = is_authenticated_with_plugin(
                self.request, submission.auth_info.plugin
            )
            plugin_id = get_authentication_plugin(self.request, submission.form)
        except (ValueError, KeyError):
            return False

        if not meets_plugin_requirements(self.request, submission.form, plugin_id):
            return False

        is_same_user = check_user_is_submission_initiator(self.request, submission)

        return is_auth_plugin_correct and is_same_user

    def custom_submission_modifications(self, submission: Submission) -> Submission:
        return submission

    def get_redirect_url(
        self, submission_uuid: uuid.UUID, token: str, *args, **kwargs
    ) -> str:
        submission = self.validate_url_and_get_submission(submission_uuid, token)

        # TODO: remove code duplication

        # No login required. If the user did NOT log in when initially starting the submission (that they are now
        # resuming) skip authentication.
        if not submission.form.login_required and not submission.is_authenticated:
            submission = self.custom_submission_modifications(submission)
            add_submmission_to_session(submission, self.request.session)
            submission_resumed.send(
                sender=self.__class__, instance=submission, request=self.request
            )
            return self.get_form_resume_url(submission)

        # Check if the user has already logged in.
        # This is done by checking if the authentication details are in the session and
        # if they match those in the saved submission.
        if FORM_AUTH_SESSION_KEY in self.request.session:
            if not self.is_auth_data_correct(submission):
                raise PermissionDenied("Authentication data is not valid")

            submission = self.custom_submission_modifications(submission)
            add_submmission_to_session(submission, self.request.session)
            submission_resumed.send(
                sender=self.__class__, instance=submission, request=self.request
            )
            return self.get_form_resume_url(submission)

        # The user has not logged in. Redirect them to the start of the authentication process
        return self.get_login_url(submission, token)


class ResumeSubmissionView(ResumeFormMixin, RedirectView):
    token_generator = submission_resume_token_generator

    def get_form_resume_url(self, submission: Submission) -> str:
        state = submission.load_execution_state()
        last_completed_step = state.get_last_completed_step()
        target_step = last_completed_step or state.submission_steps[0]

        return get_frontend_redirect_url(
            submission,
            action="resume",
            action_params={
                "step_slug": target_step.form_step.slug,
                "submission_uuid": str(submission.uuid),
            },
        )


class DownloadSubmissionReportView(PrivateMediaView):
    """
    Download the PDF report containing the submission data.

    This URL requires a token which is tied to the submission from the session. The
    token automatically expires after
    ``settings.SUBMISSION_REPORT_URL_TOKEN_TIMEOUT_DAYS`` days.
    """

    queryset = SubmissionReport.objects.all()
    pk_url_kwarg = "report_id"
    file_field = "content"
    raise_exception = True

    object: SubmissionReport

    def has_permission(self):
        report: SubmissionReport = self.get_object()
        token = self.kwargs["token"]
        return submission_report_token_generator.check_token(report, token)

    def get_sendfile_opts(self) -> dict:
        path = Path(self.object.content.name)
        opts = {
            "attachment": True,
            "attachment_filename": path.name,
            "mimetype": "application/pdf",
        }
        return opts

    def get(self, request: HttpRequest, *args, **kwargs):
        self.object = self.get_object()

        response = super().get(request, *args, **kwargs)

        self.object.last_accessed = timezone.now()
        self.object.save()
        return response


class SubmissionAttachmentDownloadView(LoginRequiredMixin, PrivateMediaView):
    # only consider finished submissions (those are eligible for further processing)
    # and submissions that have been successfully registered with the registration
    # backend
    queryset = SubmissionFileAttachment.objects.filter(
        submission_step__submission__completed_on__isnull=False,
        submission_step__submission__registration_status=RegistrationStatuses.success,
    )
    # expose UUIDs in URLs instead of enumeration-attack susceptible PKs
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    file_field = "content"
    permission_required = "submissions.view_submissionfileattachment"

    def has_permission(self):
        if not self.request.user.is_staff:
            return False
        return super().has_permission()

    def get_object(self, queryset=None):
        assert queryset is None, "Code path with explicit queryset not supported"
        log = logger.bind(
            action="submissions.attachment_download",
            user=self.request.user,
        )

        # check that a hash parameter is present on the request
        content_hash = self.request.GET.get("hash")
        if not content_hash:
            log.warning("missing_content_hash", download_blocked=True)
            raise PermissionDenied(_("File access denied."))

        # cache the object for future lookups
        if not hasattr(self, "_object"):
            obj = super().get_object(queryset=queryset)

            if not constant_time_compare(obj.content_hash, content_hash):
                log.warning("invalid_content_hash", download_blocked=True)
                raise PermissionDenied(_("File access denied."))

            self._object = obj

        return self._object

    def get_sendfile_opts(self) -> dict:
        submission_attachment = self.get_object()
        opts = {
            "attachment": True,
            "attachment_filename": submission_attachment.get_display_name(),
            "mimetype": submission_attachment.content_type,
        }
        return opts


class SearchSubmissionForCosignFormView(UserPassesTestMixin, FormView):
    form_class = SearchSubmissionForCosignForm
    template_name = "submissions/find_submission_for_cosign.html"
    raise_exception = True

    form = None
    submission: Submission | None = None

    def test_func(self):
        """
        The user should have authenticated with one of the auth plugin specified on the form
        """
        self.form = get_object_or_404(Form, slug=self.kwargs["form_slug"])
        try:
            plugin_id = get_authentication_plugin(self.request, self.form)
            return meets_plugin_requirements(self.request, self.form, plugin_id)
        except (ValueError, KeyError):
            return False

    def get(self, request: HttpRequest, *args, **kwargs):
        # If we have a code param in the query string, apply the shortcuts and skip
        # the actual lookup screen - the code is already provided in the URL
        if request.GET.get("code"):
            form = self.get_form()
            if form.is_valid():
                return self.form_valid(form)
        return super().get(request, *args, **kwargs)

    def get_form_kwargs(self):
        super_kwargs = super().get_form_kwargs()
        super_kwargs["instance"] = self.form
        if code := self.request.GET.get("code"):
            super_kwargs["data"] = {"code": code}

        super_kwargs["request"] = self.request
        return super_kwargs

    def form_valid(self, form: SearchSubmissionForCosignForm):
        self.submission = form.cleaned_data["submission"]
        assert self.submission
        add_submmission_to_session(self.submission, self.request.session)
        return super().form_valid(form)

    def get_success_url(self):
        assert self.submission
        return get_frontend_redirect_url(
            self.submission,
            action="cosign",
            action_params={
                "submission_uuid": str(self.submission.uuid),
            },
        )
