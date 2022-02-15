import hashlib
import logging
import os.path
import uuid
import warnings
from collections import OrderedDict, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Mapping, Optional, Tuple, Union

from django.core.files.base import ContentFile, File
from django.db import models, transaction
from django.template import Context, Template
from django.template.defaultfilters import date as fmt_date, time as fmt_time, yesno
from django.template.loader import render_to_string
from django.urls import resolve
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_time
from django.utils.formats import localize
from django.utils.translation import gettext, gettext_lazy as _

from celery.result import AsyncResult
from django_better_admin_arrayfield.models.fields import ArrayField
from furl import furl
from glom import glom
from privates.fields import PrivateMediaFileField
from weasyprint import HTML

from openforms.config.models import GlobalConfiguration
from openforms.formio.formatters.service import format_value
from openforms.forms.models import FormStep
from openforms.payments.constants import PaymentStatus
from openforms.utils.files import DeleteFileFieldFilesMixin, DeleteFilesQuerySetMixin
from openforms.utils.validators import (
    AllowedRedirectValidator,
    SerializerValidator,
    validate_bsn,
)

from ..contrib.kvk.validators import validate_kvk
from .constants import RegistrationStatuses
from .pricing import get_submission_price
from .query import SubmissionManager
from .serializers import CoSignDataSerializer

logger = logging.getLogger(__name__)


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


def _get_config_field(field: str) -> str:
    # workaround for when this function is called during migrations and the table
    # hasn't fully migrated yet
    qs = GlobalConfiguration.objects.values_list(field, flat=True)
    return qs.first()


def _get_values(value: Any, filter_func=bool) -> List[Any]:
    """
    Filter a single or multiple value into a list of acceptable values.
    """
    # normalize values into a list
    if not isinstance(value, (list, tuple)):
        value = [value]
    return [item for item in value if filter_func(item)]


def _join_mapped(formatter: callable, value: Any, seperator: str = ", ") -> str:
    # filter and map a single or multiple value into a joined string
    formatted_values = [formatter(x) for x in _get_values(value)]
    return seperator.join(formatted_values)


def get_default_bsn() -> str:
    default_test_bsn = _get_config_field("default_test_bsn")
    return default_test_bsn or ""


