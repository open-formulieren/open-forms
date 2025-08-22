from collections import Counter
from collections.abc import Collection
from uuid import UUID

from django.db.models import Count, Prefetch, Q

from opentelemetry import metrics

from .models import Form, FormStep

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


def count_component_usage(
    options: metrics.CallbackOptions,
) -> Collection[metrics.Observation]:
    """
    Count how often a component type is used in each form.

    The metric makes it possible to show how many (of each type of) components are
    used in a form. Some derived aggregations also provide insights into absolute
    usage statistics of components.
    """
    counter = Counter[tuple[UUID, str]]()  # [form uuid, component_type] key
    uuid_to_name_map: dict[UUID, str] = {}
    forms = (
        Form.objects.live()
        .exclude(is_appointment=True)
        .prefetch_related(
            Prefetch(
                "formstep_set",
                queryset=FormStep.objects.select_related("form_definition"),
            )
        )
    )

    for form in forms:
        uuid_to_name_map[form.uuid] = form.name
        for step in form.formstep_set.all():
            for component in step.iter_components(recursive=True):
                counter[(form.uuid, component["type"])] += 1

    return [
        metrics.Observation(
            amount,
            attributes={
                "scope": "global",
                "form.uuid": str(form_uuid),
                "form.name": uuid_to_name_map[form_uuid],
                "type": component_type,
            },
        )
        for (form_uuid, component_type), amount in counter.items()
    ]


meter.create_observable_gauge(
    name="form_component_count",
    description="The number of forms in the database.",
    unit="",  # no unit so that the _ratio suffix is not added
    callbacks=[count_component_usage],
)
