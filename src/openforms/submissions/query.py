from __future__ import annotations

from typing import TYPE_CHECKING, Self

from django.db import models
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

from .constants import RegistrationStatuses, Stages

if TYPE_CHECKING:
    from .models import Submission  # noqa


class SubmissionQuerySet(models.QuerySet["Submission"]):
    if TYPE_CHECKING:

        @classmethod
        def as_manager(cls) -> SubmissionsManagerType: ...

    def annotate_removal_fields(self, limit_field: str, method_field: str = "") -> Self:
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

    def annotate_stage(self) -> Self:
        """
        Label each submissions with its lifecycle stage.
        """
        stage_case_when = Case(
            When(
                registration_status=RegistrationStatuses.success,
                then=Value(Stages.successfully_completed),
            ),
            When(
                registration_status__in=(
                    RegistrationStatuses.pending,  # the default for newly created
                    RegistrationStatuses.in_progress,  # picked up, but processing
                ),
                then=Value(Stages.incomplete),
            ),
            When(
                registration_status=RegistrationStatuses.failed,
                then=Value(Stages.errored),
            ),
            default=Value(Stages.other),
        )
        return self.annotate(stage=stage_case_when)


# Purely used for static type checking.
class SubmissionsManagerType(models.Manager["Submission"]):
    def annotate_removal_fields(
        self, limit_field: str, method_field: str = ""
    ) -> SubmissionQuerySet: ...

    def annotate_stage(self) -> SubmissionQuerySet: ...
