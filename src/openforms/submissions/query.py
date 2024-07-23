from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from django.db import models, transaction
from django.db.models import (
    Case,
    CharField,
    DateTimeField,
    DurationField,
    ExpressionWrapper,
    F,
    IntegerField,
    Value,
    When,
)
from django.utils import timezone

from openforms.config.models import GlobalConfiguration
from openforms.logging import logevent
from openforms.payments.models import SubmissionPayment

if TYPE_CHECKING:
    from .models import Submission


class SubmissionQuerySet(models.QuerySet["Submission"]):
    def annotate_removal_fields(
        self, limit_field: str, method_field: str = ""
    ) -> "SubmissionQuerySet":
        config = GlobalConfiguration.get_solo()
        annotation = self.annotate(
            removal_limit=Case(
                When(
                    **{f"form__{limit_field}": None},
                    then=Value(getattr(config, limit_field)),
                ),
                default=F(f"form__{limit_field}"),
                output_field=IntegerField(),
            ),
            time_since_creation=ExpressionWrapper(
                Value(timezone.now(), DateTimeField()) - F("created_on"),
                output_field=DurationField(),
            ),
        )

        if method_field:
            annotation = annotation.annotate(
                removal_method=Case(
                    When(
                        **{f"form__{method_field}": ""},
                        then=Value(getattr(config, method_field)),
                    ),
                    default=F(f"form__{method_field}"),
                    output_field=CharField(),
                ),
            )

        return annotation


class SubmissionManager(models.Manager.from_queryset(SubmissionQuerySet)):
    @transaction.atomic
    def copy(
        self,
        original: "Submission",
        fields=(
            "form",
            "form_url",
        ),
    ) -> "Submission":
        """
        Copy an existing submission into a new, cleaned submission record.

        The new submission has the meta fields cleared, but existing submitted data
        copied over.

        :arg submission: An existing :class:`Submission` instance
        :arg fields: iterable of model field names to copy
        """
        from .models import SubmissionStep

        new_instance = self.create(
            previous_submission=original,  # store the reference from where it was copied
            **{field: getattr(original, field) for field in fields},
        )
        if hasattr(original, "auth_info"):
            new_auth_info = copy.deepcopy(original.auth_info)
            new_auth_info.pk = None
            new_auth_info.submission = new_instance
            new_auth_info.save()

        new_steps = []
        related_steps_manager = original.submissionstep_set
        for step in related_steps_manager.all():
            new_steps.append(
                SubmissionStep(
                    submission=new_instance,
                    form_step=step.form_step,
                    data=step.data,
                )
            )
        related_steps_manager.bulk_create(new_steps)

        if original.payment_required and original.payment_user_has_paid:
            submission_payment = SubmissionPayment.objects.get(submission=original)
            submission_payment.submission = new_instance
            submission_payment.save()

            logevent.payment_transfer_to_new_submission(
                submission_payment=submission_payment,
                old_submission=original,
                new_submission=new_instance,
            )

        return new_instance
