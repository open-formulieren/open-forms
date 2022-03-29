import logging
from typing import List

from django.utils.translation import gettext_lazy as _

from django_camunda.client import get_client

from ...base import BasePlugin, DecisionDefinition, DecisionDefinitionVersion
from ...registry import register

logger = logging.getLogger(__name__)


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

    def get_definition_xml(self, definition_id: str, version: str = "") -> str:
        query = {"key": definition_id}
        # handle version pinning
        if version:
            query["version"] = version
        else:
            query["latestVersion"] = "true"

        with get_client() as client:
            # get the results to figure out the decision definition ID
            results = client.get("decision-definition", query)

            if not results or (num_results := len(results)) > 1:
                logger.warning(
                    "None or multiple decision-definition found in the API, found %d results for query %r.",
                    num_results,
                    query,
                )
                return ""

            camunda_id = results[0]["id"]
            xml_response = client.get(f"decision-definition/{camunda_id}/xml")

        return xml_response["dmn_xml"]
