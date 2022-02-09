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
from openforms.utils.files import get_file_field_names

if TYPE_CHECKING:  # pragma: nocover
    from .models import Submission


class SubmissionQuerySet(models.QuerySet):
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


class BaseSubmissionManager(models.Manager):
    @transaction.atomic
    def copy(
        self,
        original: "Submission",
        fields=("form", "form_url", "bsn", "kvk", "pseudo", "auth_plugin"),
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


SubmissionManager = BaseSubmissionManager.from_queryset(SubmissionQuerySet)


class DeleteFilesQuerySet(models.QuerySet):
    def _delete_filefields_storage(self) -> None:
        # TODO: we might want to wrap this in transaction.on_commit, see also
        # DeleteFileFieldFilesMixin
        file_field_names = get_file_field_names(self.model)
        del_query = self._chain()

        # iterator in case we're dealing with large querysets and memory could be
        # exhausted
        for obj in del_query.iterator():
            for name in file_field_names:
                filefield = getattr(obj, name)
                filefield.delete(save=False)

    def _raw_delete(self, using):
        # raw delete is called in fast_deletes
        self._delete_filefields_storage()
        return super()._raw_delete(using)

    _raw_delete.alters_data = True

    def delete(self):
        self._delete_filefields_storage()
        return super().delete()

    delete.alters_data = True
    delete.queryset_only = True
