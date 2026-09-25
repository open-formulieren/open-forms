from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator, Mapping, MutableMapping
from typing import TYPE_CHECKING

from django.db import OperationalError

from flags.state import flag_enabled
from opentelemetry import metrics
from opentelemetry.util.types import AttributeValue

from .constants import UNIQUE_ID_MAX_LENGTH

if TYPE_CHECKING:
    from .plugin import AbstractBasePlugin


meter = metrics.get_meter("openforms.plugins")

VENDOR_HINT_METRIC_LABEL = "openforms.plugin.vendor_hint"

type MetricLabels = Mapping[str, AttributeValue]
type PluginUsageReport = (
    tuple[AbstractBasePlugin, int] | tuple[AbstractBasePlugin, int, MetricLabels]
)


class BaseRegistry[PluginT: AbstractBasePlugin]:
    """
    Base registry class for plugin modules.
    """

    module: str = ""
    """
    The name of the 'module' this registry belongs to.

    The module is the logical group of extra functionality in Open Forms on top of the
    core functionality.
    """
    _registry: dict[str, PluginT]

    def __init__(self):
        self._registry = {}

    def __call__(
        self, unique_identifier: str
    ) -> Callable[[type[PluginT]], type[PluginT]]:
        if len(unique_identifier) > UNIQUE_ID_MAX_LENGTH:
            raise ValueError(
                f"The unique identifier '{unique_identifier}' is longer than "
                f"{UNIQUE_ID_MAX_LENGTH} characters."
            )

        def decorator(plugin_cls: type[PluginT]) -> type[PluginT]:
            if unique_identifier in self._registry:
                raise ValueError(
                    f"The unique identifier '{unique_identifier}' is already present "
                    "in the registry."
                )

            plugin = plugin_cls(identifier=unique_identifier)
            self.check_plugin(plugin)
            plugin.registry = self
            self._registry[unique_identifier] = plugin
            return plugin_cls

        return decorator

    def check_plugin(self, plugin: PluginT):
        # validation hook
        pass

    def __iter__(self):
        return iter(self._registry.values())

    def __getitem__(self, key: str) -> PluginT:
        return self._registry[key]

    def __contains__(self, key: str) -> bool:
        return key in self._registry

    def iter_enabled_plugins(self) -> Iterator[PluginT]:
        try:
            with_demos = flag_enabled("ENABLE_DEMO_PLUGINS")
            enable_all = False
        except OperationalError:
            # fix CI trying to access non-existing database or table to generate OAS
            with_demos = False
            enable_all = True

        for plugin in self:
            is_demo = getattr(plugin, "is_demo_plugin", False)
            if is_demo and not with_demos:
                continue
            elif enable_all or plugin.is_enabled:  # plugins are enabled by default
                yield plugin

    def items(self):
        return iter(self._registry.items())

    def get_choices(self):
        return [(p.identifier, p.get_label()) for p in self.iter_enabled_plugins()]

    def set_as_metric_reporter(self) -> None:
        """
        Mark the instance as the one that will produce metrics for telemetry.

        Only one instance (the singleton, typically) can be used to report metrics
        without affecting other registry instances created for testing.
        """
        assert self.module
        if self.module in module_registers:
            raise ValueError(
                f"Registry {module_registers[self.module]!r} is already configured "
                "as metrics producer."
            )
        module_registers[self.module] = self

    def report_plugin_usage(self) -> Iterable[PluginUsageReport]:
        """
        Introspect the registered plugins and report how often each one is used.

        This is called by the plugin usage metric exporter to get insight in how often
        plugins are used. Can include extra metric labels.

        .. note:: This method will be invoked periodically in a background thread. Pay
           attention to DB query optimization to minimize system load.
        """
        return ()


module_registers: MutableMapping[str, BaseRegistry] = {}


def record_plugin_usage(
    options: metrics.CallbackOptions,
) -> Iterator[metrics.Observation]:
    for module, register in module_registers.items():
        for usage_item in register.report_plugin_usage():
            if len(usage_item) == 3:
                plugin, times_used, extra_attributes = usage_item
            else:
                plugin, times_used = usage_item
                extra_attributes = {}

            attributes: dict[str, AttributeValue] = {
                "scope": "global",
                "openforms.plugin.module": module,
                "openforms.plugin.identifier": plugin.identifier,
                "openforms.plugin.is_enabled": plugin.is_enabled,
                "openforms.plugin.is_demo": plugin.is_demo_plugin,
            }
            if extra_attributes:
                attributes.update(extra_attributes)

            yield metrics.Observation(
                value=times_used,
                attributes=attributes,
            )


meter.create_observable_gauge(
    name="openforms.plugin.usage_count",
    description="The usage counts of module plugins.",
    unit="",  # no unit so that the _ratio suffix is not added
    callbacks=[record_plugin_usage],
)
