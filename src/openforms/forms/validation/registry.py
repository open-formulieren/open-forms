from openforms.plugins.registry import BaseRegistry

from .base import BaseValidator


class FormioValidationRegistry(BaseRegistry[BaseValidator]):
    pass


register = FormioValidationRegistry()
