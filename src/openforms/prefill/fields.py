from django.db.models.fields import CharField

from openforms.plugins.constants import UNIQUE_ID_MAX_LENGTH
from openforms.plugins.validators import PluginExistsValidator

from .registry import register


class PrefillPluginChoiceField(CharField):
    def __init__(self, *args, **kwargs):
        self.auth_attribute = kwargs.pop("auth_attribute", "")
        self.registry = kwargs.pop("registry", register)

        kwargs.setdefault("max_length", UNIQUE_ID_MAX_LENGTH)
        if kwargs["max_length"] > UNIQUE_ID_MAX_LENGTH:
            raise ValueError(f"'max_length' is capped at {UNIQUE_ID_MAX_LENGTH}")

        super().__init__(*args, **kwargs)

        self.validators.append(PluginExistsValidator(self.registry))

    def formfield(self, *args, **kwargs):
        """
        Force this into a choices field.
        """
        monkeypatch = not (_old := self.choices)
        if monkeypatch:
            self.choices = self._get_plugin_choices()

        field = super().formfield(*args, **kwargs)

        if monkeypatch:
            self.choices = _old
        return field

    def _get_plugin_choices(self):
        choices = []
        for plugin in register.iter_enabled_plugins():
            if self.auth_attribute not in plugin.requires_auth:
                continue
            choices.append((plugin.identifier, plugin.get_label()))
        return choices
