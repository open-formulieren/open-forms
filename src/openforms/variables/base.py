from abc import ABC, abstractmethod
from typing import ClassVar

from openforms.forms.models import FormVariable
from openforms.plugins.plugin import AbstractBasePlugin
from openforms.submissions.models import Submission
from openforms.typing import JSONObject, StrOrPromise

from .constants import FormVariableDataTypes


class BaseStaticVariable(ABC, AbstractBasePlugin):
    name: ClassVar[StrOrPromise]
    data_type: ClassVar[FormVariableDataTypes]

    @abstractmethod
    def get_initial_value(self, submission: Submission | None = None):
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def as_json_schema() -> JSONObject:
        """Return JSON schema for this static variable."""
        raise NotImplementedError()

    def get_static_variable(self, submission: Submission | None = None):
        return FormVariable(
            name=self.name,
            key=self.identifier,
            data_type=self.data_type,
            initial_value=self.get_initial_value(submission=submission),
        )
