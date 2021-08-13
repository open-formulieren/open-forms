from typing import List

from django.utils.translation import gettext as _

from json_logic import jsonLogic
from rest_framework import serializers

VALID_ACTION_TYPES = ["property", "value", "disable-next"]


class LogicActionValidator:
    """
    Validates that all the expected fields are present for the different types of actions.
    Note: it does not check if form components actually exist.
    """

    def __call__(self, actions: List[dict]):
        if not isinstance(actions, list):
            raise serializers.ValidationError(
                _("Attribute 'actions' of form logic should be a list.")
            )

        for action in actions:
            if "action" not in action:
                raise serializers.ValidationError(
                    _("The 'action' attribute is required within the action.")
                )

            action_data = action["action"]

            self._validate_action(action_data)

    def _validate_action(self, action: dict) -> None:
        if "type" not in action:
            raise serializers.ValidationError(_("No action type was specified."))

        if action["type"] not in VALID_ACTION_TYPES:
            raise serializers.ValidationError(
                _("Invalid action type. Allowed values are %(types)s.")
                % {"types": ", ".join(VALID_ACTION_TYPES)}
            )

        if action["type"] == "property":
            self._validate_property(action)
        elif action["type"] == "value":
            self._validate_value(action)

    def _validate_property(self, action: dict) -> None:
        if "property" not in action:
            raise serializers.ValidationError(
                _(
                    "For actions of type 'property', the 'property' attribute is required."
                )
            )

        if not isinstance(action["property"], dict):
            raise serializers.ValidationError(
                _("Attribute 'property' should be a dictionary.")
            )

        if "value" not in action["property"]:
            raise serializers.ValidationError(
                _("Attribute 'property' should contain the attribute 'value'.")
            )

        if "state" not in action:
            raise serializers.ValidationError(
                _("For actions of type 'property', the property 'state' is required.")
            )

    def _validate_value(self, action: dict) -> None:
        if "value" not in action:
            raise serializers.ValidationError(
                _("For actions of type 'value', the 'value' attribute is required.")
            )

        try:
            jsonLogic(action["value"])
        except ValueError:
            raise serializers.ValidationError(
                _("Invalid JSON logic specified in the 'value' attribute")
            )
