import logging
from typing import Any, Dict, List

from django.utils.translation import gettext_lazy as _

from django_camunda.client import get_client

from openforms.contrib.camunda.dmn import evaluate_dmn

from ...base import BasePlugin, DecisionDefinition, DecisionDefinitionVersion
from ...registry import register

logger = logging.getLogger(__name__)


def _get_decision_definition_id(client, key: str, version: str = ""):
    query = {"key": key}
    # handle version pinning
    if version:
        query["version"] = version
    else:
        query["latestVersion"] = "true"

    # get the results to figure out the decision definition ID
    results = client.get("decision-definition", query)

    if not results or (num_results := len(results)) > 1:
        logger.warning(
            "None or multiple decision-definition found in the API, found %d results for query %r.",
            num_results,
            query,
        )
        return ""

    return results[0]["id"]


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

    def evaluate(
        self, definition_id: str, *, version: str = "", input_values: Dict[str, Any]
    ) -> Dict[str, Any]:
        with get_client() as client:
            camunda_id = _get_decision_definition_id(client, definition_id, version)
            result = evaluate_dmn(
                dmn_key=definition_id,
                dmn_id=camunda_id,
                input_values=input_values,
                client=client,
            )
        return result

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
        with get_client() as client:
            camunda_id = _get_decision_definition_id(client, definition_id, version)
            xml_response = client.get(f"decision-definition/{camunda_id}/xml")

        return xml_response["dmn_xml"]
