from __future__ import annotations

from collections.abc import Iterable

from django.db.models import Count, F

from openforms.plugins.registry import BaseRegistry

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

    def report_plugin_usage(self) -> Iterable[tuple[BasePlugin, int]]:
        from openforms.forms.models import Form

        qs = (
            Form.objects.live()
            .values(plugin=F("registration_backends__backend"))
            .values("plugin")
            .annotate(count=Count("*"))
        )
        usage_counts: dict[str, int] = {item["plugin"]: item["count"] for item in qs}
        for plugin in self:
            yield plugin, usage_counts.get(plugin.identifier, 0)


# Sentinel to provide the default registry. You an easily instantiate another
# :class:`Registry` object to use as dependency injection in tests.
register = Registry()
register.set_as_metric_reporter()
