from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field, extend_schema_serializer
from rest_framework import serializers

from openforms.api.serializers import PublicFieldsSerializerMixin
from openforms.formio.service import rewrite_formio_components_for_request
from openforms.formio.utils import iter_components
from openforms.translations.api.serializers import ModelTranslationsSerializer

from ...models import Form, FormDefinition
from ...sanitizer import sanitize_component
from ...validators import (
    validate_form_definition_is_reusable,
    validate_no_duplicate_keys,
)
from ..validators import FormIOComponentsValidator, validate_template_expressions


class UsedInFormSerializer(serializers.HyperlinkedModelSerializer):
    admin_url = serializers.SerializerMethodField(
        label=_("admin URL"),
        help_text=_("Link to the change/view page in the admin interface"),
    )

    class Meta:
        model = Form
        fields = (
            "url",
            "uuid",
            "name",
            "active",
            "admin_url",
        )
        extra_kwargs = {
            "url": {
                "view_name": "api:form-detail",
                "lookup_field": "uuid",
                "lookup_url_kwarg": "uuid_or_slug",
            },
            "name": {
                "source": "admin_name",
            },
        }

    @extend_schema_field(OpenApiTypes.URI)
    def get_admin_url(self, obj: Form) -> str:
        admin_url = reverse("admin:forms_form_change", args=(obj.pk,))
        request = self.context.get("request")
        if not request:
            return admin_url
        return request.build_absolute_uri(admin_url)


class FormDefinitionConfigurationSerializer(serializers.Serializer):
    display = serializers.ChoiceField(
        choices=["form"],
        required=False,
    )
    components = serializers.ListField(required=False)


@extend_schema_serializer(deprecate_fields=["slug"])
class FormDefinitionSerializer(
    PublicFieldsSerializerMixin, serializers.HyperlinkedModelSerializer
):
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

    class Meta:
        model = FormDefinition
        fields = (
            "url",
            "uuid",
            "name",
            "internal_name",
            "slug",
            "configuration",
            "login_required",
            "is_reusable",
            "translations",
        )
        public_fields = (
            "url",
            "uuid",
            "name",
            "internal_name",
            "slug",
            "configuration",
            "login_required",
            "is_reusable",
        )
        extra_kwargs = {
            "url": {
                "view_name": "api:formdefinition-detail",
                "lookup_field": "uuid",
            },
            "name": {"read_only": True},  # writing is done via the `translations` field
            "slug": {
                "required": False,
                "allow_blank": True,
            },
        }

    def to_representation(self, instance):
        representation = super().to_representation(instance=instance)
        # if "configuration" in self.fields:
        # Finalize formio component configuration with dynamic parts that depend on the
        # HTTP request. Note that this is invoked through:
        # 1. the :class:`openforms.submissions.api.serializers.SubmissionStepSerializer`
        #    for the dynamic formio configuration in the context of a submission.
        # 2. The serializers/API endpoints of :module:`openforms.forms.api` for
        #    'standalone' use/introspection.
        is_export = self.context.get("is_export", False)

        if not is_export:
            rewrite_formio_components_for_request(
                instance.configuration_wrapper,
                request=self.context["request"],
            )

        representation["configuration"] = instance.configuration_wrapper.configuration

        return representation

    def create(self, validated_data):
        if configuration := validated_data.get("configuration"):
            for component in iter_components(configuration):
                sanitize_component(component)

        return super().create(validated_data)

    def update(self, instance, validated_data):
        if configuration := validated_data.get("configuration"):
            for component in iter_components(configuration):
                sanitize_component(component)

        return super().update(instance, validated_data)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if self.instance:
            assert isinstance(self.instance, FormDefinition)
            validate_form_definition_is_reusable(
                self.instance, new_value=attrs.get("is_reusable")
            )
        return attrs


class FormDefinitionDetailSerializer(FormDefinitionSerializer):
    used_in = UsedInFormSerializer(
        many=True,
        label=_("Used in forms"),
        help_text=_(
            "The collection of forms making use of this definition. This includes both "
            "active and inactive forms."
        ),
    )

    class Meta(FormDefinitionSerializer.Meta):
        fields = FormDefinitionSerializer.Meta.fields + ("used_in",)
        public_fields = FormDefinitionSerializer.Meta.public_fields + ("used_in",)
