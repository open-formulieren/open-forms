from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from openforms.forms.models import Form, FormVariable
from openforms.plugins.registry import BaseRegistry

from .base import BasePlugin


class Registry(BaseRegistry[BasePlugin]):
    """
    A registry for the prefill module plugins.
    """

    module = "prefill"

    def report_plugin_usage(self) -> Iterable[tuple[BasePlugin, int, dict[str, str]]]:
        usage_counts: dict[tuple[BasePlugin, str | None], int] = defaultdict(int)

        active_form_variables = FormVariable.objects.exclude(prefill_plugin="").filter(
            form__in=Form.objects.live()
        )

        for form_variable in active_form_variables:
            plugin = self.get(form_variable.prefill_plugin)

            if not plugin:
                continue

            options = getattr(form_variable, "prefill_options", {})

            vendor_hint = plugin.get_vendor_hint(options)

            usage_counts[(plugin, vendor_hint)] += 1

        for plugin in self:
            plugin_usages = {k: v for k, v in usage_counts.items() if k[0] == plugin}

            if not plugin_usages:
                yield plugin, 0, {}
            else:
                for (p, vendor_hint), count in plugin_usages.items():
                    tags = {"openforms.plugin.vendor_hint": vendor_hint} if vendor_hint else {}
                    yield p, count, tags


# Sentinel to provide the default registry. You an easily instantiate another
# :class:`Registry` object to use as dependency injection in tests.
register = Registry()
register.set_as_metric_reporter()
