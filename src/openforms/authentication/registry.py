from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Iterator
from typing import TYPE_CHECKING

import structlog
from rest_framework.request import Request

from openforms.plugins.registry import VENDOR_HINT_METRIC_LABEL, BaseRegistry

if TYPE_CHECKING:
    from openforms.forms.models import Form

    from .base import BasePlugin, LoginInfo

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
        if is_for_cosign and (not form or not form.has_cosign_enabled):
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

    def report_plugin_usage(self) -> Iterable[tuple[BasePlugin, int, dict[str, str]]]:
        from openforms.forms.models import Form

        usage_counts: dict[tuple[BasePlugin, str | None], int] = defaultdict(int)

        active_forms = Form.objects.live().prefetch_related("auth_backends")

        for form in active_forms:
            for auth_backend in form.auth_backends.all():
                if auth_backend.backend not in self:
                    continue
                plugin = self[auth_backend.backend]

                options = getattr(
                    auth_backend, "configuration", getattr(auth_backend, "options", {})
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


# Sentinel to provide the default registry. You can easily instantiate another
# :class:`Registry` object to use as dependency injection in tests.
register = Registry()
register.set_as_metric_reporter()
