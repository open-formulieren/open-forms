from datetime import date, datetime, time

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.timezone import make_aware
from django.utils.translation import gettext_lazy as _

from tablib import Dataset

from openforms.logging.constants import (
    FORM_SUBMIT_SUCCESS_EVENT,
    REGISTRATION_SUCCESS_EVENT,
)
from openforms.logging.models import TimelineLogProxy
from openforms.submissions.models import Submission

from .models import Form


def export_registration_statistics(
    start_date: date,
    end_date: date,
    limit_to_forms: models.QuerySet[Form] | None = None,
    event: str = REGISTRATION_SUCCESS_EVENT,
) -> Dataset:
    """
    Export the form registration statistics to a tablib Dataset.

    The export retrieves log records within the specified date range (closed interval,
    [start_date, end_date]), optionally filtering them down to a set of forms. Only log
    records for successful registration are considered.

    :arg start_date: include log records starting from this date (midnight, in the local
      timezone).
    :arg end_date: include log records until (and including) this date. Log record up to
      midnight (in the local timezone) the next day are included, i.e.
      ``$date, 23:59:59 999999us``.
    :arg limit_to_forms: A queryset of forms to limit the export to. If not provided or
      ``None`` is given, all forms are included.
    """
    title_mappings = {
        REGISTRATION_SUCCESS_EVENT: _(
            "Successfully registered submissions between {start} and {end}"
        ),
        FORM_SUBMIT_SUCCESS_EVENT: _(
            "Successfully completed submissions between {start} and {end}"
        ),
    }

    dataset = Dataset(
        headers=(
            _("Public reference"),
            _("Form name (public)"),
            _("Form name (internal)"),
            _("Submitted on"),
            _("Registered on"),
        ),
        title=title_mappings[event].format(
            start=start_date.isoformat(),
            end=end_date.isoformat(),
        ),
    )

    _start_date = make_aware(datetime.combine(start_date, time.min))
    _end_date = make_aware(datetime.combine(end_date, time.max))

    log_records = TimelineLogProxy.objects.filter(
        content_type=ContentType.objects.get_for_model(Submission),
        timestamp__gte=_start_date,
        timestamp__lte=_end_date,
        # see openforms.logging.adapter for the data structure of the extra_data
        # JSONField
        extra_data__log_event=event,
    ).order_by("timestamp")

    if limit_to_forms:
        form_ids = list(limit_to_forms.values_list("pk", flat=True))
        log_records = log_records.filter(extra_data__form_id__in=form_ids)

    for record in log_records.iterator():
        extra_data = record.extra_data
        # GFKs will be broken when the submissions are pruned, so prefer extracting
        # information from the extra_data snapshot
        submission: Submission | None = record.content_object
        dataset.append(
            (
                # public reference
                extra_data.get(
                    "public_reference",
                    (
                        submission.public_registration_reference
                        if submission
                        else "-unknown-"
                    ),
                ),
                # public form name
                extra_data.get(
                    "form_name", submission.form.name if submission else "-unknown-"
                ),
                # internal form name
                extra_data.get(
                    "internal_form_name",
                    submission.form.internal_name if submission else "-unknown-",
                ),
                # when the user submitted the form
                extra_data.get(
                    "submitted_on",
                    submission.completed_on.isoformat() if submission else None,
                ),
                # when the registration succeeeded - this must be close to when it was logged
                record.timestamp.isoformat(),
            )
        )

    return dataset
