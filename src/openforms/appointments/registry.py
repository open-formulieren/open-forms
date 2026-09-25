from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from openforms.forms.constants import FormTypeChoices
from openforms.plugins.registry import BaseRegistry

if TYPE_CHECKING:
    from .base import BasePlugin


class Registry(BaseRegistry["BasePlugin"]):
    """
    A registry for appointments module plugins.
    """

    module = "appointments"

    def report_plugin_usage(self) -> Iterable[tuple[BasePlugin, int, dict[str, str]]]:
        from openforms.forms.models import Form

        from .models import AppointmentsConfig

        config = AppointmentsConfig.get_solo()
        num_appointment_forms = (
            Form.objects.live().filter(type=FormTypeChoices.appointment).count()
        )
        for plugin in self:
            in_use = num_appointment_forms > 0 and config.plugin == plugin.identifier

            if "jcc" in plugin.identifier.lower():
                vendor = "jcc_rest"
            elif "qmatic" in plugin.identifier.lower():
                vendor = "qmatic"
            elif "demo" in plugin.identifier.lower():
                vendor = "demo"
            else:
                vendor = plugin.identifier

            yield plugin, num_appointment_forms if in_use else 0, {"openforms.plugin.vendor_hint": vendor}


register = Registry()
register.set_as_metric_reporter()
