from __future__ import annotations

import uuid
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, assert_never

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone
from django.utils.formats import localize
from django.utils.functional import cached_property
from django.utils.safestring import SafeString
from django.utils.timezone import localtime
from django.utils.translation import get_language, gettext_lazy as _

import elasticapm
import structlog
from django_jsonform.models.fields import ArrayField
from furl import furl

from openforms.config.models import GlobalConfiguration
from openforms.formio.service import FormioConfigurationWrapper, FormioData
from openforms.forms.models import FormRegistrationBackend, FormStep
from openforms.logging.logevent import registration_debug
from openforms.payments.constants import PaymentStatus
from openforms.template import openforms_backend, render_from_string
from openforms.typing import JSONObject, RegistrationBackendKey
from openforms.utils.validators import AllowedRedirectValidator, SerializerValidator

from ..constants import (
    PostSubmissionEvents,
    RegistrationStatuses,
    SubmissionValueVariableSources,
)
from ..cosigning import CosignData, CosignState
from ..pricing import get_submission_price
from ..query import SubmissionQuerySet
from ..serializers import CoSignDataSerializer
from .submission_step import SubmissionStep
from .typing import SubmissionCosignData

if TYPE_CHECKING:
    from openforms.authentication.models import AuthInfo, RegistratorInfo
    from openforms.payments.models import SubmissionPaymentManager

    from .submission_files import (
        SubmissionFileAttachment,
        SubmissionFileAttachmentQuerySet,
    )
    from .submission_report import SubmissionReport
    from .submission_value_variable import SubmissionValueVariablesState

logger = structlog.stdlib.get_logger(__name__)


@dataclass
class SubmissionState:
    form_steps: list[FormStep]
    submission_steps: list[SubmissionStep]

    def _get_step_offset(self):
        completed_steps = sorted(
            [step for step in self.submission_steps if step.completed],
            key=lambda step: step.modified,
        )
        offset = (
            0
            if not completed_steps
            else self.submission_steps.index(completed_steps[-1])
        )
        return offset

    def get_last_completed_step(self) -> SubmissionStep | None:
        """
        Determine the last step that was filled out.

        The last completed step is the step that:
        - is the last submitted step
        - is applicable

        It does not consider "skipped" steps.

        If there are no more steps, the result is None.
        """
        offset = self._get_step_offset()
        candidates = (
            step
            for step in self.submission_steps[offset:]
            if step.completed and step.is_applicable
        )
        return next(candidates, None)

    def get_submission_step(self, form_step_uuid: str) -> SubmissionStep | None:
        return next(
            (
                step
                for step in self.submission_steps
                if str(step.form_step.uuid) == form_step_uuid
            ),
            None,
        )

    def resolve_step(self, form_step_uuid: str) -> SubmissionStep:
        return self.get_submission_step(form_step_uuid=form_step_uuid)


