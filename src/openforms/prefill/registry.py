from __future__ import annotations

from collections.abc import Iterable

from django.db.models import Count

from openforms.forms.models import Form, FormVariable
from openforms.plugins.registry import BaseRegistry

from .base import BasePlugin


class Registry(BaseRegistry[BasePlugin]):
    """
    A registry for the prefill module plugins.
    """

    module = "prefill"

    def report_plugin_usage(self) -> Iterable[tuple[BasePlugin, int]]:
        qs = (
            FormVariable.objects.exclude(prefill_plugin="")
            .filter(form__in=Form.objects.live())
            .values("prefill_plugin")
            .annotate(count=Count("*"))
        )
        usage_counts: dict[str, int] = {
            item["prefill_plugin"]: item["count"] for item in qs
        }
        for plugin in self:
            yield plugin, usage_counts.get(plugin.identifier, 0)


# Sentinel to provide the default registry. You an easily instantiate another
# :class:`Registry` object to use as dependency injection in tests.
register = Registry()
register.set_as_metric_reporter()
