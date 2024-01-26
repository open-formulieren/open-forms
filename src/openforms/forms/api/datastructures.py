from dataclasses import dataclass

from django.utils.functional import cached_property

from ..models import Form, FormVariable


@dataclass
class FormVariableWrapper:
    form: Form

    @cached_property
    def variables(self) -> dict[str, FormVariable]:
        return {variable.key: variable for variable in self.form.formvariable_set.all()}

    def get(self, key: str, default=None) -> FormVariable | None:
        return self.variables.get(key, default)

    def __contains__(self, key: str) -> bool:
        return key in self.variables

    def __getitem__(self, key: str) -> FormVariable:
        return self.variables[key]
