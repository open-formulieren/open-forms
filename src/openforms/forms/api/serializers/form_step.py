from django.db.models import Q

from rest_framework import serializers
from rest_framework_nested.relations import NestedHyperlinkedRelatedField

from openforms.api.serializers import PublicFieldsSerializerMixin
from openforms.translations.api.serializers import (
    ComponentTranslationsSerializer,
    ModelTranslationsSerializer,
)

from ...models import FormDefinition, FormStep
from ...validators import validate_no_duplicate_keys_across_steps, validate_price_option
from ..validators import FormStepIsApplicableIfFirstValidator
from .button_text import ButtonTextSerializer
from .form_definition import FormDefinitionConfigurationSerializer


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
        # allowlist for anonymous users
        public_fields = (
            "previous_text",
            "save_text",
            "next_text",
        )


class MinimalFormStepSerializer(serializers.ModelSerializer):
    form_definition = serializers.SlugRelatedField(read_only=True, slug_field="name")
    index = serializers.IntegerField(source="order")
    literals = FormStepLiteralsSerializer(source="*", required=False)
    url = NestedHyperlinkedRelatedField(
        queryset=FormStep.objects,
        source="*",
        view_name="api:form-steps-detail",
        lookup_field="uuid",
        parent_lookup_kwargs={"form_uuid_or_slug": "form__uuid"},
    )

    class Meta:
        model = FormStep
        fields = (
            "uuid",
            "slug",
            "form_definition",
            "index",
            "literals",
            "url",
            "is_applicable",
        )
        extra_kwargs = {
            "uuid": {
                "read_only": True,
            }
        }


class FormStepSerializer(
    PublicFieldsSerializerMixin, serializers.HyperlinkedModelSerializer
):
    index = serializers.IntegerField(source="order")
    configuration = FormDefinitionConfigurationSerializer(
        source="form_definition.configuration", read_only=True
    )
    login_required = serializers.BooleanField(
        source="form_definition.login_required", read_only=True
    )
    is_reusable = serializers.BooleanField(
        source="form_definition.is_reusable", read_only=True
    )
    name = serializers.CharField(source="form_definition.name", read_only=True)
    internal_name = serializers.CharField(
        source="form_definition.internal_name", read_only=True
    )
    literals = FormStepLiteralsSerializer(source="*", required=False)
    url = NestedHyperlinkedRelatedField(
        source="*",
        view_name="api:form-steps-detail",
        lookup_field="uuid",
        parent_lookup_kwargs={"form_uuid_or_slug": "form__uuid"},
        read_only=True,
    )
    translations = ModelTranslationsSerializer()
    component_translations = ComponentTranslationsSerializer(
        source="form_definition.component_translations",
        read_only=True,
    )

    parent_lookup_kwargs = {
        "form_uuid_or_slug": "form__uuid",
    }

    class Meta:
        model = FormStep
        fields = (
            "uuid",
            "index",
            "slug",
            "configuration",
            "form_definition",
            "name",
            "internal_name",
            "url",
            "is_applicable",
            "login_required",
            "is_reusable",
            "literals",
            "translations",
            "component_translations",
        )
        public_fields = (
            "uuid",
            "index",
            "slug",
            "configuration",
            "form_definition",
            "name",
            "internal_name",
            "url",
            "is_applicable",
            "login_required",
            "is_reusable",
            "literals",
            "component_translations",
        )

        extra_kwargs = {
            "form_definition": {
                "view_name": "api:formdefinition-detail",
                "lookup_field": "uuid",
            },
            "uuid": {
                "read_only": True,
            },
        }
        validators = [FormStepIsApplicableIfFirstValidator()]

    def create(self, validated_data):
        validated_data["form"] = self.context["form"]
        return super().create(validated_data)

    def validate_form_definition(self, current_form_definition):
        """
        Check that there are no duplicate keys in a form.
        Bandaid for #2734

        #TODO: This could cause a race condition if steps are saved in parallel and so their form definitions are not
        checked against each other.
        """
        form = self.context["form"]
        other_form_definitions_ids = form.formstep_set.filter(
            ~Q(form_definition__id=current_form_definition.id)
        ).values_list("form_definition", flat=True)
        other_form_definitions = FormDefinition.objects.filter(
            id__in=other_form_definitions_ids
        )

        validate_no_duplicate_keys_across_steps(
            current_form_definition, list(other_form_definitions)
        )

        validate_price_option(
            form.product, current_form_definition, list(other_form_definitions)
        )

        return current_form_definition
