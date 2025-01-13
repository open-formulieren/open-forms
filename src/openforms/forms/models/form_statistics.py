from __future__ import annotations

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.formats import localize
from django.utils.timezone import localtime
from django.utils.translation import gettext_lazy as _

from openforms.logging import logevent
from openforms.logging.models import TimelineLogProxy


class FormStatistics(models.Model):
    form = models.OneToOneField(
        "forms.Form",
        verbose_name=_("form"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    form_name = models.CharField(
        verbose_name=_("form name"),
        max_length=150,
        help_text=_(
            "The name of the submitted form. This is saved separately in case of form deletion."
        ),
    )
    submission_count = models.PositiveIntegerField(
        verbose_name=_("Submission count"),
        default=0,
        help_text=_("The number of the submitted forms."),
    )
    first_submission = models.DateTimeField(
        verbose_name=_("first submission"),
        help_text=_("Date and time of the first submitted form."),
        auto_now_add=True,
    )
    last_submission = models.DateTimeField(
        verbose_name=_("last submission"),
        help_text=_("Date and time of the last submitted form."),
    )

    class Meta:
        verbose_name = _("form statistics")
        verbose_name_plural = _("form statistics")

    def __str__(self):
        return _("{form_name} last submitted on {last_submitted}").format(
            form_name=self.form_name,
            last_submitted=localize(localtime(self.last_submission)),
        )


class FormStatisticsV2Manager(models.Manager["FormSubmissionStatisticsV2"]):
    def get_queryset(self):
        from openforms.submissions.models import Submission

        qs = super().get_queryset()
        submission_content_type = ContentType.objects.get_for_model(Submission)
        # only consider form_submit_success events, recorded by
        # openforms.submissions.api.mixins.SubmissionCompletionMixin._complete_submission
        return qs.filter(
            content_type=submission_content_type,
            extra_data__log_event=logevent.FORM_SUBMIT_SUCCESS_EVENT,
        )


class FormSubmissionStatisticsV2(TimelineLogProxy):
    """
    Display aggregated statistics in the admin based on log records.

    The model kind of abused to make use of standard Django admin functions for the
    list display and filter fields, rather than writing an entirely custom admin view.

    NOTE:: if/when we get Prometheus metrics, that would be an even better source to
    retrieve the data of statistics.
    """

    # aggregation fields
    form_name: str
    submission_count: int

    objects = FormStatisticsV2Manager()

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        proxy = True
        verbose_name = _("form submission statistics")
        verbose_name_plural = _("form submission statistics")
