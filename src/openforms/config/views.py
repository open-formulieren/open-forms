from typing import Any

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.generic import TemplateView

from openforms.utils.mixins import UserIsStaffMixin

from .checks import ConfigurationCheck
from .data import Entry
from .models import GlobalConfiguration
from .utils import verify_clamav_connection


class ConfigurationView(UserIsStaffMixin, PermissionRequiredMixin, TemplateView):
    template_name = "admin/config/overview.html"
    permission_required = [
        "accounts.configuration_overview",
    ]

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        sections = []

        # undocumented query string support - helps for developers ;)
        module = self.request.GET.get("module")

        check = ConfigurationCheck(requested_plugin=self.request.GET.get("plugin"))

        sections += check.get_configuration_results(module)

        sections.append({"name": "Anti-virus", "entries": [self.get_clamav_entry()]})

        context.update({"sections": sections})

        return context

    def get_clamav_entry(self):
        config = GlobalConfiguration.get_solo()
        config_url = reverse(
            "admin:config_globalconfiguration_change", args=(config.pk,)
        )
        if not config.enable_virus_scan:
            return Entry(
                name="ClamAV",
                status=None,
                actions=[
                    (_("Configuration"), config_url),
                ],
            )

        result = verify_clamav_connection(
            host=config.clamav_host,
            port=config.clamav_port,
            timeout=config.clamav_timeout,
        )

        return Entry(
            name="ClamAV",
            status=result.can_connect,
            error=result.error,
            actions=[
                (
                    _("Configuration"),
                    config_url,
                ),
            ],
        )
