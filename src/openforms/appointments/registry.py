from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from openforms.plugins.registry import BaseRegistry

if TYPE_CHECKING:
    from .base import BasePlugin


class Registry(BaseRegistry["BasePlugin"]):
    """
    A registry for appointments module plugins.
    """

    module = "appointments"

    def report_plugin_usage(self) -> Iterable[tuple[BasePlugin, int]]:
        from openforms.forms.models import Form

        from .models import AppointmentsConfig

        config = AppointmentsConfig.get_solo()
        num_appointment_forms = Form.objects.live().filter(is_appointment=True).count()
        for plugin in self:
            in_use = num_appointment_forms > 0 and config.plugin == plugin.identifier
            yield plugin, num_appointment_forms if in_use else 0


register = Registry()
register.set_as_metric_reporter()
