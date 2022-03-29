from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, NoReturn

from openforms.formio.typing import Component
from openforms.forms.models import Form
from openforms.plugins.plugin import AbstractBasePlugin


@dataclass
class DecisionDefinition:
    identifier: str
    label: str


class BasePlugin(ABC, AbstractBasePlugin):
    @abstractmethod
    def get_available_decision_definitions(self) -> List[DecisionDefinition]:
        """
        Get a collection of all the available decision definitions.

        The end-user configuring the component selects one of the available choices.
        Note that different versions of the same definition must be filtered out, as
        specifying a particular version is a separate action.
        """
        raise NotImplementedError()

    # @abstractmethod
    # def validate_inputs_defined(self, form: Form, component: Component) -> NoReturn:
    #     """
    #     Validate that all the required inputs for the DMN component are defined.

    #     Given the DMN component configuration and the full form definition, check that
    #     all the required inputs for the decision definition/table are present in the
    #     form.
    #     """
    #     raise NotImplementedError()
