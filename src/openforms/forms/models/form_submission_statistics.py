from __future__ import annotations

from datetime import datetime

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from openforms.logging.constants import FORM_SUBMIT_SUCCESS_EVENT
from openforms.logging.models import TimelineLogProxy


class FormStatisticsV2Manager(models.Manager["FormSubmissionStatistics"]):
    def get_queryset(self):
        from openforms.submissions.models import Submission

        qs = super().get_queryset()
        submission_content_type = ContentType.objects.get_for_model(Submission)
        # only consider form_submit_success events, recorded by
        # openforms.submissions.api.mixins.SubmissionCompletionMixin._complete_submission
        return qs.filter(
            content_type=submission_content_type,
            extra_data__log_event=FORM_SUBMIT_SUCCESS_EVENT,
        )


class FormSubmissionStatistics(TimelineLogProxy):
    """
    Display aggregated statistics in the admin based on log records.

    The model kind of abused to make use of standard Django admin functions for the
    list display and filter fields, rather than writing an entirely custom admin view.

    NOTE:: if/when we get Prometheus metrics, that would be an even better source to
    retrieve the data of statistics.
    """

    # annotation fields
    form_name: str
    submission_count: int
    first_submission: datetime
    last_submission: datetime

    objects = FormStatisticsV2Manager()

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        proxy = True
        verbose_name = _("form submission statistics")
        verbose_name_plural = _("form submission statistics")
