from __future__ import annotations

from typing import TYPE_CHECKING

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

if TYPE_CHECKING:
    from .models import Submission  # noqa


class SubmissionQuerySet(models.QuerySet["Submission"]):
    def annotate_removal_fields(
        self, limit_field: str, method_field: str = ""
    ) -> SubmissionQuerySet:
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
