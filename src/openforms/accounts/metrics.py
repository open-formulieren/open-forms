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

logins = meter.create_counter(
    "auth.logins",
    unit="1",  # unitless count
    description="The number of succesful user logins.",
)

logouts = meter.create_counter(
    "auth.logouts",
    unit="1",  # unitless count
    description="The number of user logouts.",
)

login_failures = meter.create_counter(
    "auth.login_failures",
    unit="1",  # unitless count
    description="The number of failed logins by users, including the admin.",
)

user_lockouts = meter.create_counter(
    "auth.user_lockouts",
    unit="1",  # unitless count
    description="The number of user lockouts because of failed logins.",
)
