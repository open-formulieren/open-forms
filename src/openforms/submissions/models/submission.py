import logging
import uuid
from collections import OrderedDict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List, Mapping, Optional, Union

from django.contrib.auth.hashers import make_password as get_salted_hash
from django.db import models, transaction
from django.template import Context, Template
from django.urls import resolve
from django.utils.translation import gettext_lazy as _

from django_better_admin_arrayfield.models.fields import ArrayField
from furl import furl
from glom import glom

from openforms.authentication.constants import AuthAttribute
from openforms.config.models import GlobalConfiguration
from openforms.contrib.kvk.validators import validate_kvk
from openforms.formio.formatters.service import filter_printable
from openforms.forms.models import FormStep
from openforms.payments.constants import PaymentStatus
from openforms.utils.validators import (
    AllowedRedirectValidator,
    SerializerValidator,
    validate_bsn,
)

from ..constants import RegistrationStatuses
from ..pricing import get_submission_price
from ..query import SubmissionManager
from ..serializers import CoSignDataSerializer
from .submission_step import SubmissionStep

if TYPE_CHECKING:
    from .submission_files import (
        SubmissionFileAttachment,
        SubmissionFileAttachmentQuerySet,
    )

logger = logging.getLogger(__name__)


def _get_config_field(field: str) -> str:
    # workaround for when this function is called during migrations and the table
    # hasn't fully migrated yet
    qs = GlobalConfiguration.objects.values_list(field, flat=True)
    return qs.first()


def get_default_bsn() -> str:
    default_test_bsn = _get_config_field("default_test_bsn")
    return default_test_bsn or ""


def get_default_kvk() -> str:
    default_test_kvk = _get_config_field("default_test_kvk")
    return default_test_kvk or ""


@dataclass
class SubmissionState:
    form_steps: List[FormStep]
    submission_steps: List["SubmissionStep"]

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

    def get_next_step(self) -> Optional["SubmissionStep"]:
        """
        Determine the next logical step to fill out.

        The next step is the step:
        - after the last submitted step
        - that is applicable

        It does not consider "skipped" steps.

        If there are no more steps, the result is None.
        """
        offset = self._get_step_offset()
        candidates = (
            step
            for step in self.submission_steps[offset:]
            if not step.completed and step.is_applicable
        )
        return next(candidates, None)

    def get_last_completed_step(self) -> Optional["SubmissionStep"]:
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

    def get_submission_step(self, form_step_uuid: str) -> Optional["SubmissionStep"]:
        return next(
            (
                step
                for step in self.submission_steps
                if str(step.form_step.uuid) == form_step_uuid
            ),
            None,
        )

    def resolve_step(self, form_step_url: str) -> "SubmissionStep":
        step_to_modify_uuid = resolve(furl(form_step_url).pathstr).kwargs["uuid"]
        return self.get_submission_step(form_step_uuid=step_to_modify_uuid)


