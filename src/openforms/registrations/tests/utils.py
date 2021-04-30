from contextlib import contextmanager
from unittest.mock import patch

from ..fields import BackendChoiceField
from ..registry import Registry
from ..validators import PluginValidator


@contextmanager
def patch_registry(field: BackendChoiceField, register: Registry):
    validators = [
        validator
        for validator in field.validators
        if isinstance(validator, PluginValidator)
    ]
    assert len(validators) == 1, "Expected only one PluginValidator"
    validator = validators[0]

    with patch.object(field, "registry", register):
        with patch.object(validator, "registry", register):
            yield
