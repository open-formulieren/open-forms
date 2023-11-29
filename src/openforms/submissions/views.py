import logging
import uuid

from django.contrib.auth.hashers import check_password as check_salted_hash
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.utils.crypto import constant_time_compare
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, RedirectView
from django.views.generic.base import TemplateResponseMixin

from furl import furl
from privates.views import PrivateMediaView
from rest_framework.reverse import reverse

from openforms.authentication.constants import FORM_AUTH_SESSION_KEY
from openforms.authentication.utils import (
    is_authenticated_with_plugin,
    meets_plugin_requirements,
)
from openforms.forms.models import Form
from openforms.tokens import BaseTokenGenerator

from .constants import RegistrationStatuses
from .exceptions import FormDeactivated, FormMaintenance
from .forms import SearchSubmissionForCosignForm
from .models import Submission, SubmissionFileAttachment
from .signals import submission_resumed
from .tokens import submission_resume_token_generator
from .utils import add_submmission_to_session, check_form_status

logger = logging.getLogger(__name__)


class ResumeFormMixin(TemplateResponseMixin):
    request: HttpRequest
    token_generator: BaseTokenGenerator
    template_name = "submissions/resume_form_error.html"

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except (FormDeactivated, FormMaintenance) as exc:
            return self.render_to_response(
                context={"error": exc},
                status=exc.status_code if isinstance(exc, FormMaintenance) else 200,
            )

    def validate_url_and_get_submission(
        self, submission_uuid: uuid.UUID, token: str
    ) -> Submission:
        try:
            submission = Submission.objects.get(uuid=submission_uuid)
        except Submission.DoesNotExist:
            logger.debug(
                "Called endpoint with an invalid submission uuid: %s", submission_uuid
            )
            raise PermissionDenied("Url is not valid")

        # Check that the token is valid
        valid = self.token_generator.check_token(submission, token)
        if not valid:
            logger.debug("Called endpoint with an invalid token: %s", token)
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

        is_auth_plugin_correct = is_authenticated_with_plugin(
            self.request, submission.auth_info.plugin
        )
        if not meets_plugin_requirements(
            self.request, submission.form.authentication_backend_options
        ):
            return False
        is_auth_attribute_correct = (
            submission.auth_info.attribute
            == self.request.session[FORM_AUTH_SESSION_KEY]["attribute"]
        )

        submission_auth_value = submission.auth_info.value
        # there are two modus operandi - the submission may not be completed yet, in
        # which case we don't have a hashed value yet, but the raw value (used for
        # prefill and the like). There are also other flows where the attributes may
        # be hashed despite the submission not being completed yet.
        current_auth_value = self.request.session[FORM_AUTH_SESSION_KEY]["value"]

        if submission.auth_info.attribute_hashed:
            is_auth_data_correct = check_salted_hash(
                current_auth_value, submission_auth_value, setter=None
            )
        else:
            # timing attacks are not a concern here, as you need to go through a valid
            # authentication flow first which sets the value in the session. Additionally,
            # enumeration would still be possible and you don't necessarily leak passwords
            # that may be used on other sites - end-users cannot change their BSN/KVK etc.
            # anyway.
            is_auth_data_correct = submission_auth_value == current_auth_value

        return (
            is_auth_plugin_correct
            and is_auth_data_correct
            and is_auth_attribute_correct
        )

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
        form_resume_url = submission.cleaned_form_url

        state = submission.load_execution_state()
        last_completed_step = state.get_last_completed_step()
        target_step = last_completed_step or state.submission_steps[0]

        # furl adds paths with the /= operator
        form_resume_url /= "stap"
        form_resume_url /= target_step.form_step.form_definition.slug
        # Add the submission uuid to the query param
        form_resume_url.add({"submission_uuid": submission.uuid})
        return form_resume_url.url


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

        # check that a hash parameter is present on the request
        content_hash = self.request.GET.get("hash")
        if not content_hash:
            logger.warning(
                "Unauthorized file download attempted (missing content hash). Path: %s, user: %r",
                self.request.path,
                self.request.user,
            )
            raise PermissionDenied(_("File access denied."))

        # cache the object for future lookups
        if not hasattr(self, "_object"):
            obj = super().get_object(queryset=queryset)

            if not constant_time_compare(obj.content_hash, content_hash):
                logger.warning(
                    "Unauthorized file download attempted (invalid content hash). Path: %s, user: %r",
                    self.request.path,
                    self.request.user,
                )
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
    submission = None

    def test_func(self):
        """
        The user should have authenticated with the auth plugin specified on the form for the co-sign component
        """
        self.form = get_object_or_404(Form, slug=self.kwargs["form_slug"])
        cosign_component = self.form.get_cosign_component()
        expected_auth_plugin = cosign_component["authPlugin"]
        return is_authenticated_with_plugin(
            self.request, expected_auth_plugin
        ) and meets_plugin_requirements(
            self.request, self.form.authentication_backend_options
        )

    def get_form_kwargs(self):
        super_kwargs = super().get_form_kwargs()
        super_kwargs["instance"] = self.form
        return super_kwargs

    def form_valid(self, form):
        self.submission = form.cleaned_data["submission"]
        add_submmission_to_session(self.submission, self.request.session)
        return super().form_valid(form)

    def get_success_url(self):
        cosign_page = self.submission.cleaned_form_url / "cosign" / "check"
        cosign_page.args["submission_uuid"] = self.submission.uuid
        return cosign_page.url
