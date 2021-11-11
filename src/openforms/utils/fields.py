from django.db import models

from . import form_fields


class StringUUIDField(models.UUIDField):
    """
    DEPRECATED

    remains here for references in historical migrations
    """

    def from_db_value(self, value, expression, connection, context):
        if value is None:
            return value
        return str(value)

    def to_python(self, value):
        value = super().to_python(value)
        return str(value)


class SVGOrImageField(models.ImageField):
    # SVG's are not regular "images", so they get different treatment. Note that
    # we're not doing extended sanitization *yet* here, so be careful when using
    # this field.
    def formfield(self, **kwargs):
        return super().formfield(
            **{
                "form_class": form_fields.SVGOrImageField,
                **kwargs,
            }
        )
