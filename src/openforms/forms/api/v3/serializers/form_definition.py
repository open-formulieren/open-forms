from typing import NotRequired, TypedDict
from uuid import UUID

from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

from openforms.formio.dynamic_config import rewrite_formio_components_for_request
from openforms.formio.typing.base import FormioConfiguration
from openforms.translations.api.serializers import ModelTranslationsSerializer
from openforms.typing import JSONObject

from ....models.form_definition import FormDefinition
from ....validators import (
    validate_form_definition_is_reusable,
    validate_no_duplicate_keys,
    validate_template_expressions,
)
from ...validators import FormIOComponentsValidator


@extend_schema_serializer(component_name="FormDefinitionConfigurationV3Serializer")
class FormDefinitionConfigurationSerializer(serializers.Serializer):
    display = serializers.ChoiceField(
        choices=["form"],
        required=False,
    )
    components = serializers.ListField(required=False)


class FormDefinitionData(TypedDict):
    uuid: UUID
    internal_name: str
    slug: NotRequired[str]
    configuration: FormioConfiguration
    login_required: NotRequired[bool]
    is_reusable: NotRequired[bool]
    translations: dict[str, JSONObject]


@extend_schema_serializer(
    deprecate_fields=["slug"], component_name="FormDefinitionV3Serializer"
)
class FormDefinitionSerializer(serializers.ModelSerializer):
    translations = ModelTranslationsSerializer()
    configuration = FormDefinitionConfigurationSerializer(
        label=_("Form.io configuration"),
        help_text=_("The form definition as Form.io JSON schema"),
        validators=[
            FormIOComponentsValidator(),
            validate_template_expressions,
            validate_no_duplicate_keys,
        ],
    )

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = FormDefinition
        fields = (
            "uuid",
            "name",
            "internal_name",
            "slug",
            "configuration",
            "login_required",
            "is_reusable",
            "translations",
        )
        extra_kwargs = {
            "name": {
                "read_only": True  # Writing is done via the `translations` field.
            },
            "slug": {
                "required": False,
                "allow_blank": True,
            },
            "uuid": {
                "required": True,  # Model's `default` would allow empty values.
                "read_only": False,
                "validators": [],  # Removes the uniqueness validator, which allows reusing existing form definitions.
            },
        }

    def to_representation(self, instance: FormDefinition) -> dict:
        representation = super().to_representation(instance=instance)
        # if "configuration" in self.fields:
        # Finalize formio component configuration with dynamic parts that depend on the
        # HTTP request. Note that this is invoked through:
        # 1. the :class:`openforms.submissions.api.serializers.SubmissionStepSerializer`
        #    for the dynamic formio configuration in the context of a submission.
        # 2. The serializers/API endpoints of :module:`openforms.forms.api` for
        #    'standalone' use/introspection.
        rewrite_formio_components_for_request(
            instance.configuration_wrapper,
            request=self.context["request"],
        )

        representation["configuration"] = instance.configuration_wrapper.configuration

        return representation

    def validate(self, attrs: FormDefinitionData) -> FormDefinitionData:
        validated_data = super().validate(attrs)
        if self.instance:
            assert isinstance(self.instance, FormDefinition)
            validate_form_definition_is_reusable(
                self.instance, new_value=validated_data.get("is_reusable")
            )
        return validated_data
