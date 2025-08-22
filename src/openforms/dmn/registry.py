from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from openforms.forms.constants import LogicActionTypes
from openforms.forms.models import Form, FormLogic
from openforms.plugins.registry import BaseRegistry

from .base import BasePlugin


class Registry(BaseRegistry[BasePlugin]):
    """
    A registry for decision modelling/evaluation module plugins.
    """

    module = "dmn"

    def report_plugin_usage(self) -> Iterable[tuple[BasePlugin, int]]:
        logic_rules = FormLogic.objects.filter(
            form__in=Form.objects.live(),
            actions__contains=[{"action": {"type": LogicActionTypes.evaluate_dmn}}],
        )
        usage_counts = defaultdict[str, int](lambda: 0)
        for rule in logic_rules:
            for action in rule.actions:
                if action["action"]["type"] != LogicActionTypes.evaluate_dmn:
                    continue
                plugin_id = action["action"]["config"]["plugin_id"]
                usage_counts[plugin_id] += 1

        for plugin in self:
            yield plugin, usage_counts[plugin.identifier]


# Sentinel to provide the default registry. You an easily instantiate another
# :class:`Registry` object to use as dependency injection in tests.
register = Registry()
register.set_as_metric_reporter()
