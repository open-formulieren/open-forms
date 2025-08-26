from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import TYPE_CHECKING

from django.db.models import Count, F

import structlog
from rest_framework.request import Request

from openforms.plugins.registry import BaseRegistry

if TYPE_CHECKING:
    from openforms.forms.models import Form

    from .base import BasePlugin, LoginInfo  # noqa: F401

logger = structlog.stdlib.get_logger(__name__)


def _iter_plugin_ids(form: Form | None, registry: Registry) -> Iterator[str]:
    if form is not None:
        yield from form.auth_backends.values_list("backend", flat=True)
    else:
        for plugin in registry.iter_enabled_plugins():
            yield plugin.identifier


class Registry(BaseRegistry["BasePlugin"]):
    """
    A registry for the authentication module plugins.
    """

    module = "authentication"

    def get_options(
        self,
        request: Request,
        form: Form | None = None,
        is_for_cosign: bool = False,
    ) -> list[LoginInfo]:
        options: list[LoginInfo] = []

        # return empty list for forms without cosign
        if is_for_cosign:
            if not form or not form.has_cosign_enabled:
                return []

        for plugin_id in _iter_plugin_ids(form, self):
            if plugin_id not in self._registry:
                logger.warning(
                    "ignore_unknown_plugin",
                    plugin_id=plugin_id,
                    form_uuid=str(form.uuid) if form else None,
                )
                continue
            plugin = self._registry[plugin_id]
            info = plugin.get_login_info(request, form, is_for_cosign)
            options.append(info)
        return options

    def report_plugin_usage(self) -> Iterable[tuple[BasePlugin, int]]:
        from openforms.forms.models import Form

        qs = (
            Form.objects.live()
            .values(plugin=F("auth_backends__backend"))
            .values("plugin")
            .annotate(count=Count("*"))
        )
        usage_counts: dict[str, int] = {item["plugin"]: item["count"] for item in qs}
        for plugin in self:
            yield plugin, usage_counts.get(plugin.identifier, 0)


# Sentinel to provide the default registry. You can easily instantiate another
# :class:`Registry` object to use as dependency injection in tests.
register = Registry()
register.set_as_metric_reporter()
