from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from openforms.plugins.registry import VENDOR_HINT_METRIC_LABEL, BaseRegistry

from .base import BasePlugin


class Registry(BaseRegistry[BasePlugin]):
    """
    A registry for registrations module plugins.
    """

    module = "registrations"

    def check_plugin(self, plugin: BasePlugin):
        if not plugin.configuration_options:
            raise ValueError(
                "Please specify 'configuration_options' attribute for plugin class."
            )

    def report_plugin_usage(self) -> Iterable[tuple[BasePlugin, int, dict[str, str]]]:
        from openforms.forms.models import Form

        usage_counts: dict[tuple[BasePlugin, str | None], int] = defaultdict(int)

        for form in Form.objects.live().prefetch_related("registration_backends"):
            for backend in form.registration_backends.all():
                if backend.backend not in self:
                    continue
                plugin = self[backend.backend]

                options = getattr(
                    backend, "configuration", getattr(backend, "options", {})
                )

                vendor_hint = plugin.get_vendor_hint(options)

                usage_counts[(plugin, vendor_hint)] += 1

        for plugin in self:
            plugin_usages = {k: v for k, v in usage_counts.items() if k[0] == plugin}

            if not plugin_usages:
                yield plugin, 0, {}
            else:
                for (p, vendor_hint), count in plugin_usages.items():
                    tags = (
                        {VENDOR_HINT_METRIC_LABEL: vendor_hint} if vendor_hint else {}
                    )
                    yield p, count, tags


# Sentinel to provide the default registry. You an easily instantiate another
# :class:`Registry` object to use as dependency injection in tests.
register = Registry()
register.set_as_metric_reporter()
