from collections import defaultdict

from django.db.models import Q
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import OpenApiExample, extend_schema_serializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from openforms.api.fields import (
    PrimaryKeyRelatedAsChoicesField,
    RelatedFieldFromContext,
)
from openforms.api.serializers import ListWithChildSerializer
from openforms.formio.api.fields import FormioVariableKeyField
from openforms.registrations.contrib.objects_api.models import ObjectsAPIGroupConfig
from openforms.utils.mixins import JsonSchemaSerializerMixin
from openforms.variables.api.serializers import ServiceFetchConfigurationSerializer
from openforms.variables.constants import FormVariableSources
from openforms.variables.models import ServiceFetchConfiguration
from openforms.variables.service import get_static_variables

from ...models import Form, FormDefinition, FormVariable


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name="Variable mapping example",
            value={
                "variable_key": "a_component_variable",
                "target_path": ["path", "to.the", "target"],
            },
        )
    ]
)
class ObjecttypeVariableMappingSerializer(serializers.Serializer):
    """A mapping between a form variable key and the corresponding Objecttype attribute."""

    variable_key = FormioVariableKeyField(
        label=_("variable key"),
        help_text=_(
            "The 'dotted' path to a form variable key. The format should comply to how Formio handles nested component keys."
        ),
    )
    target_path = serializers.ListField(
        child=serializers.CharField(label=_("Segment of a JSON path")),
        label=_("target path"),
        help_text=_(
            "Representation of the JSON target location as a list of string segments."
        ),
    )


class FormVariableOptionsSerializer(JsonSchemaSerializerMixin, serializers.Serializer):
    objects_api_group = PrimaryKeyRelatedAsChoicesField(
        queryset=ObjectsAPIGroupConfig.objects.exclude(
            Q(objects_service=None)
            | Q(objecttypes_service=None)
            | Q(drc_service=None)
            | Q(catalogi_service=None)
        ),
        label=("Objects API group"),
        required=False,
        help_text=_("Which Objects API group to use."),
    )
    objecttype_uuid = serializers.UUIDField(
        label=_("objecttype"),
        required=False,
        help_text=_("UUID of the objecttype in the Objecttypes API. "),
    )
    objecttype_version = serializers.IntegerField(
        label=_("objecttype version"),
        required=False,
        help_text=_("Version of the objecttype in the Objecttypes API."),
    )
    variables_mapping = ObjecttypeVariableMappingSerializer(
        label=_("variables mapping"),
        many=True,
        required=False,
    )


class FormVariableListSerializer(ListWithChildSerializer):
    def get_child_serializer_class(self):
        return FormVariableSerializer

    def process_object(self, variable: FormVariable):
        variable.check_data_type_and_initial_value()
        return variable

    def preprocess_validated_data(self, validated_data):
        def save_fetch_config(data):
            if config := data.get("service_fetch_configuration"):
                config.save()
                data["service_fetch_configuration"] = config.instance
            return data

        return map(save_fetch_config, validated_data)

    def validate(self, attrs):
        static_data_keys = [item.key for item in get_static_variables()]

        existing_form_key_combinations = []

        errors = defaultdict(list)

        for index, item in enumerate(attrs):
            key_form_combination = (item["key"], item["form"].slug)
            if key_form_combination in existing_form_key_combinations:
                errors[f"{index}.key"].append(
                    serializers.ErrorDetail(
                        _("The variable key must be unique within a form"),
                        code="unique",
                    )
                )
                continue

            if item["key"] in static_data_keys:
                errors[f"{index}.key"].append(
                    serializers.ErrorDetail(
                        _(
                            "The variable key cannot be equal to any of the following values: {static_data}."
                        ).format(static_data=", ".join(static_data_keys)),
                        code="unique",
                    )
                )
                continue

            existing_form_key_combinations.append(key_form_combination)

        if errors:
            raise ValidationError(errors)

        return attrs


# TODO transform in polymorphic serializer to validate on different types of initial values?

# Performance notes: when doing stuff in bulk, every serializer is validated individually,
# meaning it does a lookup for ``form`` and ``form_definition`` for EVERY variable.
# This means that (out of the box) at least O(2*n) queries are performed, with ``n`` the
# number of component # variables, and an additional O(m) queries with ``m`` the number
# of user-defined variables.
#
# We can reduce this by not querying for the form and instead rely on the serializer
# context (the form is looked up in the viewset). We can further optimize this by
# prefetching the form definitions used in the form and put that in the serializer
# context, making it easier to lookup the values without having to do DB queries to
# validate them (and there will also be duplicate results).


