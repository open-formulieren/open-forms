from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

from openforms.translations.api.serializers import ModelTranslationsSerializer

from ....models import FormStep
from ...validators import FormStepIsApplicableIfFirstValidator
from .form_definition import (
    FormDefinitionSerializer,
)


@extend_schema_serializer(component_name="FormStepV3Serializer")
class FormStepSerializer(serializers.ModelSerializer):
    index = serializers.IntegerField(source="order", read_only=True)
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
            "translations",
        )

        extra_kwargs = {
            "uuid": {  # TODO: reuse existing steps (nice to have).
                "read_only": True,
            },
            "slug": {"allow_blank": True},
        }
        validators = [FormStepIsApplicableIfFirstValidator()]
