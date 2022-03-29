from typing import List

from django.utils.translation import gettext_lazy as _

from django_camunda.client import get_client

from ...base import BasePlugin, DecisionDefinition
from ...registry import register


@register("camunda")
class Plugin(BasePlugin):
    verbose_name = _("Camunda")

    def get_available_decision_definitions(self) -> List[DecisionDefinition]:
        with get_client() as client:
            results = client.get(
                "decision-definition",
                params={"latestVersion": "true"},
            )
        return [
            DecisionDefinition(
                identifier=result["key"], label=result["name"] or result["key"]
            )
            for result in results
        ]
