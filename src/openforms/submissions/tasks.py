import itertools
import logging
from datetime import timedelta

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

from ..celery import app
from ..config.models import GlobalConfiguration
from ..submissions.constants import RemovalMethods
from .constants import RegistrationStatuses
from .models import Submission

logger = logging.getLogger(__name__)


@app.task
def delete_submissions():
    logger.debug("Deleting submissions")

    config = GlobalConfiguration.get_solo()

    successful_submissions_to_delete = Submission.objects.annotate(
        removal_method=Case(
            When(
                form__successful_submissions_removal_method="",
                then=Value(config.successful_submissions_removal_method),
            ),
            default=F("form__successful_submissions_removal_method"),
            output_field=CharField(),
        ),
        removal_limit=Case(
            When(
                form__successful_submissions_removal_limit=None,
                then=Value(config.successful_submissions_removal_limit),
            ),
            default=F("form__successful_submissions_removal_limit"),
            output_field=IntegerField(),
        ),
        time_since_creation=ExpressionWrapper(
            Value(timezone.now(), DateTimeField()) - F("created_on"),
            output_field=DurationField(),
        ),
    ).filter(
        registration_status=RegistrationStatuses.success,
        removal_method=RemovalMethods.delete_permanently,
        time_since_creation__gt=(timedelta(days=1) * F("removal_limit")),
    )
    logger.info(
        "Deleting %s successful submissions", successful_submissions_to_delete.count()
    )
    successful_submissions_to_delete.delete()

    incomplete_submissions_to_delete = Submission.objects.annotate(
        removal_method=Case(
            When(
                form__incomplete_submissions_removal_method="",
                then=Value(config.incomplete_submissions_removal_method),
            ),
            default=F("form__incomplete_submissions_removal_method"),
            output_field=CharField(),
        ),
        removal_limit=Case(
            When(
                form__incomplete_submissions_removal_limit=None,
                then=Value(config.incomplete_submissions_removal_limit),
            ),
            default=F("form__incomplete_submissions_removal_limit"),
            output_field=IntegerField(),
        ),
        time_since_creation=ExpressionWrapper(
            Value(timezone.now(), DateTimeField()) - F("created_on"),
            output_field=DurationField(),
        ),
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

    errored_submissions_to_delete = Submission.objects.annotate(
        removal_method=Case(
            When(
                form__errored_submissions_removal_method="",
                then=Value(config.errored_submissions_removal_method),
            ),
            default=F("form__errored_submissions_removal_method"),
            output_field=CharField(),
        ),
        removal_limit=Case(
            When(
                form__errored_submissions_removal_limit=None,
                then=Value(config.errored_submissions_removal_limit),
            ),
            default=F("form__errored_submissions_removal_limit"),
            output_field=IntegerField(),
        ),
        time_since_creation=ExpressionWrapper(
            Value(timezone.now(), DateTimeField()) - F("created_on"),
            output_field=DurationField(),
        ),
    ).filter(
        registration_status=RegistrationStatuses.failed,
        removal_method=RemovalMethods.delete_permanently,
        time_since_creation__gt=(timedelta(days=1) * F("removal_limit")),
    )

    logger.info(
        "Deleting %s errored submissions", errored_submissions_to_delete.count()
    )
    errored_submissions_to_delete.delete()

    other_submissions_to_delete = Submission.objects.annotate(
        removal_limit=Case(
            When(
                form__all_submissions_removal_limit=None,
                then=Value(config.all_submissions_removal_limit),
            ),
            default=F("form__all_submissions_removal_limit"),
            output_field=IntegerField(),
        ),
        time_since_creation=ExpressionWrapper(
            Value(timezone.now(), DateTimeField()) - F("created_on"),
            output_field=DurationField(),
        ),
    ).filter(
        time_since_creation__gt=(timedelta(days=1) * F("removal_limit")),
    )
    logger.info(
        "Deleting %s other submissions regardless of registration",
        other_submissions_to_delete.count(),
    )
    other_submissions_to_delete.delete()


@app.task
def make_sensitive_data_anonymous() -> None:
    logger.debug("Making sensitive submission data anonymous")

    config = GlobalConfiguration.get_solo()

    successful_submissions = Submission.objects.annotate(
        removal_method=Case(
            When(
                form__successful_submissions_removal_method="",
                then=Value(config.successful_submissions_removal_method),
            ),
            default=F("form__successful_submissions_removal_method"),
            output_field=CharField(),
        ),
        removal_limit=Case(
            When(
                form__successful_submissions_removal_limit=None,
                then=Value(config.successful_submissions_removal_limit),
            ),
            default=F("form__successful_submissions_removal_limit"),
            output_field=IntegerField(),
        ),
        time_since_creation=ExpressionWrapper(
            Value(timezone.now(), DateTimeField()) - F("created_on"),
            output_field=DurationField(),
        ),
    ).filter(
        registration_status=RegistrationStatuses.success,
        removal_method=RemovalMethods.make_anonymous,
        time_since_creation__gt=(timedelta(days=1) * F("removal_limit")),
        _is_cleaned=False,
    )

    incomplete_submissions = Submission.objects.annotate(
        removal_method=Case(
            When(
                form__incomplete_submissions_removal_method="",
                then=Value(config.incomplete_submissions_removal_method),
            ),
            default=F("form__incomplete_submissions_removal_method"),
            output_field=CharField(),
        ),
        removal_limit=Case(
            When(
                form__incomplete_submissions_removal_limit=None,
                then=Value(config.incomplete_submissions_removal_limit),
            ),
            default=F("form__incomplete_submissions_removal_limit"),
            output_field=IntegerField(),
        ),
        time_since_creation=ExpressionWrapper(
            Value(timezone.now(), DateTimeField()) - F("created_on"),
            output_field=DurationField(),
        ),
    ).filter(
        registration_status__in=[
            RegistrationStatuses.pending,
            RegistrationStatuses.in_progress,
        ],
        removal_method=RemovalMethods.make_anonymous,
        time_since_creation__gt=(timedelta(days=1) * F("removal_limit")),
        _is_cleaned=False,
    )

    errored_submissions = Submission.objects.annotate(
        removal_method=Case(
            When(
                form__errored_submissions_removal_method="",
                then=Value(config.errored_submissions_removal_method),
            ),
            default=F("form__errored_submissions_removal_method"),
            output_field=CharField(),
        ),
        removal_limit=Case(
            When(
                form__errored_submissions_removal_limit=None,
                then=Value(config.errored_submissions_removal_limit),
            ),
            default=F("form__errored_submissions_removal_limit"),
            output_field=IntegerField(),
        ),
        time_since_creation=ExpressionWrapper(
            Value(timezone.now(), DateTimeField()) - F("created_on"),
            output_field=DurationField(),
        ),
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