class Submission(models.Model):
    """
    Container for submission steps that hold the actual submitted data.
    """

    uuid = models.UUIDField(_("UUID"), unique=True, default=uuid.uuid4)
    form = models.ForeignKey("forms.Form", on_delete=models.PROTECT)

    # meta information
    form_url = models.URLField(
        _("form URL"),
        max_length=255,
        blank=False,
        default="",
        help_text=_("URL where the user initialized the submission."),
        validators=[AllowedRedirectValidator()],
    )
    created_on = models.DateTimeField(_("created on"), auto_now_add=True)
    completed_on = models.DateTimeField(_("completed on"), blank=True, null=True)
    suspended_on = models.DateTimeField(_("suspended on"), blank=True, null=True)

    # authentication state
    auth_plugin = models.CharField(
        _("auth plugin"),
        max_length=100,
        blank=True,
        help_text=_("The plugin used by the user for authentication."),
    )
    bsn = models.CharField(
        _("BSN"),
        max_length=255,  # large enough to accomodate hashes
        default=get_default_bsn,
        blank=True,
        validators=(validate_bsn,),
    )
    kvk = models.CharField(
        _("KvK number"),
        max_length=255,  # large enough to accomodate hashes
        default=get_default_kvk,
        blank=True,
        validators=(validate_kvk,),
    )
    pseudo = models.CharField(
        _("Pseudo ID"),
        max_length=255,  # large enough to accomodate hashes
        blank=True,
        help_text=_("Pseudo ID provided by authentication with eIDAS"),
    )
    auth_attributes_hashed = models.BooleanField(
        _("identifying attributes hashed"),
        help_text=_("are the auth/identifying attributes hashed?"),
        default=False,
        editable=False,
    )
    co_sign_data = models.JSONField(
        _("co-sign data"),
        blank=True,
        default=dict,
        validators=[SerializerValidator(CoSignDataSerializer)],
        help_text=_("Authentication details of a co-signer."),
    )
    prefill_data = models.JSONField(
        _("prefill data"),
        blank=True,
        default=dict,
        help_text=_("Data used for prefills."),
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
            "or evaluated from price logic rules. The price is calculated and saved "
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
        choices=RegistrationStatuses,
        default=RegistrationStatuses.pending,
        help_text=_(
            "Indication whether the registration in the configured backend was successful."
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

    confirmation_email_sent = models.BooleanField(
        _("confirmation email sent"),
        default=False,
        help_text=_("Indicates whether the confirmation email has been sent."),
    )

    _is_cleaned = models.BooleanField(
        _("is cleaned"),
        default=False,
        help_text=_(
            "Indicates whether sensitive data (if there was any) has been removed from this submission."
        ),
    )

    # tracking async execution state
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

    # relation to earlier submission which is altered after processing
    previous_submission = models.ForeignKey(
        "submissions.Submission", on_delete=models.SET_NULL, null=True, blank=True
    )

    objects = SubmissionManager()

    class Meta:
        verbose_name = _("submission")
        verbose_name_plural = _("submissions")
        constraints = [
            models.UniqueConstraint(
                fields=("public_registration_reference",),
                name="unique_public_registration_reference",
                condition=~models.Q(public_registration_reference=""),
            )
        ]

    def __str__(self):
        return _("{pk} - started on {started}").format(
            pk=self.pk or _("(unsaved)"),
            started=self.created_on or _("(no timestamp yet)"),
        )

    def refresh_from_db(self, *args, **kwargs):
        super().refresh_from_db(*args, **kwargs)
        if hasattr(self, "_execution_state"):
            del self._execution_state

    def save_registration_status(self, status, result):
        self.registration_status = status
        self.registration_result = result
        update_fields = ["registration_status", "registration_result"]

        if status == RegistrationStatuses.failed:
            self.needs_on_completion_retry = True
            update_fields += ["needs_on_completion_retry"]

        self.save(update_fields=update_fields)

    @property
    def is_authenticated(self):
        return bool(self.auth_plugin)

    @property
    def is_completed(self):
        return bool(self.completed_on)

    @transaction.atomic()
    def remove_sensitive_data(self):
        self.bsn = ""
        self.kvk = ""
        self.pseudo = ""
        self.prefill_data = dict()

        steps_qs = self.submissionstep_set.select_related(
            "form_step",
            "form_step__form_definition",
        )
        for submission_step in steps_qs.select_for_update():
            fields = submission_step.form_step.form_definition.sensitive_fields
            removed_data = {key: "" for key in fields}
            submission_step.data.update(removed_data)
            submission_step.save()

            # handle the attachments
            submission_step.attachments.filter(form_key__in=fields).delete()
        self._is_cleaned = True

        if self.co_sign_data:
            # We do keep the representation, as that is used in PDF and confirmation e-mail
            # generation and is usually a label derived from the source fields.
            self.co_sign_data.update(
                {
                    "identifier": "",
                    "fields": {},
                }
            )

        self.save()

    def hash_identifying_attributes(self, save=False):
        """
        Generate a salted hash for each of the identifying attributes.

        Hashes allow us to compare correct values at a later stage, while still
        preventing sensitive data to be available in plain text if the database were
        to leak.

        We use :module:`django.contrib.auth.hashers` for the actual salting and hashing,
        relying on the global Django ``PASSWORD_HASHERS`` setting.
        """
        attrs = [AuthAttribute.bsn, AuthAttribute.kvk, AuthAttribute.pseudo]
        for attr in attrs:
            hashed = get_salted_hash(getattr(self, attr))
            setattr(self, attr, hashed)
        self.auth_attributes_hashed = True
        if save:
            self.save(update_fields=["auth_attributes_hashed", *attrs])

    def load_execution_state(self) -> SubmissionState:
        """
        Retrieve the current execution state of steps from the database.
        """
        if hasattr(self, "_execution_state"):
            return self._execution_state

        form_steps = self.form.formstep_set.select_related("form_definition").order_by(
            "order"
        )
        _submission_steps = self.submissionstep_set.select_related(
            "form_step", "form_step__form_definition"
        )
        submission_steps = {step.form_step: step for step in _submission_steps}

        # build the resulting list - some SubmissionStep instances will probably not exist
        # in the database yet - this is on purpose!
        steps: List[SubmissionStep] = []
        for form_step in form_steps:
            if form_step in submission_steps:
                step = submission_steps[form_step]
            else:
                # there's no known DB record for this, so we create a fresh, unsaved
                # instance and return this
                step = SubmissionStep(
                    # nothing assigned yet, and on next call it'll be a different value
                    # if we rely on the default
                    uuid=None,
                    submission=self,
                    form_step=form_step,
                )
            steps.append(step)

        state = SubmissionState(
            form_steps=list(form_steps),
            submission_steps=steps,
        )
        self._execution_state = state
        return state

    def render_confirmation_page(self) -> str:
        if not (template := self.form.submission_confirmation_template):
            config = GlobalConfiguration.get_solo()
            template = config.submission_confirmation_template

        context_data = {
            # use private variables that can't be accessed in the template data, so that
            # template designers can't call the .delete method, for example. Variables
            # starting with underscores are blocked by the Django template engine.
            "_submission": self,
            "_form": self.form,  # should be the same as self.form
            "public_reference": self.public_registration_reference,
            **self.data,
        }

        rendered_content = Template(template).render(Context(context_data))
        return rendered_content

    @property
    def steps(self) -> List["SubmissionStep"]:
        # fetch the existing DB records for submitted form steps
        submission_state = self.load_execution_state()
        return submission_state.submission_steps

    def get_next_step(self) -> Optional["SubmissionStep"]:
        """
        Determine which is the next step for the current submission.
        """
        submission_state = self.load_execution_state()
        return submission_state.get_next_step()

    def get_last_completed_step(self) -> Optional["SubmissionStep"]:
        """
        Determine which is the next step for the current submission.
        """
        submission_state = self.load_execution_state()
        return submission_state.get_last_completed_step()

    def get_ordered_data_with_component_type(self) -> OrderedDict:
        ordered_data = OrderedDict()
        merged_data = self.get_merged_data()

        # first collect data we have in the same order the components are defined in the form
        for component in filter_printable(self.form.iter_components(recursive=True)):
            key = component["key"]
            value = merged_data.get(key, None)
            component.setdefault("label", key)
            ordered_data[key] = (
                component,
                value,
            )

        return ordered_data

    def get_merged_appointment_data(self) -> Dict[str, Dict[str, Union[str, dict]]]:
        component_config_key_to_appointment_key = {
            "appointments.showProducts": "productIDAndName",
            "appointments.showLocations": "locationIDAndName",
            "appointments.showTimes": "appStartTime",
            "appointments.lastName": "clientLastName",
            "appointments.birthDate": "clientDateOfBirth",
            "appointments.phoneNumber": "clientPhoneNumber",
        }

        merged_data = self.get_merged_data()
        appointment_data = {}

        for component in self.form.iter_components(recursive=True):
            # is this component any of the keys were looking for?
            for (
                component_key,
                appointment_key,
            ) in component_config_key_to_appointment_key.items():
                is_the_right_component = glom(component, component_key, default=False)
                if not is_the_right_component:
                    continue

                # it is the right component, get the value and store it
                appointment_data[appointment_key] = {
                    "label": component["label"],
                    "value": merged_data.get(component["key"]),
                }
                break

        return appointment_data

    def get_merged_data(self) -> dict:
        merged_data = dict()

        for step in self.submissionstep_set.exclude(data=None):
            for key, value in step.data.items():
                if key in merged_data:
                    logger.warning(
                        'Key "%s" was previously in merged_data and will be overwritten by: %s',
                        key,
                        value,
                    )
                merged_data[key] = value

        return merged_data

    data = property(get_merged_data)

    def get_co_signer(self) -> str:
        if not self.co_sign_data:
            return ""
        if not (co_signer := self.co_sign_data.get("representation", "")):
            logger.warning("Incomplete co-sign data for submission %s", self.uuid)
        return co_signer

    def get_attachments(self) -> "SubmissionFileAttachmentQuerySet":
        from .submission_files import SubmissionFileAttachment

        return SubmissionFileAttachment.objects.for_submission(self)

    attachments = property(get_attachments)

    def get_merged_attachments(self) -> Mapping[str, "SubmissionFileAttachment"]:
        if not hasattr(self, "_merged_attachments"):
            self._merged_attachments = self.get_attachments().as_form_dict()
        return self._merged_attachments

    def get_email_confirmation_recipients(self, submitted_data: dict) -> List[str]:
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
        self.price = get_submission_price(self)
        if save:
            self.save(update_fields=["price"])

    @property
    def payment_required(self) -> bool:
        return self.form.payment_required

    @property
    def payment_user_has_paid(self) -> bool:
        # TODO support partial payments
        return self.payments.filter(
            status__in=(PaymentStatus.registered, PaymentStatus.completed)
        ).exists()

    @property
    def payment_registered(self) -> bool:
        # TODO support partial payments
        return self.payments.filter(status=PaymentStatus.registered).exists()

    def get_auth_mode_display(self):
        # compact anonymous display of authentication method
        auth = []
        if self.bsn:
            auth.append("bsn")
        if self.kvk:
            auth.append("kvk")
        if self.pseudo:
            auth.append("pseudo")

        if self.auth_plugin:
            return f"{self.auth_plugin} ({','.join(auth)})"
        else:
            return ""
