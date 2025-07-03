from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from django.contrib.postgres.fields import ArrayField
from django.core.validators import (
    FileExtensionValidator,
    get_available_image_extensions,
)
from django.db import models
from django.forms import CheckboxSelectMultiple, ImageField, MultipleChoiceField

from .sanitizer import sanitize_svg_file

image_or_svg_extension_validator = FileExtensionValidator(
    allowed_extensions=["svg"] + list(get_available_image_extensions())
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
        if not data:
            return None

        # get the extension
        extension = get_extension(data)

        # SVG's are not regular "images", so they get different treatment.
        if extension == "svg":
            data = sanitize_svg_file(data)

            # we call the parent of the original ImageField instead of calling to_python
            # of ImageField (the direct superclass), as that one tries to validate the
            # image with PIL
            return super(ImageField, self).to_python(data)

        # for regular image fields, just use the normal behaviour
        return super().to_python(data)


def get_arrayfield_choices(model: type[models.Model], field: str):
    model_field = model._meta.get_field(field)
    assert isinstance(model_field, ArrayField)
    choices = model_field.base_field.choices
    assert isinstance(choices, Sequence)
    return choices


class CheckboxChoicesArrayField(MultipleChoiceField):
    widget = CheckboxSelectMultiple
    get_field_choices: Callable[[], Sequence[tuple[Any, Any]]]

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("choices", self.get_field_choices)
        for kwarg in ("base_field", "max_length", "nested"):
            if kwarg in kwargs:  # pragma: no cover
                kwargs.pop(kwarg)
        super().__init__(*args, **kwargs)
