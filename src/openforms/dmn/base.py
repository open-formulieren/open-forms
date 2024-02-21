from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from openforms.plugins.plugin import AbstractBasePlugin

from .types import DMNInputOutput


@dataclass
class DecisionDefinition:
    """
    Represent a single decision definition.
    """

    identifier: str
    label: str


@dataclass
class DecisionDefinitionVersion:
    """
    Represent a version of a decision definition.
    """

    id: str
    label: str


class BasePlugin(ABC, AbstractBasePlugin):
    @abstractmethod
    def get_available_decision_definitions(self) -> list[DecisionDefinition]:
        """
        Get a collection of all the available decision definitions.

        The end-user configuring the evaluation selects one of the available choices.
        Note that different versions of the same definition must be filtered out, as
        specifying a particular version is a separate action.
        """
        raise NotImplementedError()

    @abstractmethod
    def evaluate(
        self, definition_id: str, *, version: str = "", input_values: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Evaluate the decision definition with the given input data.
        """
        raise NotImplementedError()

    def get_decision_definition_versions(
        self, definition_id: str
    ) -> list[DecisionDefinitionVersion]:
        """
        Get a collection of available versions for a given decision definition.

        Backends supporting versioning can implement this method to offer more
        granularity. By default we assume versioning is not supported and return an
        empty list.
        """
        return []

    def get_definition_xml(self, definition_id: str, version: str = "") -> str:
        """
        Return the standards-compliant XML definition of the decision table.

        If this is not available, return an empty string.
        """
        return ""

    @abstractmethod
    def get_decision_definition_parameters(
        self, definition_id: str, version: str = ""
    ) -> DMNInputOutput:
        """
        Return the input/output clauses for a given decision definition (version).

        An input clause defines the id, label, expression and type of a decision table input. It is represented by an
        input element inside a decisionTable XML element.
        An output clause defines the id, label, name and type of a decision table output. It is represented by an
        output element inside a decisionTable XML element.
        """
        ...
