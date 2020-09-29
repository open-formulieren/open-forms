from django.db import models


class StringUUIDField(models.UUIDField):

    def from_db_value(self, value, expression, connection, context):
        if value is None:
            return value
        return str(value)

    def to_python(self, value):
        value = super().to_python(value)
        return str(value)
