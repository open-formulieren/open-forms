from collections.abc import Collection

from django.db.models import Count, Q

from opentelemetry import metrics

from .models import Form

meter = metrics.get_meter("openforms.forms")


def count_forms(options: metrics.CallbackOptions) -> Collection[metrics.Observation]:
    counts: dict[str, int] = Form.objects.aggregate(
        total=Count("id", filter=Q(_is_deleted=False)),
        live=Count("id", filter=Q(_is_deleted=False, active=True)),
        translation_enabled=Count(
            "id", filter=Q(_is_deleted=False, translation_enabled=True)
        ),
        is_appointment=Count("id", filter=Q(_is_deleted=False, is_appointment=True)),
        trash=Count("id", filter=Q(_is_deleted=True)),
    )
    return [
        metrics.Observation(
            amount,
            attributes={
                "scope": "global",
                "type": kind,
            },
        )
        for kind, amount in counts.items()
    ]


meter.create_observable_gauge(
    name="form_count",
    description="The number of forms in the database.",
    unit="",  # no unit so that the _ratio suffix is not added
    callbacks=[count_forms],
)
