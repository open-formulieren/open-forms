from django.contrib.postgres.fields import ArrayField
from django.db.models.fields import CharField

from openforms.plugins.constants import UNIQUE_ID_MAX_LENGTH
from openforms.plugins.validators import PluginExistsValidator

from .registry import register


class AuthenticationBackendMultiSelectField(ArrayField):
    system_check_removed_details = {
        "msg": (
            "openforms.authentication.fields.AuthenticationBackendMultiSelectField has"
            "been removed except for support in historical migrations."
        ),
        "id": "authentication.fields.E001",
    }


class BackendChoiceField(CharField):
    def __init__(self, *args, **kwargs):
        self.registry = kwargs.pop("registry", register)

        kwargs.setdefault("max_length", UNIQUE_ID_MAX_LENGTH)
        if kwargs["max_length"] > UNIQUE_ID_MAX_LENGTH:
            raise ValueError(f"'max_length' is capped at {UNIQUE_ID_MAX_LENGTH}")

        super().__init__(*args, **kwargs)

        self.validators.append(PluginExistsValidator(self.registry))
