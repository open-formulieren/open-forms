from django.db import models

from . import form_fields


class StringUUIDField(models.UUIDField):
    system_check_removed_details = {
        "msg": (
            "StringUUIDField has been removed except for support in historical migrations."
        ),
        "hint": "Use models.UUIDField instead.",
        "id": "openforms.utils.fields.E001",
    }


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
