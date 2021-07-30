from contextlib import contextmanager
from unittest.mock import patch

from openforms.plugins.validators import PluginExistsValidator

from ..fields import RegistrationBackendChoiceField
from ..registry import Registry


@contextmanager
def patch_registry(field: RegistrationBackendChoiceField, register: Registry):
    validators = [
        validator
        for validator in field.validators
        if isinstance(validator, PluginExistsValidator)
    ]
    assert len(validators) == 1, "Expected only one PluginValidator"
    validator = validators[0]

    with patch.object(field, "registry", register):
        with patch.object(validator, "registry", register):
            yield
