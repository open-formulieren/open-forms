from django.utils.translation import gettext as _

from json_logic import jsonLogic
from rest_framework import serializers


class JsonLogicValidator:
    """Validate that a json object is a valid jsonLogic expression"""

    def __call__(self, value: dict):
        try:
            jsonLogic(value)
        except Exception as exc:
            raise serializers.ValidationError(
                _("Invalid JSON logic."), code="invalid"
            ) from exc
