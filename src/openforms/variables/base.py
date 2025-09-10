from abc import ABC, abstractmethod
from copy import deepcopy
from typing import ClassVar

from openforms.forms.models import FormVariable
from openforms.plugins.plugin import AbstractBasePlugin
from openforms.submissions.models import Submission
from openforms.typing import JSONObject, StrOrPromise

from .constants import DATA_TYPE_TO_JSON_SCHEMA, FormVariableDataTypes


class BaseStaticVariable(ABC, AbstractBasePlugin):
    name: ClassVar[StrOrPromise]
    data_type: ClassVar[FormVariableDataTypes]
    exclude_from_confirmation_email: ClassVar[bool] = False

    @abstractmethod
    def get_initial_value(self, submission: Submission | None = None):
        raise NotImplementedError()

    def as_json_schema(self) -> JSONObject:
        """Return JSON schema for this static variable.

        Can be overwritten in the child class. By default, it returns a basic schema
        based on the data type.
        """
        return deepcopy(DATA_TYPE_TO_JSON_SCHEMA[self.data_type])

    def get_static_variable(self, submission: Submission | None = None):
        variable = FormVariable(
            name=self.name,
            key=self.identifier,
            data_type=self.data_type,
            initial_value=self.get_initial_value(submission=submission),
        )
        variable.json_schema = self.as_json_schema()
        return variable
