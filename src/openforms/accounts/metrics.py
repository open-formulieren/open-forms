from collections.abc import Collection

from django.db.models import Count, Q

from opentelemetry import metrics

from .models import User

meter = metrics.get_meter("openforms.accounts")


def count_users(options: metrics.CallbackOptions) -> Collection[metrics.Observation]:
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
    name="openforms.auth.user_count",
    description="The number of application users in the database.",
    unit=r"{user}",  # no unit so that the _ratio suffix is not added
    callbacks=[count_users],
)

logins = meter.create_counter(
    "openforms.auth.logins",
    unit="1",  # unitless count
    description="The number of successful user logins.",
)

logouts = meter.create_counter(
    "openforms.auth.logouts",
    unit="1",  # unitless count
    description="The number of user logouts.",
)

login_failures = meter.create_counter(
    "openforms.auth.login_failures",
    unit="1",  # unitless count
    description="The number of failed logins by users, including the admin.",
)

user_lockouts = meter.create_counter(
    "openforms.auth.user_lockouts",
    unit="1",  # unitless count
    description="The number of user lockouts because of failed logins.",
)
