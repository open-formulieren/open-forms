import itertools
from datetime import timedelta

from django.db.models import F, Q
from django.utils import timezone

import structlog

from openforms.celery import app
from openforms.submissions.constants import Stages
from openforms.submissions.models import Submission

from .constants import RemovalMethods

logger = structlog.stdlib.get_logger(__name__)

TIME_SINCE_CREATION_DELTA = F("removal_limit") * timedelta(days=1)


@app.task(ignore_result=True)
def delete_submissions():
    log = logger.bind(action="data_removal.delete_submissions")
    log.debug("start")

    base_qs = Submission.objects.annotate_stage()
    filters = {
        "removal_method": RemovalMethods.delete_permanently,
        "time_since_creation__gt": TIME_SINCE_CREATION_DELTA,
    }
    # we want to keep the submissions which have an appointment connected and it's still
    # valid. This keeps the cancel endpoint available until the expiry date.
    future_appointments_filter = Q(
        form__is_appointment=True, appointment__datetime__gte=timezone.now()
    )

    successful_submissions_to_delete = base_qs.annotate_removal_fields(
        "successful_submissions_removal_limit",
        method_field="successful_submissions_removal_method",
    ).filter(
        Q(**filters) & ~future_appointments_filter,
        stage=Stages.successfully_completed,
    )

    log.info(
        "delete_submissions",
        kind="successful",
        amount=successful_submissions_to_delete.count(),
    )
    successful_submissions_to_delete.delete()

    incomplete_submissions_to_delete = base_qs.annotate_removal_fields(
        "incomplete_submissions_removal_limit",
        method_field="incomplete_submissions_removal_method",
    ).filter(**filters, stage=Stages.incomplete)
    log.info(
        "delete_submissions",
        kind="incomplete",
        amount=incomplete_submissions_to_delete.count(),
    )
    incomplete_submissions_to_delete.delete()

    errored_submissions_to_delete = base_qs.annotate_removal_fields(
        "errored_submissions_removal_limit",
        method_field="errored_submissions_removal_method",
    ).filter(**filters, stage=Stages.errored)
    log.info(
        "delete_submissions",
        kind="errored",
        amount=errored_submissions_to_delete.count(),
    )
    errored_submissions_to_delete.delete()

    other_submissions_to_delete = Submission.objects.annotate_removal_fields(
        "all_submissions_removal_limit"
    ).filter(
        ~future_appointments_filter,
        time_since_creation__gt=TIME_SINCE_CREATION_DELTA,
    )
    log.info(
        "delete_submissions", kind="other", amount=other_submissions_to_delete.count()
    )
    other_submissions_to_delete.delete()


@app.task(ignore_result=True)
def make_sensitive_data_anonymous() -> None:
    log = logger.bind(action="data_removal.make_sensitive_data_anonymous")
    log.debug("start")

    base_qs = Submission.objects.annotate_stage().filter(_is_cleaned=False)
    filters = {
        "removal_method": RemovalMethods.make_anonymous,
        "time_since_creation__gt": TIME_SINCE_CREATION_DELTA,
    }

    successful_submissions = base_qs.annotate_removal_fields(
        "successful_submissions_removal_limit",
        method_field="successful_submissions_removal_method",
    ).filter(**filters, stage=Stages.successfully_completed)

    incomplete_submissions = base_qs.annotate_removal_fields(
        "incomplete_submissions_removal_limit",
        method_field="incomplete_submissions_removal_method",
    ).filter(**filters, stage=Stages.incomplete)

    errored_submissions = base_qs.annotate_removal_fields(
        "errored_submissions_removal_limit",
        method_field="errored_submissions_removal_method",
    ).filter(**filters, stage=Stages.errored)

    log.info(
        "anonymize_submissions",
        kind="successful",
        amount=successful_submissions.count(),
    )
    log.info(
        "anonymize_submissions",
        kind="incomplete",
        amount=incomplete_submissions.count(),
    )
    log.info(
        "anonymize_submissions", kind="errored", amount=errored_submissions.count()
    )

    for submission in itertools.chain(
        successful_submissions.iterator(),
        incomplete_submissions.iterator(),
        errored_submissions.iterator(),
    ):
        submission.remove_sensitive_data()