class Submission(models.Model):
    """
    Container for submission steps that hold the actual submitted data.
    """

    uuid = models.UUIDField(_("UUID"), unique=True, default=uuid.uuid4)
    form = models.ForeignKey("forms.Form", on_delete=models.PROTECT)

    # meta information
    form_url = models.URLField(
        _("form URL"),
        max_length=1000,
        blank=False,
        default="",
        help_text=_("URL where the user initialized the submission."),
        validators=[AllowedRedirectValidator()],
    )
    created_on = models.DateTimeField(_("created on"), auto_now_add=True)
    completed_on = models.DateTimeField(_("completed on"), blank=True, null=True)
    suspended_on = models.DateTimeField(_("suspended on"), blank=True, null=True)

    co_sign_data = models.JSONField(
        _("co-sign data"),
        blank=True,
        default=dict,
        validators=[SerializerValidator(CoSignDataSerializer)],
        help_text=_("Authentication details of a co-signer."),
    )

    # payment state
    price = models.DecimalField(
        _("price"),
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        editable=False,
        help_text=_(
            "Cost of this submission. Either derived from the related product, "
            "or set through logic rules. The price is calculated and saved "
            "on submission completion."
        ),
    )

    # interaction with registration backend
    last_register_date = models.DateTimeField(
        _("last register attempt date"),
        blank=True,
        null=True,
        help_text=_(
            "The last time the submission registration was attempted with the backend.  "
            "Note that this date will be updated even if the registration is not successful."
        ),
    )
    registration_attempts = models.PositiveIntegerField(
        _("registration backend retry counter"),
        default=0,
        help_text=_(
            "Counter to track how often we tried calling the registration backend. "
        ),
    )
    registration_result = models.JSONField(
        _("registration backend result"),
        blank=True,
        null=True,
        help_text=_(
            "Contains data returned by the registration backend while registering the submission data."
        ),
    )
    registration_status = models.CharField(
        _("registration backend status"),
        max_length=50,
        choices=RegistrationStatuses.choices,
        default=RegistrationStatuses.pending,
        help_text=_(
            "Indication whether the registration in the configured backend was successful."
        ),
    )
    pre_registration_completed = models.BooleanField(
        _("pre-registration completed"),
        default=False,
        help_text=_(
            "Indicates whether the pre-registration task completed successfully."
        ),
    )
    public_registration_reference = models.CharField(
        _("public registration reference"),
        max_length=100,
        blank=True,
        help_text=_(
            "The registration reference communicated to the end-user completing the form. "
            "This reference is intended to be unique and the reference the end-user uses "
            "to communicate with the service desk. It should be extracted from the "
            "registration result where possible, and otherwise generated to be unique. "
            "Note that this reference is displayed to the end-user and used as payment "
            "reference!"
        ),
    )
    cosign_complete = models.BooleanField(
        _("cosign complete"),
        default=False,
        help_text=_("Indicates whether the submission has been cosigned."),
    )
    cosign_request_email_sent = models.BooleanField(
        _("cosign request email sent"),
        default=False,
        help_text=_("Has the email to request a co-sign been sent?"),
    )
    cosign_confirmation_email_sent = models.BooleanField(
        _("cosign confirmation email sent"),
        default=False,
        help_text=_(
            "Has the confirmation email been sent after the submission has successfully been cosigned?"
        ),
    )

    confirmation_email_sent = models.BooleanField(
        _("confirmation email sent"),
        default=False,
        help_text=_("Indicates whether the confirmation email has been sent."),
    )

    payment_complete_confirmation_email_sent = models.BooleanField(
        _("payment complete confirmation email sent"),
        default=False,
        help_text=_("Has the confirmation emails been sent after successful payment?"),
    )

    privacy_policy_accepted = models.BooleanField(
        _("privacy policy accepted"),
        default=False,
        help_text=_("Has the user accepted the privacy policy?"),
    )
    cosign_privacy_policy_accepted = models.BooleanField(
        _("cosign privacy policy accepted"),
        default=False,
        help_text=_("Has the co-signer accepted the privacy policy?"),
    )
    statement_of_truth_accepted = models.BooleanField(
        _("statement of truth accepted"),
        default=False,
        help_text=_("Did the user declare the form to be filled out truthfully?"),
    )
    cosign_statement_of_truth_accepted = models.BooleanField(
        _("cosign statement of truth accepted"),
        default=False,
        help_text=_("Did the co-signer declare the form to be filled out truthfully?"),
    )

    _is_cleaned = models.BooleanField(
        _("is cleaned"),
        default=False,
        help_text=_(
            "Indicates whether sensitive data (if there was any) has been removed from this submission."
        ),
    )
    initial_data_reference = models.CharField(
        _("initial data reference"),
        blank=True,
        help_text=_(
            "An identifier that can be passed as a querystring when the form is started. "
            "Initial form field values are pre-populated from the retrieved data. "
            "During registration, the object may be updated again (or a new record may be created). "
            "This can be an object reference in the Objects API, for example."
        ),
    )

    # TODO: Deprecated, replaced by the PostCompletionMetadata model
    on_completion_task_ids = ArrayField(
        base_field=models.CharField(
            _("on completion task ID"),
            max_length=255,
            blank=True,
        ),
        default=list,
        verbose_name=_("on completion task IDs"),
        blank=True,
        help_text=_(
            "Celery task IDs of the on_completion workflow. Use this to inspect the "
            "state of the async jobs."
        ),
    )

    needs_on_completion_retry = models.BooleanField(
        _("needs on_completion retry"),
        default=False,
        help_text=_(
            "Flag to track if the on_completion_retry chain should be invoked. "
            "This is scheduled via celery-beat."
        ),
    )

    language_code = models.CharField(
        _("language code"),
        max_length=2,
        default=get_language,
        choices=settings.LANGUAGES,
        help_text=_(
            "The code (RFC5646 format) of the language used to fill in the Form."
        ),
    )

    finalised_registration_backend_key = models.CharField(
        _("final registration backend key"),
        max_length=50,  # FormRegistrationBackend.key.max_length
        default="",
        blank=True,
        help_text=_("The key of the registration backend to use."),
    )

    objects = SubmissionQuerySet.as_manager()

    _form_login_required: bool | None = None  # can be set via annotation
    _prefilled_data = None
    _total_configuration_wrapper = None

    # type hints for (reverse) related fields
    auth_info: AuthInfo
    report: SubmissionReport
    payments: SubmissionPaymentManager

    class Meta:
        verbose_name = _("submission")
        verbose_name_plural = _("submissions")
        constraints = [
            models.UniqueConstraint(
                fields=("public_registration_reference",),
                name="unique_public_registration_reference",
                condition=~models.Q(public_registration_reference=""),
            ),
            models.CheckConstraint(
                check=~(
                    models.Q(registration_status=RegistrationStatuses.success)
                    & models.Q(pre_registration_completed=False)
                ),
                name="registration_status_consistency_check",
            ),
            models.CheckConstraint(
                check=(
                    models.Q(finalised_registration_backend_key="")
                    | (
                        ~models.Q(finalised_registration_backend_key="")
                        & models.Q(completed_on__isnull=False)
                    )
                ),
                name="only_completed_submission_has_finalised_registration_backend_key",
                violation_error_message=_(
                    "Only completed submissions may persist a finalised registration "
                    "backend key."
                ),
            ),
        ]

    def __str__(self):
        return _("{pk} - started on {started}").format(
            pk=self.pk or _("(unsaved)"),
            started=localize(localtime(self.created_on)) or _("(no timestamp yet)"),
        )

    def refresh_from_db(self, *args, **kwargs):
        super().refresh_from_db(*args, **kwargs)
        if hasattr(self, "_execution_state"):
            del self._execution_state
        if hasattr(self, "_variables_state"):
            del self._variables_state

    def save_registration_status(
        self,
        status: RegistrationStatuses,
        result: dict | None,
        record_attempt: bool = False,
    ) -> None:
        # combine the new result with existing data, where the new result overwrites
        # on key collisions. This allows storing intermediate results in the plugin
        # itself.
        if not self.registration_result and result is None:
            full_result = None
        else:
            assert result is not None
            full_result = {
                **(self.registration_result or {}),
                **result,
            }
        self.registration_status = status
        self.registration_result = full_result
        update_fields = ["registration_status", "registration_result"]

        if status == RegistrationStatuses.failed:
            self.needs_on_completion_retry = True
            update_fields += ["needs_on_completion_retry"]

        if record_attempt:
            self.last_register_date = timezone.now()
            self.registration_attempts += 1
            update_fields += ["last_register_date", "registration_attempts"]

        self.save(update_fields=update_fields)

    @property
    def cleaned_form_url(self) -> furl:
        """
        Return the base URL where the form of the submission is/was hosted.

        The SDK itself performs client-side redirects and this URL gets recorded,
        but appointment management/submission resuming relies on the cleaned, canonical
        URL.

        See open-formulieren/open-forms#3025 for the original ticket.
        """
        furl_instance = furl(self.form_url).remove("_start")
        # if the url path ends with 'startpagina', strip it off
        if furl_instance.path.segments[-1:] == ["startpagina"]:
            furl_instance.path.segments.remove("startpagina")

        return furl_instance.remove(
            fragment=True
        )  # Fragments are present in hash based routing

    @property
    def total_configuration_wrapper(self) -> FormioConfigurationWrapper:
        if not self._total_configuration_wrapper:
            state = self.load_execution_state()
            form_steps = state.form_steps
            if len(form_steps) == 0:
                return FormioConfigurationWrapper(configuration={})

            begin_configuration = deepcopy(form_steps[0].form_definition.configuration)
            wrapper = FormioConfigurationWrapper(begin_configuration)
            for form_step in form_steps[1:]:
                wrapper += form_step.form_definition.configuration_wrapper
            self._total_configuration_wrapper = wrapper
        return self._total_configuration_wrapper

    @property
    def form_login_required(self):
        # support annotated fields to save additional queries. Unfortunately,
        # we cannot pass an annotated queryset to use within a select_related field,
        # so instead in our viewset(s) we annotate the submission object.
        #
        # This saves a number of queries, since we can avoid prefetch calls for single
        # objects or form.formstep_set.all() calls on the fly.
        if self._form_login_required is not None:
            return self._form_login_required
        return self.form.login_required

    @property
    def is_authenticated(self) -> bool:
        return hasattr(self, "auth_info")

    @property
    def registrator(self) -> AuthInfo | RegistratorInfo | None:
        if hasattr(self, "_registrator") and self._registrator:
            return self._registrator
        elif self.is_authenticated:
            return self.auth_info

    @property
    def has_registrator(self):
        return hasattr(self, "_registrator") and self._registrator is not None

    @property
    def is_completed(self):
        return bool(self.completed_on)

    @property
    def is_ready_to_hash_identifying_attributes(self) -> bool:
        """
        Check if the submission can safely hash the identifying auth attributes.
        """
        # no authentication -> there's nothing to hash
        if not self.is_authenticated:
            return False
        # completed, but not cosigned yet -> registration after cosigning requires
        # unhashed attributes
        if self.is_completed and self.cosign_state.is_waiting:
            return False

        # the submission has not been submitted/completed/finalized, so it will
        # definitely not be processed yet -> okay to hash
        if not self.is_completed:
            return True

        # fully registered, no more processing needed -> safe to hash
        if self.is_registered:
            return True

        # otherwise assume it's not safe yet
        return False

    @property
    def is_registered(self) -> bool:
        # success is set if it succeeded or there was no registration backend configured
        return self.registration_status == RegistrationStatuses.success

    @transaction.atomic()
    def remove_sensitive_data(self):
        from .submission_files import SubmissionFileAttachment

        if self.is_authenticated:
            self.auth_info.clear_sensitive_data()

        sensitive_variable_keys = self.form.formvariable_set.filter(
            is_sensitive_data=True
        ).values_list("key", flat=True)
        sensitive_variables = self.submissionvaluevariable_set.filter(
            key__in=sensitive_variable_keys
        )
        sensitive_variables.update(
            value="", source=SubmissionValueVariableSources.sensitive_data_cleaner
        )

        SubmissionFileAttachment.objects.filter(
            submission_step__submission=self,
            submission_variable__key__in=sensitive_variable_keys,
        ).delete()

        self._is_cleaned = True

        if self.co_sign_data:
            # FIXME: this only deals with cosign v1 and not v2
            # We do keep the representation, as that is used in PDF and confirmation e-mail
            # generation and is usually a label derived from the source fields.
            self.co_sign_data.update(
                {
                    "identifier": "",
                    "fields": {},
                }
            )

        self.save()

    @elasticapm.capture_span(span_type="app.data.loading")
    def load_submission_value_variables_state(
        self, refresh: bool = False
    ) -> SubmissionValueVariablesState:
        if hasattr(self, "_variables_state") and not refresh:
            return self._variables_state

        # circular import
        from .submission_value_variable import SubmissionValueVariablesState

        self._variables_state = SubmissionValueVariablesState(submission=self)
        return self._variables_state

    @elasticapm.capture_span(span_type="app.data.loading")
    def load_execution_state(self, refresh: bool = False) -> SubmissionState:
        """
        Retrieve the current execution state of steps from the database.
        """
        if hasattr(self, "_execution_state") and not refresh:
            return self._execution_state

        form_steps = list(
            self.form.formstep_set.select_related("form_definition").order_by("order")
        )
        # ⚡️ no select_related/prefetch ON PURPOSE - while processing the form steps,
        # we're doing this in python as we have the objects already from the query
        # above.
        _submission_steps = self.submissionstep_set.all()
        submission_steps = {}
        for step in _submission_steps:
            # non-empty value implies that the form_step FK was (cascade) deleted
            if step.form_step_history:
                # deleted formstep FKs are loaded from history
                if step.form_step not in form_steps:
                    form_steps.append(step.form_step)
            submission_steps[step.form_step_id] = step

        # sort the steps again in case steps from history were inserted
        form_steps = sorted(form_steps, key=lambda s: s.order)

        # build the resulting list - some SubmissionStep instances will probably not exist
        # in the database yet - this is on purpose!
        steps: list[SubmissionStep] = []
        for form_step in form_steps:
            if form_step.id in submission_steps:
                step = submission_steps[form_step.id]
                # replace the python objects to avoid extra queries and/or joins in the
                # submission step query.
                step.form_step = form_step
                step.submission = self
            else:
                # there's no known DB record for this, so we create a fresh, unsaved
                # instance and return this
                step = SubmissionStep(uuid=None, submission=self, form_step=form_step)
            steps.append(step)

        state = SubmissionState(
            form_steps=form_steps,
            submission_steps=steps,
        )
        self._execution_state = state
        return state

    def clear_execution_state(self) -> None:
        if not hasattr(self, "_execution_state"):
            return

        for submission_step in self._execution_state.submission_steps:
            submission_step._can_submit = True

        del self._execution_state

    def render_confirmation_page_title(self) -> SafeString:
        config = GlobalConfiguration.get_solo()
        template = (
            config.cosign_submission_confirmation_title
            if self.cosign_state.is_required
            else config.submission_confirmation_title
        )
        return render_from_string(
            template,
            context={"public_reference": self.public_registration_reference},
        )

    def render_confirmation_page(self) -> SafeString:
        from openforms.variables.utils import get_variables_for_context

        config = GlobalConfiguration.get_solo()
        cosign = self.cosign_state
        if cosign_required := cosign.is_required:
            template = config.cosign_submission_confirmation_template
        elif not (template := self.form.submission_confirmation_template):
            template = config.submission_confirmation_template

        context_data = {
            # use private variables that can't be accessed in the template data, so that
            # template designers can't call the .delete method, for example. Variables
            # starting with underscores are blocked by the Django template engine.
            "_submission": self,
            "_form": self.form,  # should be the same as self.form
            "public_reference": self.public_registration_reference,
            "cosigner_email": cosign.email if cosign_required else "",
            **get_variables_for_context(submission=self),
        }
        return render_from_string(template, context_data, backend=openforms_backend)

    def render_summary_page(self) -> list[JSONObject]:
        """Use the renderer logic to decide what to display in the summary page.

        The values of the component are returned raw, because the frontend decides how to display them.
        """
        from openforms.formio.rendering.nodes import ComponentNode

        from ..rendering import Renderer, RenderModes
        from ..rendering.nodes import SubmissionStepNode

        renderer = Renderer(submission=self, mode=RenderModes.summary, as_html=False)

        summary_data = []
        current_step = {}
        for node in renderer:
            if isinstance(node, SubmissionStepNode):
                if current_step != {}:
                    summary_data.append(current_step)
                current_step = {
                    "slug": node.step.form_step.slug,
                    "name": node.render(),
                    "data": [],
                }
                continue

            if isinstance(node, ComponentNode):
                current_field = {
                    "name": node.label,
                    "value": node.value,
                    "component": node.component,
                }
                current_step["data"].append(current_field)

        if current_step != {}:
            summary_data.append(current_step)

        return summary_data

    @property
    def steps(self) -> list[SubmissionStep]:
        # fetch the existing DB records for submitted form steps
        submission_state = self.load_execution_state()
        return submission_state.submission_steps

    def get_last_completed_step(self) -> SubmissionStep | None:
        """
        Determine which is the next step for the current submission.
        """
        submission_state = self.load_execution_state()
        return submission_state.get_last_completed_step()

    @property
    def data(self) -> FormioData:
        """The filled-in data of the submission.

        This is a mapping between variable keys and their corresponding values.

        .. note::

            Keys containing dots (``.``) will be nested under another mapping.
            Static variables values are *not* included.
        """
        values_state = self.load_submission_value_variables_state()
        return values_state.get_data()

    def get_co_signer(self) -> str | SubmissionCosignData:
        # Legacy cosign returns an empty string, cosign v2 returns SubmissionCosignData
        if not self.co_sign_data:
            return ""

        co_sign_data: CosignData = self.co_sign_data

        match co_sign_data:
            # v2 cosign
            case {"version": "v2"}:
                timestamp = co_sign_data.get("cosign_date")
                _co_sign_data: SubmissionCosignData = {
                    **co_sign_data,
                    "cosign_date": (
                        datetime.fromisoformat(timestamp) if timestamp else None
                    ),
                }
                return _co_sign_data

            # v1 cosign
            case {"version": "v1"}:
                if not (representation := self.co_sign_data.get("representation", "")):
                    logger.warning(
                        "incomplete_co_sign_data_detected",
                        submission_uuid=str(self.uuid),
                    )
                return representation
            case _:  # pragma: no cover
                assert_never(co_sign_data)

    def get_attachments(self) -> SubmissionFileAttachmentQuerySet:
        from .submission_files import SubmissionFileAttachment

        return SubmissionFileAttachment.objects.for_submission(self).order_by("pk")

    @property
    def attachments(self) -> SubmissionFileAttachmentQuerySet:
        return self.get_attachments()

    def get_merged_attachments(self) -> Mapping[str, list[SubmissionFileAttachment]]:
        if not hasattr(self, "_merged_attachments"):
            self._merged_attachments = self.get_attachments().as_form_dict()
        return self._merged_attachments

    def get_email_confirmation_recipients(self, submitted_data: dict) -> list[str]:
        from openforms.appointments.service import get_email_confirmation_recipients

        # first check if there are any recipients because it's an appointment form, as that
        # shortcuts the formio component checking (there aren't any)
        if emails := get_email_confirmation_recipients(self):
            return emails

        recipient_emails = set()
        for key in self.form.get_keys_for_email_confirmation():
            value = submitted_data.get(key)
            if value:
                if isinstance(value, str):
                    recipient_emails.add(value)
                elif isinstance(value, list):
                    recipient_emails.update(value)

        return list(recipient_emails)

    def calculate_price(self, save=True) -> None:
        """
        Calculate and save the price of this particular submission.
        """
        log = logger.bind(
            action="submissions.calculate_price", submission_uuid=str(self.uuid)
        )

        log.debug("start_calculation")
        if not self.payment_required:
            log.debug("skip_calculation", reason="no_payment_required")
            return None

        self.price = get_submission_price(self)
        if save:
            log.debug("save_price")
            self.save(update_fields=["price"])
        else:
            log.debug("skip_save")

    @property
    def payment_required(self) -> bool:
        if not self.form.payment_required:
            return False

        return bool(get_submission_price(self))

    @property
    def payment_user_has_paid(self) -> bool:
        # TODO support partial payments
        return self.payments.paid().exists()

    @property
    def payment_registered(self) -> bool:
        # TODO support partial payments
        return self.payments.filter(status=PaymentStatus.registered).exists()

    def get_auth_mode_display(self):
        # compact anonymous display of authentication method
        if not self.is_authenticated:
            return ""

        return f"{self.auth_info.plugin} ({self.auth_info.attribute})"

    def get_prefilled_data(self):
        if self._prefilled_data is None:
            values_state = self.load_submission_value_variables_state()
            prefill_vars = values_state.get_prefill_variables()
            self._prefilled_data = {
                variable.key: variable.value for variable in prefill_vars
            }
        return self._prefilled_data

    @cached_property
    def cosign_state(self) -> CosignState:
        return CosignState(submission=self)

    def resolve_default_registration_backend_key(
        self, enable_log: bool = False
    ) -> RegistrationBackendKey | None:
        backends = list(self.form.registration_backends.order_by("id"))
        match len(backends):  # sanity check
            case 1:
                return backends[0].key
            case 0:
                if enable_log:
                    registration_debug(
                        self,
                        extra_data={
                            "message": _("No registration backends defined on form.")
                        },
                    )
                return None
            case _:
                default = backends[0]
                if enable_log:
                    registration_debug(
                        self,
                        extra_data={
                            "message": _("Multiple backends defined on form."),
                            "backend": {"key": default.key, "name": default.name},
                        },
                    )
                return default.key

    def resolve_registration_backend(
        self, enable_log: bool = False
    ) -> FormRegistrationBackend | None:
        if self.finalised_registration_backend_key:
            try:
                return self.form.registration_backends.get(
                    key=self.finalised_registration_backend_key
                )
            except FormRegistrationBackend.DoesNotExist as e:
                registration_debug(
                    self,
                    error=e,
                    extra_data={
                        "message": _(
                            "Unknown registration backend set by form logic. Trying default..."
                        ),
                        "backend": {"key": self.finalised_registration_backend_key},
                    },
                )

        # not/faulty set by logic; fallback to default
        return (
            self.form.registration_backends.get(key=default_key)
            if (
                default_key := self.resolve_default_registration_backend_key(
                    enable_log=enable_log
                )
            )
            else None
        )

    @property
    def registration_backend(self) -> FormRegistrationBackend | None:
        return self.resolve_registration_backend(enable_log=True)

    @property
    def post_completion_task_ids(self) -> list[str]:
        """Get the IDs of the tasks triggered when the submission was completed

        Other tasks are triggered later once the submission is cosigned, a payment is made or a retry flow is triggered.
        But to give feedback to the user we only need the first set of triggered tasks.
        """
        result = self.postcompletionmetadata_set.filter(
            trigger_event=PostSubmissionEvents.on_completion
        ).first()
        return result.tasks_ids if result else []
