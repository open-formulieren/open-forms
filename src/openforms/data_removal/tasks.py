import itertools
import logging
from datetime import timedelta

from django.db.models import F

from openforms.celery import app
from openforms.submissions.constants import RegistrationStatuses
from openforms.submissions.models import Submission

from .constants import RemovalMethods

logger = logging.getLogger(__name__)


@app.task(ignore_result=True)
def delete_submissions():
    logger.debug("Deleting submissions")

    successful_submissions_to_delete = Submission.objects.annotate_removal_fields(
        "successful_submissions_removal_limit",
        method_field="successful_submissions_removal_method",
    ).filter(
        registration_status=RegistrationStatuses.success,
        removal_method=RemovalMethods.delete_permanently,
        time_since_creation__gt=(timedelta(days=1) * F("removal_limit")),
    )
    logger.info(
        "Deleting %s successful submissions", successful_submissions_to_delete.count()
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
    logger.info(
        "Deleting %s incomplete submissions", incomplete_submissions_to_delete.count()
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

    logger.info(
        "Deleting %s errored submissions", errored_submissions_to_delete.count()
    )
    errored_submissions_to_delete.delete()

    other_submissions_to_delete = Submission.objects.annotate_removal_fields(
        "all_submissions_removal_limit"
    ).filter(
        time_since_creation__gt=(timedelta(days=1) * F("removal_limit")),
    )
    logger.info(
        "Deleting %s other submissions regardless of registration",
        other_submissions_to_delete.count(),
    )
    other_submissions_to_delete.delete()


@app.task(ignore_result=True)
def make_sensitive_data_anonymous() -> None:
    logger.debug("Making sensitive submission data anonymous")

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

    logger.info(
        "Anonymizing %s successful submissions",
        successful_submissions.count(),
    )
    logger.info(
        "anonymizing %s incomplete submissions",
        incomplete_submissions.count(),
    )
    logger.info(
        "anonymizing %s errored submissions",
        errored_submissions.count(),
    )

    for submission in itertools.chain(
        successful_submissions.iterator(),
        incomplete_submissions.iterator(),
        errored_submissions.iterator(),
    ):
        submission.remove_sensitive_data()
