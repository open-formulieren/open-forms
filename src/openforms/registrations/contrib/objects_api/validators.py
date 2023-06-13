import json

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.utils.deconstruct import deconstructible
from django.template import TemplateSyntaxError
from openforms.registrations.contrib.objects_api.constants import (
    JsonTemplateValidatorErrorTypes,
)

from rest_framework import serializers

from openforms.template import render_from_string
from openforms.template.backends.sandboxed_django import get_openforms_backend


@deconstructible
class JsonTemplateValidator:
    """Validate that the converted django template is legal JSON"""

    def __init__(
        self,
        max_length: int | None = None,
        backend: str = get_openforms_backend(),
        error_type: JsonTemplateValidatorErrorTypes.choices = JsonTemplateValidatorErrorTypes.model,
    ):
        self.max_length = max_length
        self.backend = backend
        self.error_type = error_type

    def __call__(self, template):
        if not template:
            return

        try:
            template = render_from_string(
                str(template), context={}, backend=self.backend
            )
        except TemplateSyntaxError as err:
            self.__error__(_("Invalid template source."))

        if self.max_length:
            if len(template) > self.max_length:
                self.__error__(
                    _(
                        f"JSON exceeded maximum character limit by {len(template) - self.max_length} characters."
                    )
                )

        try:
            json.loads(template)
        except ValueError or AttributeError:
            self.__error__(_("Invalid JSON."))

    def __error__(self, msg: str) -> None:
        if not msg:
            return

        match self.error_type:
            case JsonTemplateValidatorErrorTypes.model:
                raise ValidationError(msg, code="invalid")
            case JsonTemplateValidatorErrorTypes.api:
                raise serializers.ValidationError(msg, code="invalid")
            case _:
                return