def get_default_kvk() -> str:
    default_test_kvk = _get_config_field("default_test_kvk")
    return default_test_kvk or ""


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
        max_length=9,
        default=get_default_bsn,
        blank=True,
        validators=(validate_bsn,),
    )
    kvk = models.CharField(
        _("KvK number"),
        max_length=9,
        default=get_default_kvk,
        blank=True,
        validators=(validate_kvk,),
    )
    pseudo = models.CharField(
        _("Pseudo ID"),
        max_length=64,
        blank=True,
        help_text=_("Pseudo ID provided by authentication with eIDAS"),
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

        enable_formio_formatters = (
            GlobalConfiguration.get_solo().enable_formio_formatters
        )

        # first collect data we have in the same order the components are defined in the form
        for component in self.form.iter_components(recursive=True):
            key = component["key"]
            if key in merged_data:
                if enable_formio_formatters:
                    component.setdefault("label", key)
                    ordered_data[key] = (
                        component,
                        merged_data[key],
                    )
                else:
                    ordered_data[key] = {
                        "type": component["type"],
                        "value": merged_data[key],
                        "label": component.get("label", key),
                        "multiple": component.get("multiple", False),
                        # The select component has the values/labels nested in a 'data' field
                        "values": component.get("values")
                        or component.get("data", {}).get("values"),
                        # appointments stuff...
                        "appointments": component.get("appointments", {}),
                    }
        # now append remaining data that doesn't have a matching component
        for key, value in merged_data.items():
            if key not in ordered_data:
                if enable_formio_formatters:
                    ordered_data[key] = (
                        {
                            "type": "unknown component",
                            "label": key,
                        },
                        merged_data[key],
                    )
                else:
                    ordered_data[key] = {
                        "type": "unknown component",
                        "value": merged_data[key],
                        "label": key,
                    }

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

    @staticmethod
    def _get_value_label(possible_values: list, value: str) -> str:
        for possible_value in possible_values:
            if possible_value["value"] == value:
                return possible_value["label"]
        # TODO what if value is not a string? shouldn't it be passed through something to covert for display?
        return value

    def get_printable_data(
        self,
        limit_keys_to: Optional[List[str]] = None,
        use_merged_data_fallback=False,
    ) -> List[Tuple[str, str]]:
        printable_data = []
        attachment_data = self.get_merged_attachments()
        merged_data = self.get_merged_data() if use_merged_data_fallback else {}

        for key, info in self.get_ordered_data_with_component_type().items():
            if limit_keys_to and key not in limit_keys_to:
                continue

            if GlobalConfiguration.get_solo().enable_formio_formatters:
                info, value = info
                label = info["label"]
                printable_data.append((label, format_value(info, value)))
            else:
                warnings.warn(
                    "Formatting without using the formio formatters registry is deprecated. "
                    "Please consider concentrating all future improvements/fixes there.",
                    DeprecationWarning,
                )

                label = info["label"]
                multiple = info.get("multiple", False)
                if info["type"] == "file":
                    files = attachment_data.get(key)
                    if files:
                        value = _("attachment: %s") % (
                            ", ".join(file.get_display_name() for file in files)
                        )
                    # FIXME: ugly workaround to patch the demo, this should be fixed properly
                    elif use_merged_data_fallback:
                        value = merged_data.get(key)
                    else:
                        value = _("empty")

                elif info["type"] == "date" or (
                    info.get("appointments", {}).get("showDates", False)
                ):
                    value = _join_mapped(
                        lambda v: fmt_date(parse_date(v)), info["value"]
                    )

                elif info["type"] == "time" or (
                    appointment_time := info.get("appointments", {}).get(
                        "showTimes", False
                    )
                ):
                    _parse_time = (
                        datetime.fromisoformat if appointment_time else parse_time
                    )
                    # strip off the seconds
                    value = _join_mapped(
                        lambda v: fmt_time(_parse_time(v)), info["value"]
                    )

                elif info["type"] == "selectboxes":
                    selected_values: Dict[str, bool] = info["value"]
                    selected_labels = [
                        entry["label"]
                        for entry in info["values"]
                        if selected_values.get(entry["value"])
                    ]
                    value = ", ".join(selected_labels)

                elif info["type"] == "number" or info["type"] == "currency":
                    if multiple:
                        value = _join_mapped(lambda v: localize(v), info["value"])
                    else:
                        value = localize(info["value"])
                elif info["type"] == "checkbox":
                    value = yesno(info["value"])
                elif type(info["value"]) is dict:
                    printable_value = info["value"]
                    if "name" in printable_value:
                        value = printable_value["name"]
                    else:
                        printable_value = list(printable_value.values())[0]
                        logger.warning(
                            'Key "%s" is a dict with unknown values (%s). The first value "%s" was stored.',
                            key,
                            info["value"],
                            printable_value,
                        )
                        value = printable_value["name"]
                else:
                    printable_value = info["value"]
                    if values := info.get("values"):
                        value = printable_value
                        if not multiple:
                            value = [value]

                        def _format(val):
                            return self._get_value_label(values, val)

                        # Case in which each value has a label (for example select and radio components)
                        printable_value = _join_mapped(
                            lambda v: self._get_value_label(values, v), value
                        )

                    # more here? like getComponentValue() in the SDK?
                    value = printable_value

                printable_data.append((label, value))
        # finally, check if we have co-sign information to append
        if self.co_sign_data:
            if not (co_signer := self.co_sign_data.get("representation", "")):
                logger.warning("Incomplete co-sign data for submission %s", self.uuid)
            printable_data.append((gettext("Co-signed by"), co_signer))

        return printable_data

    def get_attachments(self) -> "SubmissionFileAttachmentQuerySet":
        return SubmissionFileAttachment.objects.for_submission(self)

    attachments = property(get_attachments)

    def get_merged_attachments(self) -> Mapping[str, "SubmissionFileAttachment"]:
        return self.get_attachments().as_form_dict()

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


class SubmissionStep(models.Model):
    """
    Submission data.

    TODO: This model (and therefore API) allows for the same form step to be
    submitted multiple times. Can be useful for retrieving historical data or
    changes made during filling out the form... but...
    """

    uuid = models.UUIDField(_("UUID"), unique=True, default=uuid.uuid4)
    submission = models.ForeignKey("submissions.Submission", on_delete=models.CASCADE)
    form_step = models.ForeignKey("forms.FormStep", on_delete=models.CASCADE)
    data = models.JSONField(_("data"), blank=True, null=True)
    created_on = models.DateTimeField(_("created on"), auto_now_add=True)
    modified = models.DateTimeField(_("modified on"), auto_now=True)

    # can be modified by logic evaluations/checks
    _can_submit = True
    _is_applicable = True

    class Meta:
        verbose_name = _("Submission step")
        verbose_name_plural = _("Submission steps")
        unique_together = (("submission", "form_step"),)

    def __str__(self):
        return f"SubmissionStep {self.pk}: Submission {self.submission_id} submitted on {self.created_on}"

    @property
    def completed(self) -> bool:
        # TODO: should check that all the data for the form definition is present?
        # and validates?
        # For now - if it's been saved, we assume that was because it was completed
        return bool(self.pk and self.data is not None)

    @property
    def can_submit(self) -> bool:
        return self._can_submit

    @property
    def is_applicable(self) -> bool:
        return self._is_applicable


class SubmissionReport(models.Model):
    title = models.CharField(
        verbose_name=_("title"),
        max_length=200,
        help_text=_("Title of the submission report"),
    )
    content = PrivateMediaFileField(
        verbose_name=_("content"),
        upload_to="submission-reports/%Y/%m/%d",
        help_text=_("Content of the submission report"),
    )
    submission = models.OneToOneField(
        to="Submission",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name=_("submission"),
        help_text=_("Submission the report is about."),
        related_name="report",
    )
    last_accessed = models.DateTimeField(
        verbose_name=_("last accessed"),
        blank=True,
        null=True,
        help_text=_(
            "When the submission report was last accessed. This value is "
            "updated when the report is downloaded."
        ),
    )
    task_id = models.CharField(
        verbose_name=_("task id"),
        max_length=200,
        help_text=_(
            "ID of the celery task creating the content of the report. This is "
            "used to check the generation status."
        ),
        blank=True,
    )

    class Meta:
        verbose_name = _("submission report")
        verbose_name_plural = _("submission reports")

    def __str__(self):
        return self.title

    def generate_submission_report_pdf(self) -> str:
        """
        Generate the submission report as a PDF.

        :return: string with the HTML used for the PDF generation, so that contents
          can be tested.
        """
        form = self.submission.form
        printable_data = self.submission.get_printable_data()

        html_report = render_to_string(
            "report/submission_report.html",
            context={
                "form": form,
                "submission_data": printable_data,
                "submission": self.submission,
            },
        )

        html_object = HTML(string=html_report)
        pdf_report = html_object.write_pdf()

        self.content = ContentFile(
            content=pdf_report,
            name=f"{form.name}.pdf",  # Takes care of replacing spaces with underscores
        )
        self.save()
        return html_report

    def get_celery_task(self) -> Optional[AsyncResult]:
        if not self.task_id:
            return

        return AsyncResult(id=self.task_id)


def fmt_upload_to(prefix, instance, filename):
    name, ext = os.path.splitext(filename)
    return "{p}/{d}/{u}{e}".format(
        p=prefix, d=date.today().strftime("%Y/%m/%d"), u=instance.uuid, e=ext
    )


def temporary_file_upload_to(instance, filename):
    return fmt_upload_to("temporary-uploads", instance, filename)


def submission_file_upload_to(instance, filename):
    return fmt_upload_to("submission-uploads", instance, filename)


class TemporaryFileUploadQuerySet(DeleteFilesQuerySetMixin, models.QuerySet):
    def select_prune(self, age: timedelta):
        return self.filter(created_on__lt=timezone.now() - age)


class TemporaryFileUpload(DeleteFileFieldFilesMixin, models.Model):
    uuid = models.UUIDField(_("UUID"), unique=True, default=uuid.uuid4)
    content = PrivateMediaFileField(
        verbose_name=_("content"),
        upload_to=temporary_file_upload_to,
        help_text=_("content of the file attachment."),
    )
    file_name = models.CharField(_("original name"), max_length=255)
    content_type = models.CharField(_("content type"), max_length=255)
    # store the file size to not have to do disk IO to get the file size
    file_size = models.PositiveIntegerField(
        _("file size"),
        default=0,
        help_text=_("Size in bytes of the uploaded file."),
    )
    created_on = models.DateTimeField(_("created on"), auto_now_add=True)

    objects = TemporaryFileUploadQuerySet.as_manager()

    class Meta:
        verbose_name = _("temporary file upload")
        verbose_name_plural = _("temporary file uploads")


class SubmissionFileAttachmentQuerySet(DeleteFilesQuerySetMixin, models.QuerySet):
    def for_submission(self, submission: Submission):
        return self.filter(submission_step__submission=submission)

    def as_form_dict(self) -> Mapping[str, List["SubmissionFileAttachment"]]:
        files = defaultdict(list)
        for file in self:
            files[file.form_key].append(file)
        return dict(files)


class SubmissionFileAttachmentManager(models.Manager):
    def create_from_upload(
        self,
        submission_step: SubmissionStep,
        form_key: str,
        upload: TemporaryFileUpload,
        file_name: Optional[str] = None,
    ) -> Tuple["SubmissionFileAttachment", bool]:
        try:
            return (
                self.get(
                    submission_step=submission_step,
                    temporary_file=upload,
                    form_key=form_key,
                ),
                False,
            )
        except self.model.DoesNotExist:
            return (
                self.create(
                    submission_step=submission_step,
                    temporary_file=upload,
                    form_key=form_key,
                    # wrap in File() so it will be physically copied
                    content=File(upload.content, name=upload.file_name),
                    content_type=upload.content_type,
                    original_name=upload.file_name,
                    file_name=file_name,
                ),
                True,
            )


class SubmissionFileAttachment(DeleteFileFieldFilesMixin, models.Model):
    uuid = models.UUIDField(_("UUID"), unique=True, default=uuid.uuid4)
    submission_step = models.ForeignKey(
        to="SubmissionStep",
        on_delete=models.CASCADE,
        verbose_name=_("submission"),
        help_text=_("Submission step the file is attached to."),
        related_name="attachments",
    )
    # TODO OneToOne?
    temporary_file = models.ForeignKey(
        to="TemporaryFileUpload",
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("temporary file"),
        help_text=_("Temporary upload this file is sourced to."),
        related_name="attachments",
    )
    form_key = models.CharField(_("form component key"), max_length=255)

    content = PrivateMediaFileField(
        verbose_name=_("content"),
        upload_to=submission_file_upload_to,
        help_text=_("Content of the submission file attachment."),
    )
    file_name = models.CharField(
        _("file name"), max_length=255, help_text=_("reformatted file name"), blank=True
    )
    original_name = models.CharField(
        _("original name"), max_length=255, help_text=_("original uploaded file name")
    )
    content_type = models.CharField(_("content type"), max_length=255)
    created_on = models.DateTimeField(_("created on"), auto_now_add=True)

    objects = SubmissionFileAttachmentManager.from_queryset(
        SubmissionFileAttachmentQuerySet
    )()

    class Meta:
        verbose_name = _("submission file attachment")
        verbose_name_plural = _("submission file attachments")
        # see https://docs.djangoproject.com/en/2.2/topics/db/managers/#using-managers-for-related-object-access
        base_manager_name = "objects"

    def get_display_name(self):
        return self.file_name or self.original_name

    def get_format(self):
        return os.path.splitext(self.get_display_name())[1].lstrip(".")

    @property
    def content_hash(self) -> str:
        """
        Calculate the sha256 hash of the content.

        MD5 is fast, but has known collisions, so we use sha256 instead.
        """
        chunk_size = 8192
        sha256 = hashlib.sha256()
        with self.content.open(mode="rb") as file_content:
            while chunk := file_content.read(chunk_size):
                sha256.update(chunk)
        return sha256.hexdigest()
