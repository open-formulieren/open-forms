from collections.abc import Sequence

from django.db.models import Count, Q

from opentelemetry import metrics

from .models import User

meter = metrics.get_meter("openforms.accounts")


def count_users(options: metrics.CallbackOptions) -> Sequence[metrics.Observation]:
    counts: dict[str, int] = User.objects.aggregate(
        total=Count("id"),
        staff=Count("id", filter=Q(is_staff=True)),
        superuser=Count("id", filter=Q(is_superuser=True)),
    )
    return (
        metrics.Observation(
            counts["total"],
            {"scope": "global", "type": "all"},
        ),
        metrics.Observation(
            counts["staff"],
            {"scope": "global", "type": "staff"},
        ),
        metrics.Observation(
            counts["superuser"],
            {"scope": "global", "type": "superuser"},
        ),
    )


meter.create_observable_gauge(
    name="user_count",
    description="The number of application users in the database.",
    unit="1",
    callbacks=[count_users],
)
