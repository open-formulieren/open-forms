import logging
import re
import uuid
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.db import models
from django.template import Context, Template, TemplateSyntaxError
from django.template.loader import get_template
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel

from openforms.forms.constants import AvailabilityOptions
from openforms.forms.models import FormStep
from openforms.utils.fields import StringUUIDField
from openforms.utils.validators import validate_bsn

from .constants import URL_REGEX, RegistrationStatuses

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


class Submission(models.Model):
    """
    Container for submission steps that hold the actual submitted data.
    """

    uuid = StringUUIDField(unique=True, default=uuid.uuid4)
    form = models.ForeignKey("forms.Form", on_delete=models.PROTECT)
    created_on = models.DateTimeField(auto_now_add=True)
    completed_on = models.DateTimeField(blank=True, null=True)
    suspended_on = models.DateTimeField(blank=True, null=True)
    bsn = models.CharField(
        max_length=9, default="", blank=True, validators=(validate_bsn,)
    )
    current_step = models.PositiveIntegerField(default=0)

    # interaction with registration backend
    registration_result = JSONField(
        _("result of backend registration"),
        blank=True,
        null=True,
        help_text=_(
            "Contains data returned by the registration backend while registering the submission data."
        ),
    )
    registration_status = models.CharField(
        _("Backend registration status"),
        max_length=50,
        choices=RegistrationStatuses,
        default=RegistrationStatuses.pending,
        help_text=_("Whether registration in the configured backend was successful."),
    )

    class Meta:
        verbose_name = "Submission"
        verbose_name_plural = "Submissions"

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


class SubmissionStep(models.Model):
    """
    Submission data.

    TODO: This model (and therefore API) allows for the same form step to be
    submitted multiple times. Can be useful for retrieving historical data or
    changes made during filling out the form... but...
    """

    uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    submission = models.ForeignKey("submissions.Submission", on_delete=models.CASCADE)
    form_step = models.ForeignKey("forms.FormStep", on_delete=models.CASCADE)
    data = JSONField(blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "SubmissionStep"
        verbose_name_plural = "SubmissionSteps"
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


class ConfirmationEmailTemplate(models.Model):
    subject = models.CharField(
        max_length=1000, help_text=_("Subject of the email message")
    )
    content = models.TextField(
        help_text=_(
            "The content of the email message, can contain variables that will be "
            "templated form the submitted form data."
        )
    )
    form = models.OneToOneField(
        "forms.Form",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        related_name="confirmation_email_template",
        help_text=_("The form for which this confirmation email template will be used"),
    )
    # email_property_name = models.CharField(
    #     max_length=200,
    #     help_text=_(
    #         "The name of the attribute in the submission data that contains the "
    #         "email address to which the confirmation email will be sent."
    #     ),
    # )

    class Meta:
        verbose_name = _("Confirmation email template")
        verbose_name_plural = _("Confirmation email templates")

    def __str__(self):
        return f"Confirmation email template - {self.form}"

    def render(self, context):
        def replace_urls(match):
            parsed = urlparse(match.group())
            if parsed.netloc in settings.EMAIL_TEMPLATE_URL_WHITELIST:
                return match.group()
            return ""

        default_template = get_template("confirmation_mail.html")
        rendered_content = Template(self.content).render(Context(context))
        stripped = re.sub(URL_REGEX, replace_urls, rendered_content)
        return default_template.render({"body": stripped})

    def clean(self):
        try:
            self.render({})
        except TemplateSyntaxError as e:
            raise ValidationError(e)
        return super().clean()


class SMTPServerConfig(SingletonModel):
    host = models.CharField(
        max_length=1000, blank=True, help_text=_("De host van de SMTP server")
    )
    port = models.IntegerField(
        null=True, blank=True, help_text=_("De port van de SMTP server")
    )
    username = models.CharField(
        max_length=1000, blank=True, help_text=_("De username van de SMTP server")
    )
    password = models.CharField(
        max_length=1000, blank=True, help_text=_("Het password van de SMTP server")
    )
    default_from_email = models.CharField(
        max_length=1000,
        blank=True,
        help_text=_("De afzender waarvan de bevestigingsemails afkomstig zijn"),
        verbose_name=_("Standaard e-mailadres afzender"),
    )

    class Meta:
        verbose_name = _("SMTP Server Configuration")
