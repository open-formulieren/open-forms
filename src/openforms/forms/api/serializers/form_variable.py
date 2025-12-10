from collections import defaultdict

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from openforms.api.fields import RelatedFieldFromContext
from openforms.api.serializers import ListWithChildSerializer
from openforms.prefill.contrib.customer_interactions.constants import (
    PLUGIN_IDENTIFIER as COMMUNICATION_PREFERENCES_PLUGIN_IDENTIFIER,
)
from openforms.prefill.registry import register
from openforms.variables.api.serializers import ServiceFetchConfigurationSerializer
from openforms.variables.constants import FormVariableSources
from openforms.variables.models import ServiceFetchConfiguration
from openforms.variables.service import get_static_variables

from ...models import Form, FormDefinition, FormVariable


def save_fetch_config(data):
    if config := data.get("service_fetch_configuration"):
        config.save()
        data["service_fetch_configuration"] = config.instance
    return data


class FormVariableListSerializer(ListWithChildSerializer):
    bulk_create_kwargs = {
        "update_conflicts": True,
        "update_fields": (
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
        ),
        "unique_fields": ("form", "key"),
    }

    def get_child_serializer_class(self):
        return FormVariableSerializer

    def process_object(self, obj: FormVariable):
        obj.check_data_type_and_initial_value()
        return obj

    def preprocess_validated_data(self, validated_data):
        # only process not-component variables, as those are managed via the form
        # step endpoint
        validated_data = [
            item
            for item in validated_data
            if (item["source"] != FormVariableSources.component)
        ]
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

        existing_profile_form_vars: list[str] = []

        # Validate the uniqueness of variables using the communication preferences prefill plugin.
        # Keeping this separate from the above key validation, as they aren't related.
        for index, variable in enumerate(attrs):
            prefill_plugin = variable.get("prefill_plugin")
            prefill_options = variable.get("prefill_options")

            if (
                prefill_plugin != COMMUNICATION_PREFERENCES_PLUGIN_IDENTIFIER
                or not prefill_options
            ):
                continue

            profile_form_variable = prefill_options.get("profile_form_variable")
            if profile_form_variable in existing_profile_form_vars:
                errors[f"{index}.prefill_options.profile_form_variable"].append(
                    serializers.ErrorDetail(
                        _(
                            "This profile form variable is already used in another "
                            "communication preferences prefill plugin."
                        ),
                        code="invalid",
                    )
                )
                continue

            existing_profile_form_vars.append(profile_form_variable)

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
    prefill_options = serializers.JSONField(required=False)

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
                    "prefill_attribute": _(
                        "Prefill plugin, attribute and options can not be specified at the same time."
                    ),
                }
            )

        if prefill_options:
            if source == FormVariableSources.component:
                raise ValidationError(
                    {
                        "prefill_options": _(
                            "Prefill options should not be specified for component variables."
                        ),
                    }
                )

        if (prefill_plugin and not (prefill_attribute or prefill_options)) or (
            not prefill_plugin and (prefill_attribute or prefill_options)
        ):
            raise ValidationError(
                _(
                    "Prefill plugin must be specified with either prefill attribute or prefill options."
                )
            )

        # check the specific validation options of the prefill plugin
        if prefill_plugin and prefill_options:
            plugin = register[prefill_plugin]
            serializer = plugin.options(
                data=prefill_options, context={"form": attrs["form"]}
            )
            try:
                serializer.is_valid(raise_exception=True)
            except serializers.ValidationError as e:
                detail = {"prefill_options": e.detail}
                raise serializers.ValidationError(detail) from e

        return attrs
