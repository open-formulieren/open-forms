from typing import NotRequired, TypedDict

from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

from openforms.translations.api.serializers import ModelTranslationsSerializer
from openforms.typing import JSONObject

from ....models import FormStep
from ...serializers.button_text import ButtonTextSerializer
from ...validators import FormStepIsApplicableIfFirstValidator
from .form_definition import (
    FormDefinitionData,
    FormDefinitionSerializer,
)


class LiteralData(TypedDict):
    previous_text: NotRequired[str]
    save_text: NotRequired[str]
    next_text: NotRequired[str]


@extend_schema_serializer(component_name="FormStepLiteralsV3Serializer")
class FormStepLiteralsSerializer(serializers.Serializer):
    previous_text = ButtonTextSerializer(raw_field="previous_text", required=False)
    save_text = ButtonTextSerializer(raw_field="save_text", required=False)
    next_text = ButtonTextSerializer(raw_field="next_text", required=False)

    class Meta:
        fields = (
            "previous_text",
            "save_text",
            "next_text",
        )


class FormStepData(TypedDict):
    order: int
    slug: NotRequired[str]
    form_definition: FormDefinitionData
    is_applicable: NotRequired[bool]
    literals: NotRequired[LiteralData]
    translations: dict[str, JSONObject]


@extend_schema_serializer(component_name="FormStepV3Serializer")
class FormStepSerializer(serializers.ModelSerializer):
    index = serializers.IntegerField(source="order")
    literals = FormStepLiteralsSerializer(source="*", required=False)
    form_definition = FormDefinitionSerializer()
    translations = ModelTranslationsSerializer()

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = FormStep
        fields = (
            "uuid",
            "index",
            "slug",
            "form_definition",
            "is_applicable",
            "literals",
            "translations",
        )

        extra_kwargs = {
            "uuid": {  # TODO: reuse existing steps (nice to have)
                "read_only": True,
            },
            "slug": {"allow_blank": True},
        }
        validators = [FormStepIsApplicableIfFirstValidator()]
