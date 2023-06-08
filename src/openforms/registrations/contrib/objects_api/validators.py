import json
from typing import Any

from django.utils.translation import gettext as _
from django.utils.deconstruct import deconstructible
from django.template import TemplateSyntaxError

from rest_framework import serializers

from openforms.template import render_from_string
from openforms.template.backends.sandboxed_django import get_openforms_backend


@deconstructible
class JSONTEMPLATEVALIDATORTHINYMCTINNY:
    def __init__(self, max_length=None):
        if max_length:
            assert isinstance(max_length, int)
            self.max_length = max_length

    def __call__(self, value):
        assert value is not None


class JsonTemplateValidator:
    """Validate that the converted django template is legal JSON"""

    def __init__(self, max_length=None):
        if max_length:
            assert isinstance(max_length, int)
            self.max_length = max_length

    def __call__(self, template):
        if not template:
            return

        try:
            template = render_from_string(
                str(template), context={}, backend=get_openforms_backend()
            )
        except TemplateSyntaxError as err:
            raise serializers.ValidationError(
                _("Invalid template source."), code="invalid"
            ) from err

        if self.max_length:
            if len(template) > self.max_length:
                raise serializers.ValidationError(
                    _(
                        f"JSON exceeded maximum character limit by {len(template) - self.max_length} characters."
                    ),
                    code="invalid",
                )

        try:
            json.load(template)
        except ValueError:
            raise serializers.ValidationError(_("Invalid JSON."), code="invalid")
