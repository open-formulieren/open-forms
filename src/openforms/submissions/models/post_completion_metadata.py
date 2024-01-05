from django.db import models
from django.db.models import Q, UniqueConstraint
from django.utils.translation import gettext_lazy as _

from django_jsonform.models.fields import ArrayField

from openforms.submissions.constants import PostSubmissionEvents


class PostCompletionMetadata(models.Model):
    submission = models.ForeignKey(
        to="Submission",
        on_delete=models.CASCADE,
        verbose_name=_("submission"),
        help_text=_("Submission to which the result belongs to."),
    )
    tasks_ids = ArrayField(
        base_field=models.CharField(
            _("celery task ID"),
            max_length=255,
            blank=True,
        ),
        default=list,
        verbose_name=_("task IDs"),
        blank=True,
        help_text=_(
            "Celery task IDs of the tasks queued once a post submission event happens."
        ),
    )
    created_on = models.DateTimeField(_("created on"), auto_now_add=True)
    trigger_event = models.CharField(
        _("created by"),
        help_text=_("Which event scheduled these tasks."),
        choices=PostSubmissionEvents.choices,
        max_length=100,
    )

    class Meta:
        verbose_name = _("post completion metadata")
        verbose_name_plural = _("post completion metadata")
        constraints = [
            UniqueConstraint(
                fields=["submission"],
                condition=Q(trigger_event=PostSubmissionEvents.on_completion),
                name="unique_on_completion_event",
            )
        ]

    def __str__(self):
        return f'{self.submission.public_registration_reference}: {", ".join(self.tasks_ids)}'
