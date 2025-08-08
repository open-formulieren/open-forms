from collections.abc import Collection

from django.db.models import Count

from opentelemetry import metrics

from .models import Submission

meter = metrics.get_meter("openforms.submissions")

start_counter = meter.create_counter(
    "submission.starts",
    description="Amount of form submissions started (via the API).",
    unit="1",  # unitless count
)

suspension_counter = meter.create_counter(
    "submission.supensions",
    description="Amount of form submissions suspended/paused.",
    unit="1",  # unitless count
)

completion_counter = meter.create_counter(
    "submission.completions",
    unit="1",  # unitless count
    description="The number of form submissions completed by end users.",
)

step_saved_counter = meter.create_counter(
    "submission.step_saves",
    unit="1",  # unitless count
    description="The number of steps saved to the database.",
)


def count_submissions(
    options: metrics.CallbackOptions,
) -> Collection[metrics.Observation]:
    counts_by_form_and_status = (
        Submission.objects.annotate_stage()
        .values("form__name", "stage")
        .annotate(count=Count("pk"))
    )
    return [
        metrics.Observation(
            value=agg["count"],
            attributes={
                "form.name": agg["form__name"],
                "type": agg["stage"],
                "scope": "global",
            },
        )
        for agg in counts_by_form_and_status
    ]


meter.create_observable_gauge(
    name="submission_count",
    description="The number of submissions.",
    unit="",  # no unit so that the _ratio suffix is not added
    callbacks=[count_submissions],
)
