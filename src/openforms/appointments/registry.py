from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from openforms.forms.constants import FormTypeChoices
from openforms.plugins.registry import (
    VENDOR_HINT_METRIC_LABEL,
    BaseRegistry,
    PluginUsageReport,
)

if TYPE_CHECKING:
    pass


class Registry(BaseRegistry["BasePlugin"]):
    """
    A registry for appointments module plugins.
    """

    module = "appointments"

    def report_plugin_usage(self) -> Iterable[PluginUsageReport]:
        from openforms.forms.models import Form

        from .models import AppointmentsConfig

        config = AppointmentsConfig.get_solo()
        num_appointment_forms = (
            Form.objects.live().filter(type=FormTypeChoices.appointment).count()
        )
        for plugin in self:
            in_use = num_appointment_forms > 0 and config.plugin == plugin.identifier
            yield (
                plugin,
                num_appointment_forms if in_use else 0,
                {VENDOR_HINT_METRIC_LABEL: plugin.identifier},
            )


register = Registry()
register.set_as_metric_reporter()
