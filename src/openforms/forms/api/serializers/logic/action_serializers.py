from django.utils.translation import ugettext_lazy as _

from drf_polymorphic.serializers import PolymorphicSerializer
from rest_framework import serializers

from openforms.submissions.api.fields import URLRelatedField

from ....constants import LogicActionTypes, PropertyTypes
from ....models import FormStep
from ...validators import JsonLogicActionValueValidator


class ComponentPropertySerializer(serializers.Serializer):
    value = serializers.CharField(
        label=_("property key"),
        help_text=_(
            "The Form.io component property to alter, identified by `component.key`"
        ),
    )
    type = serializers.ChoiceField(
        label=_("type"),
        help_text=_("The type of the value field"),
        choices=PropertyTypes,
    )


class LogicPropertyActionSerializer(serializers.Serializer):
    property = ComponentPropertySerializer()
    state = serializers.JSONField(
        label=_("value of the property"),
        help_text=_(
            "Valid JSON determining the new value of the specified property. For example: `true` or `false`."
        ),
    )

    def validate_state(self, value):
        if value == "":
            raise serializers.ValidationError(
                self.fields["state"].error_messages["null"],
                code="blank",
            )
        return value


class LogicValueActionSerializer(serializers.Serializer):
    value = serializers.JSONField(
        label=_("Value"),
        help_text=_(
            "A valid JsonLogic expression describing the value. This may refer to "
            "(other) Form.io components."
        ),
        validators=[JsonLogicActionValueValidator()],
    )


class LogicActionPolymorphicSerializer(PolymorphicSerializer):
    type = serializers.ChoiceField(
        choices=LogicActionTypes,
        label=_("Type"),
        help_text=_("Action type for this particular action"),
    )

    discriminator_field = "type"
    serializer_mapping = {
        LogicActionTypes.disable_next: serializers.Serializer,
        LogicActionTypes.property: LogicPropertyActionSerializer,
        LogicActionTypes.value: LogicValueActionSerializer,
        LogicActionTypes.step_not_applicable: serializers.Serializer,
    }


class LogicComponentActionSerializer(serializers.Serializer):
    # TODO: validate that the component is present on the form
    component = serializers.CharField(
        required=False,  # validated against the action.type
        allow_blank=True,
        label=_("Form.io component"),
        help_text=_(
            "Key of the Form.io component that the action applies to. This field is "
            "optional if the action type is `{action_type}`, otherwise required."
        ).format(action_type=LogicActionTypes.disable_next),
    )
    form_step = URLRelatedField(
        allow_null=True,
        required=False,  # validated against the action.type
        queryset=FormStep.objects,
        view_name="api:form-steps-detail",
        lookup_field="uuid",
        parent_lookup_kwargs={"form_uuid_or_slug": "form__uuid"},
        label=_("form step"),
        help_text=_(
            "The form step that will be affected by the action. This field is "
            "required if the action type is `%(action_type)s`, otherwise optional."
        )
        % {"action_type": LogicActionTypes.step_not_applicable},
    )
    action = LogicActionPolymorphicSerializer()

    def validate(self, data: dict) -> dict:
        """
        Check that the component is supplied depending on the action type.
        """
        action_type = data.get("action", {}).get("type")
        component = data.get("component")
        form_step = data.get("form_step")

        if (
            action_type
            and action_type in LogicActionTypes.requires_component
            and not component
        ):
            raise serializers.ValidationError(
                {"component": self.fields["component"].error_messages["blank"]},
                code="blank",
            )

        if (
            action_type
            and action_type == LogicActionTypes.step_not_applicable
            and not form_step
        ):
            raise serializers.ValidationError(
                {"form_step": self.fields["form_step"].error_messages["null"]},
                code="blank",
            )

        return data
