import logging
import uuid
from dataclasses import dataclass
from typing import List, Optional

from django.contrib.postgres.fields import JSONField
from django.core.files.base import ContentFile
from django.db import models
from django.shortcuts import render
from django.template import Context, Template
from django.utils.translation import gettext as _

from celery.result import AsyncResult
from privates.fields import PrivateMediaFileField
from weasyprint import HTML

from openforms.config.models import GlobalConfiguration
from openforms.emails.utils import sanitize_content
from openforms.forms.constants import AvailabilityOptions
from openforms.forms.models import FormStep
from openforms.utils.fields import StringUUIDField
from openforms.utils.validators import validate_bsn

from ..contrib.kvk.validators import validate_kvk
from ..utils.helpers import get_flattened_components
from .constants import RegistrationStatuses

logger = logging.getLogger(__name__)


@dataclass
class SubmissionState:
    form_steps: List[FormStep]
    submission_steps: List["SubmissionStep"]

    def get_next_step(self) -> Optional["SubmissionStep"]:
        """
        Determine the next logical step to fill out.

        The next step is the step:
        - after the last submitted step
        - that is available

        It does not consider "skipped" steps.

        If there are no more steps, the result is None.
        """
        completed_steps = sorted(
            [step for step in self.submission_steps if step.completed],
            key=lambda step: step.modified,
        )
        offset = (
            0
            if not completed_steps
            else self.submission_steps.index(completed_steps[-1])
        )
        candidates = (
            step
            for step in self.submission_steps[offset:]
            if not step.completed and step.available
        )
        return next(candidates, None)


def get_default_bsn() -> str:
    config = GlobalConfiguration.get_solo()
    return config.default_test_bsn if config.default_test_bsn else ""


def get_default_kvk() -> str:
    config = GlobalConfiguration.get_solo()
    return config.default_test_kvk if config.default_test_kvk else ""


class Submission(models.Model):
    """
    Container for submission steps that hold the actual submitted data.
    """

    uuid = StringUUIDField(_("UUID"), unique=True, default=uuid.uuid4)
    form = models.ForeignKey("forms.Form", on_delete=models.PROTECT)
    created_on = models.DateTimeField(_("created on"), auto_now_add=True)
    completed_on = models.DateTimeField(_("completed on"), blank=True, null=True)
    suspended_on = models.DateTimeField(_("suspended on"), blank=True, null=True)
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
    current_step = models.PositiveIntegerField(_("current step"), default=0)

    # interaction with registration backend
    registration_result = JSONField(
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

    class Meta:
        verbose_name = _("Submission")
        verbose_name_plural = _("Submissions")

    def __str__(self):
        return _("{pk} - started on {started}").format(
            pk=self.pk or _("(unsaved)"),
            started=self.created_on or _("(no timestamp yet)"),
        )

    def refresh_from_db(self, *args, **kwargs):
        super().refresh_from_db(*args, **kwargs)
        if hasattr(self, "_execution_state"):
            del self._execution_state

    @property
    def is_completed(self):
        return bool(self.completed_on)

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

        rendered_content = Template(template).render(Context(self.data))

        return sanitize_content(rendered_content)

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

    def get_merged_data_with_component_type(self) -> dict:
        merged_data = dict()

        for step in self.submissionstep_set.exclude(data=None).select_related(
            "form_step"
        ):
            components = step.form_step.form_definition.configuration["components"]
            flattened_components = get_flattened_components(components)
            component_key_to_type = dict()
            for component in flattened_components:
                component_key_to_type[component["key"]] = component["type"]
            for key, value in step.data.items():
                if key in merged_data:
                    logger.warning(
                        "%s was previously in merged_data and will be overwritten by %s",
                        key,
                        value,
                    )

                merged_data[key] = {
                    "type": component_key_to_type.get(key, "unknown component"),
                    "value": value,
                }

        return merged_data

    def get_merged_data(self) -> dict:
        merged_data = dict()

        for step in self.submissionstep_set.exclude(data=None):
            for key, value in step.data.items():
                if key in merged_data:
                    logger.warning(
                        "%s was previously in merged_data and will be overwritten by %s",
                        key,
                        value,
                    )
                merged_data[key] = value

        return merged_data

    data = property(get_merged_data)
    data_with_component_type = property(get_merged_data_with_component_type)

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
    data = JSONField(_("data"), blank=True, null=True)
    created_on = models.DateTimeField(_("created on"), auto_now_add=True)
    modified = models.DateTimeField(_("modified on"), auto_now=True)

    class Meta:
        verbose_name = _("Submission step")
        verbose_name_plural = _("Submission steps")
        unique_together = (("submission", "form_step"),)

    def __str__(self):
        return f"SubmissionStep {self.pk}: Submission {self.submission_id} submitted on {self.created_on}"

    @property
    def available(self) -> bool:
        strat = self.form_step.availability_strategy
        if strat == AvailabilityOptions.always:
            return True

        elif strat == AvailabilityOptions.after_previous_step:
            submission_state = self.submission.load_execution_state()
            index = submission_state.form_steps.index(self.form_step)
            if index == 0:  # there is no previous step...
                logger.warning(
                    "First step is misconfigured, should always be available. Form step: %d",
                    self.form_step_id,
                )
                return False

            # check if the previous available step was completed
            candidates = [
                step
                for step in submission_state.submission_steps[:index]
                if step.available
            ]
            if candidates and candidates[-1].completed:
                return True
            return False
        else:
            raise NotImplementedError(f"Unknown strategy: {strat}")

    @property
    def completed(self) -> bool:
        # TODO: should check that all the data for the form definition is present?
        # and validates?
        # For now - if it's been saved, we assume that was because it was completed
        return bool(self.pk and self.data is not None)


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
    submission = models.ForeignKey(
        to="Submission",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name=_("submission"),
        help_text=_("Submission related to the report"),
    )
    last_accessed = models.DateTimeField(
        verbose_name=_("last accessed"),
        blank=True,
        null=True,
        help_text=_("When the submission report was last accessed"),
    )
    task_id = models.CharField(
        verbose_name=_("task id"),
        max_length=200,
        help_text=_("ID of the celery task creating the content of the report."),
        blank=True,
    )

    class Meta:
        verbose_name = _("submission report")
        verbose_name_plural = _("submission reports")

    def __str__(self):
        return self.title

    def generate_submission_report_pdf(self) -> None:
        form = self.submission.form
        submission_data = self.submission.get_merged_data()

        html_report = render(
            request=None,
            template_name="report/submission_report.html",
            context={
                "form": form,
                "submission_data": submission_data,
                "submission": self.submission,
            },
        ).content.decode("utf8")

        html_object = HTML(string=html_report)
        pdf_report = html_object.write_pdf()

        self.content = ContentFile(
            content=pdf_report,
            name=f"{form.name}.pdf",  # Takes care of replacing spaces with underscores
        )
        self.save()

    def get_celery_task(self) -> Optional[AsyncResult]:
        if not self.task_id:
            return

        return AsyncResult(id=self.task_id)
