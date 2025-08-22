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

upload_file_size = meter.create_histogram(
    name="attachment.file_size",
    unit="bytes",
    description="Size of a single uploaded attachment.",
    explicit_bucket_boundaries_advisory=(
        0,  # 0 bytes
        1024,  # 1 KiB
        100 * 1024,  # 100 KiB
        1024**2,  # 1 MiB
        10 * 1024**2,  # 10 MiB
        100 * 1024**2,  # 100 MiB
        1024**3,  # 1 GiB
    ),
)

attachments_per_submission = meter.create_histogram(
    name="submission.attachments_per_submission",
    unit="1",
    description="Number of attachments per completed form submission.",
    explicit_bucket_boundaries_advisory=(0, 5, 10, 20, 50, 100),
)
