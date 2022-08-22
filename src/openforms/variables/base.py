from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from openforms.forms.models import FormVariable


@dataclass
class BaseStaticVariable(ABC):
    identifier: str
    name: str = field(init=False)
    data_type: str = field(init=False)

    @abstractmethod
    def get_initial_value(self, *args, **kwargs):
        raise NotImplementedError()  # pragma: nocover

    def get_static_variable(self, *args, **kwargs):
        return FormVariable(
            name=self.name,
            key=self.identifier,
            data_type=self.data_type,
            initial_value=self.get_initial_value(*args, **kwargs),
        )
