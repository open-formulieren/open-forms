from pathlib import Path

from django.core.validators import (
    FileExtensionValidator,
    get_available_image_extensions,
)
from django.forms import ImageField

image_or_svg_extension_validator = FileExtensionValidator(
    allowed_extensions=["svg"] + get_available_image_extensions()
)


def get_extension(file_like):
    return Path(file_like.name).suffix[1:].lower()


def unless_svg(func):
    """
    Decorator to invoke the original validator UNLESS we're dealing with an SVG file.
    """

    def validator(value):
        extension = get_extension(value)
        if extension != "svg":
            return func(value)

    return validator


class SVGOrImageField(ImageField):
    default_validators = [
        image_or_svg_extension_validator,
        *[unless_svg(validator) for validator in ImageField.default_validators],
    ]

    def to_python(self, data):
        # get the extension
        extension = get_extension(data)

        # SVG's are not regular "images", so they get different treatment. Note that
        # we're not doing extended sanitization *yet* here, so be careful when using
        # this field.
        if extension == "svg":
            # we call the parent of the original ImageField instead of calling to_python
            # of ImageField (the direct superclass), as that one tries to validate the
            # image with PIL
            return super(ImageField, self).to_python(data)

        # for regular image fields, just use the normal behaviour
        return super().to_python(data)
