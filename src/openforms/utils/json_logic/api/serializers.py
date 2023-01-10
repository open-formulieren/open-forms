from dataclasses import dataclass

from django.utils.translation import gettext_lazy as _

from json_logic.typing import JSON
from rest_framework import serializers

from .. import generate_rule_description
from .validators import JsonLogicValidator


@dataclass
class LogicDescription:
    expression: JSON
    description: str


class LogicDescriptionSerializer(serializers.Serializer):
    expression = serializers.JSONField(
        label=_("JsonLogic expression"),
        validators=[JsonLogicValidator()],
        write_only=True,
    )
    description = serializers.CharField(
        label=_("generated description"),
        help_text=_("Description derived from the input expression"),
        read_only=True,
    )

    def create(self, validated_data: dict):
        description = generate_rule_description(validated_data["expression"])
        return LogicDescription(description=description, **validated_data)
