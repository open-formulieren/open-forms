from django.utils.translation import gettext_lazy as _

from rest_framework import fields


class NullField(fields.Field):
    """
    Field that only accepts the 'null' value.
    """

    default_error_messages = {"invalid": _("Must be 'null'.")}
    initial = None

    def to_internal_value(self, data):
        if data is not None:
            self.fail("invalid", input=data)
        return None

    def to_representation(self, value):
        return None