class FormVariableSerializer(serializers.HyperlinkedModelSerializer):
    form = RelatedFieldFromContext(
        queryset=Form.objects.all(),
        view_name="api:form-detail",
        lookup_field="uuid",
        lookup_url_kwarg="uuid_or_slug",
        label=FormVariable._meta.get_field("form").verbose_name,
        help_text=FormVariable._meta.get_field("form").help_text,
        required=True,
        context_name="forms",
    )
    form_definition = RelatedFieldFromContext(
        queryset=FormDefinition.objects.all(),
        view_name="api:formdefinition-detail",
        lookup_field="uuid",
        lookup_url_kwarg="uuid",
        label=FormVariable._meta.get_field("form_definition").verbose_name,
        help_text=FormVariable._meta.get_field("form_definition").help_text,
        required=False,
        allow_null=True,
        context_name="form_definitions",
    )
    service_fetch_configuration = ServiceFetchConfigurationSerializer(
        required=False, allow_null=True
    )
    prefill_options = FormVariableOptionsSerializer(required=False)

    class Meta:
        model = FormVariable
        list_serializer_class = FormVariableListSerializer
        fields = (
            "form",
            "form_definition",
            "name",
            "key",
            "source",
            "service_fetch_configuration",
            "prefill_plugin",
            "prefill_attribute",
            "prefill_identifier_role",
            "prefill_options",
            "data_type",
            "data_format",
            "is_sensitive_data",
            "initial_value",
        )
        # note that DRF by default generates a UniqueTogetherValidator on (form, key).
        # We removed this validator for performance reasons, as it's doing a query for
        # every variable in the bulk update call, leading to O(n) queries with ``n``
        # the amount of variables.
        # The (bulk) API endpoint(s) and this ListSerializer are responsible for
        # applying this validation on the whole collection.
        validators = []

    def validate_service_fetch_configuration(self, value):
        if value is None:
            return value
        config_instance = None
        if config_id := value.get("id"):
            try:
                config_instance = ServiceFetchConfiguration.objects.get(id=config_id)
            except ServiceFetchConfiguration.DoesNotExist:
                raise ValidationError(
                    _(
                        "The service fetch configuration with identifier {config_id} does not exist"
                    ).format(config_id=config_id),
                    code="not_found",
                )

        value["service"] = reverse(
            "api:service-detail", kwargs={"pk": value["service"].pk}
        )
        config = ServiceFetchConfigurationSerializer(
            data=value, instance=config_instance
        )
        config.is_valid(raise_exception=True)
        return config

    def validate(self, attrs):
        if (form_definition := attrs.get("form_definition")) and attrs.get(
            "source"
        ) == FormVariableSources.component:
            config_wrapper = form_definition.configuration_wrapper
            component = config_wrapper.component_map.get(attrs["key"])
            if not component:
                raise ValidationError(
                    {
                        "key": _(
                            "Invalid component variable: "
                            "no component with corresponding key present in the form definition."
                        )
                    }
                )

        # Check the combination of the provided prefill-attributes (see the model constraints)
        source = attrs.get("source") or ""
        prefill_plugin = attrs.get("prefill_plugin") or ""
        prefill_attribute = attrs.get("prefill_attribute") or ""
        prefill_options = attrs.get("prefill_options")

        if prefill_plugin and prefill_options and prefill_attribute:
            raise ValidationError(
                {
                    "prefill_attribute_options": _(
                        "Prefill plugin, attribute and options can not be specified at the same time."
                    ),
                }
            )

        if source == FormVariableSources.component:
            if prefill_options:
                raise ValidationError(
                    {
                        "component_prefill_attribute": _(
                            "Prefill options should not be specified for component variables."
                        ),
                    }
                )
            if not prefill_plugin and prefill_attribute:
                raise ValidationError(
                    {
                        "component_prefill_attribute": _(
                            "Prefill attribute cannot be specified without prefill plugin for component variables."
                        ),
                    }
                )

        return attrs
