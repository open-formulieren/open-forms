from django.contrib.postgres.fields import ArrayField
from django.db.models.fields import CharField

from openforms.plugins.constants import UNIQUE_ID_MAX_LENGTH
from openforms.plugins.validators import PluginExistsValidator
from openforms.utils.validators import UniqueValuesValidator

from .registry import register


class AuthenticationBackendMultiSelectField(ArrayField):
    def __init__(self, *args, **kwargs):
        self.registry = kwargs.pop("registry", register)
        kwargs["base_field"] = BackendChoiceField(registry=self.registry)
        kwargs.setdefault("default", list)
        super().__init__(**kwargs)

        self.validators.append(UniqueValuesValidator())


class AuthenticationBackendChoiceField(CharField):
    def __init__(self, *args, **kwargs):
        self.registry = kwargs.pop("registry", register)

        kwargs.setdefault("max_length", UNIQUE_ID_MAX_LENGTH)
        if kwargs["max_length"] > UNIQUE_ID_MAX_LENGTH:
            raise ValueError(f"'max_length' is capped at {UNIQUE_ID_MAX_LENGTH}")

        super().__init__(*args, **kwargs)

        self.validators.append(PluginExistsValidator(self.registry))

    def formfield(self, **kwargs):
        """
        Force this into a choices field.
        """
        monkeypatch = not self.choices
        if monkeypatch:
            _old = self.choices
            self.choices = self._get_plugin_choices()
        field = super().formfield(**kwargs)
        if monkeypatch:
            self.choices = _old
        return field

    def _get_plugin_choices(self):
        return self.registry.get_choices()


class BackendChoiceField(CharField):
    def __init__(self, *args, **kwargs):
        self.registry = kwargs.pop("registry", register)

        kwargs.setdefault("max_length", UNIQUE_ID_MAX_LENGTH)
        if kwargs["max_length"] > UNIQUE_ID_MAX_LENGTH:
            raise ValueError(f"'max_length' is capped at {UNIQUE_ID_MAX_LENGTH}")

        super().__init__(*args, **kwargs)

        self.validators.append(PluginExistsValidator(self.registry))
