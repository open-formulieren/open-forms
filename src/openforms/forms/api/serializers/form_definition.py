from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from openforms.formio.service import (
    get_dynamic_configuration,
    update_configuration_for_request,
)

from ...models import Form, FormDefinition
from ...validators import validate_form_definition_is_reusable
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


class FormDefinitionSerializer(serializers.HyperlinkedModelSerializer):
    def to_representation(self, instance):
        representation = super().to_representation(instance=instance)
        configuration = representation["configuration"]

        # set upload urls etc
        # TODO: move this to openforms.formio.dynamic_config
        update_configuration_for_request(configuration, request=self.context["request"])

        _handle_custom_types = self.context.get("handle_custom_types", True)
        # avoid doing a second pass if the dynamic config was already processed.
        # TODO: this can probably be removed completely because of the logic check
        # being called in submissions app?
        if _handle_custom_types and not configuration.get(
            "_dynamic_config_processed", False
        ):
            representation["configuration"] = get_dynamic_configuration(
                configuration,
                request=self.context["request"],
                submission=self.context["submission"],
            )
        return representation

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
        )
        extra_kwargs = {
            "url": {
                "view_name": "api:formdefinition-detail",
                "lookup_field": "uuid",
            },
            "configuration": {
                "validators": [
                    FormIOComponentsValidator(),
                    validate_template_expressions,
                ],
            },
        }

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if self.instance:
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
