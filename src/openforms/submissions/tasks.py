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
from ..config.constants import RemovalMethods
from ..config.models import GlobalConfiguration
from .constants import RegistrationStatuses
from .models import Submission

logger = logging.getLogger(__name__)


@app.task
def delete_submissions():
    logger.debug("Deleting submissions")

    config = GlobalConfiguration.get_solo()

    Submission.objects.annotate(
        removal_method=Case(
            When(
                form__successful_submissions_removal_method=None,
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
    ).delete()

    Submission.objects.annotate(
        removal_method=Case(
            When(
                form__incomplete_submissions_removal_method=None,
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
    ).delete()

    Submission.objects.annotate(
        removal_method=Case(
            When(
                form__errored_submissions_removal_method=None,
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
    ).delete()

    Submission.objects.annotate(
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
    ).delete()


@app.task
def make_sensitive_data_anonymous() -> None:
    logger.debug("Making sensitive submission data anonymous")

    config = GlobalConfiguration.get_solo()

    successful_submissions = Submission.objects.annotate(
        removal_method=Case(
            When(
                form__successful_submissions_removal_method=None,
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
    )

    incomplete_submissions = Submission.objects.annotate(
        removal_method=Case(
            When(
                form__incomplete_submissions_removal_method=None,
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
    )

    errored_submissions = Submission.objects.annotate(
        removal_method=Case(
            When(
                form__errored_submissions_removal_method=None,
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
    )

    for submission in (
        list(successful_submissions)
        + list(incomplete_submissions)
        + list(errored_submissions)
    ):
        if submission.has_sensitive_information:
            submission.remove_sensitive_data()
