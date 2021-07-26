from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _


@deconstructible
class PluginExistsValidator:
    message = _("Choose a valid plugin")
    code = "invalid"

    def __init__(self, registry):
        self.registry = registry

    def __call__(self, value: str):
        try:
            self.registry[value]
        except KeyError:
            raise ValidationError(self.message, code=self.code)
