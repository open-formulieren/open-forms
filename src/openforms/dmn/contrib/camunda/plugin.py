from typing import List

from django.utils.translation import gettext_lazy as _

from django_camunda.client import get_client

from ...base import BasePlugin, DecisionDefinition, DecisionDefinitionVersion
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

    def get_decision_definition_versions(
        self, definition_id: str
    ) -> List[DecisionDefinitionVersion]:
        """
        Get a collection of available versions for a given decision definition.

        :param definition_id: the key of the decision definition in the Camunda API.
        """
        with get_client() as client:
            results = client.get(
                "decision-definition",
                params={"key": definition_id, "sortBy": "version", "sortOrder": "desc"},
            )
        return [
            DecisionDefinitionVersion(
                id=str(result["version"]),
                label=_("v{version} (version tag: {version_tag})").format(
                    version=result["version"],
                    version_tag=result["version_tag"] or _("n/a"),
                ),
            )
            for result in results
        ]
