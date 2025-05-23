import itertools
from datetime import timedelta

from django.db.models import F

import structlog

from openforms.celery import app
from openforms.submissions.constants import RegistrationStatuses
from openforms.submissions.models import Submission

from .constants import RemovalMethods

logger = structlog.stdlib.get_logger(__name__)


@app.task(ignore_result=True)
def delete_submissions():
    log = logger.bind(action="data_removal.delete_submissions")
    log.debug("start")

    successful_submissions_to_delete = Submission.objects.annotate_removal_fields(
        "successful_submissions_removal_limit",
        method_field="successful_submissions_removal_method",
    ).filter(
        registration_status=RegistrationStatuses.success,
        removal_method=RemovalMethods.delete_permanently,
        time_since_creation__gt=(timedelta(days=1) * F("removal_limit")),
    )
    log.info(
        "delete_submissions",
        kind="successful",
        amount=successful_submissions_to_delete.count(),
    )
    successful_submissions_to_delete.delete()

    incomplete_submissions_to_delete = Submission.objects.annotate_removal_fields(
        "incomplete_submissions_removal_limit",
        method_field="incomplete_submissions_removal_method",
    ).filter(
        registration_status__in=[
            RegistrationStatuses.pending,
            RegistrationStatuses.in_progress,
        ],
        removal_method=RemovalMethods.delete_permanently,
        time_since_creation__gt=(timedelta(days=1) * F("removal_limit")),
    )
    log.info(
        "delete_submissions",
        kind="incomplete",
        amount=incomplete_submissions_to_delete.count(),
    )
    incomplete_submissions_to_delete.delete()

    errored_submissions_to_delete = Submission.objects.annotate_removal_fields(
        "errored_submissions_removal_limit",
        method_field="errored_submissions_removal_method",
    ).filter(
        registration_status=RegistrationStatuses.failed,
        removal_method=RemovalMethods.delete_permanently,
        time_since_creation__gt=(timedelta(days=1) * F("removal_limit")),
    )
    log.info(
        "delete_submissions",
        kind="errored",
        amount=errored_submissions_to_delete.count(),
    )
    errored_submissions_to_delete.delete()

    other_submissions_to_delete = Submission.objects.annotate_removal_fields(
        "all_submissions_removal_limit"
    ).filter(
        time_since_creation__gt=(timedelta(days=1) * F("removal_limit")),
    )
    log.info(
        "delete_submissions", kind="other", amount=other_submissions_to_delete.count()
    )
    other_submissions_to_delete.delete()


@app.task(ignore_result=True)
def make_sensitive_data_anonymous() -> None:
    log = logger.bind(action="data_removal.make_sensitive_data_anonymous")
    log.debug("start")

    successful_submissions = Submission.objects.annotate_removal_fields(
        "successful_submissions_removal_limit",
        method_field="successful_submissions_removal_method",
    ).filter(
        registration_status=RegistrationStatuses.success,
        removal_method=RemovalMethods.make_anonymous,
        time_since_creation__gt=(timedelta(days=1) * F("removal_limit")),
        _is_cleaned=False,
    )

    incomplete_submissions = Submission.objects.annotate_removal_fields(
        "incomplete_submissions_removal_limit",
        method_field="incomplete_submissions_removal_method",
    ).filter(
        registration_status__in=[
            RegistrationStatuses.pending,
            RegistrationStatuses.in_progress,
        ],
        removal_method=RemovalMethods.make_anonymous,
        time_since_creation__gt=(timedelta(days=1) * F("removal_limit")),
        _is_cleaned=False,
    )

    errored_submissions = Submission.objects.annotate_removal_fields(
        "errored_submissions_removal_limit",
        method_field="errored_submissions_removal_method",
    ).filter(
        registration_status=RegistrationStatuses.failed,
        removal_method=RemovalMethods.make_anonymous,
        time_since_creation__gt=(timedelta(days=1) * F("removal_limit")),
        _is_cleaned=False,
    )

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
