from dataclasses import dataclass

from openforms.forms.models import FormVariable


@dataclass
class BaseStaticVariable:
    identifier: str

    def get_initial_value(self, *args, **kwargs):
        raise NotImplementedError()

    def get_static_variable(self, *args, **kwargs):
        return FormVariable(
            name=self.name,
            key=self.identifier,
            data_type=self.data_type,
            initial_value=self.get_initial_value(*args, **kwargs),
        )
