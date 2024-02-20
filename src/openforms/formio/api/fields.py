from rest_framework import serializers

from ..validators import variable_key_validator


class FormioVariableKeyField(serializers.CharField):
    """A ``CharField`` that will validate values are valid Formio variable keys.

    It must only contain alphanumeric characters, underscores, dots and dashes and should not be ended by dash or dot.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.validators = [variable_key_validator, *self.validators]
