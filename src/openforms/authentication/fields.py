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


class BackendChoiceField(CharField):
    def __init__(self, *args, **kwargs):
        self.registry = kwargs.pop("registry", register)

        kwargs.setdefault("max_length", UNIQUE_ID_MAX_LENGTH)
        if kwargs["max_length"] > UNIQUE_ID_MAX_LENGTH:
            raise ValueError(f"'max_length' is capped at {UNIQUE_ID_MAX_LENGTH}")

        super().__init__(*args, **kwargs)

        self.validators.append(PluginExistsValidator(self.registry))
