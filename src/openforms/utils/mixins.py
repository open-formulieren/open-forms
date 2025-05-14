from django.contrib.auth.mixins import UserPassesTestMixin

from drf_jsonschema_serializer import to_jsonschema
from drf_polymorphic.serializers import PolymorphicSerializer

from openforms.api.utils import underscore_to_camel


def _camelize_required(schema: dict):
    """
    Camelize the `required` field names, which are not picked up by drf camel case.
    """
    new = {**schema}
    # recurse
    for key, value in schema.items():
        if isinstance(value, list):
            new[key] = [
                _camelize_required(nested) if isinstance(nested, dict) else nested
                for nested in value
            ]
        elif isinstance(value, dict):
            new[key] = _camelize_required(value)

    # does it look like a proper schema?
    if "type" in schema and "properties" in schema:
        if required := schema.get("required"):
            assert isinstance(required, list)
            new["required"] = [underscore_to_camel(field) for field in required]

    return new


class JsonSchemaSerializerMixin:
    @classmethod
    def _add_polymorphic_items_to_jsonschema(cls, json_schema: dict):
        """
        Add polymorphic items to a jsonschema schema.

        Polymorphic items (from drf_polymorphic) are statically not available, as they
        rely on their "discriminator_field" to define its shape. To add the entire
        polymorphic shape to a jsonschema, each polymorphic item needs to be manually
        transformed to a json schema.

        JSON schemas only support polymorphic items via "anyOf" definitions. This setup
        lacks any connection between a discriminator and the polymorphic shape, making it
        impossible to know which shape should be part of the schema at any time. To
        create such a relationship, some custom definitions are required.

        .. note:: The `discriminator` schema property, and its structure, are unknown by
           JSON schema, so any regular JSON schema validation won't validate these parts.

        :param json_schema: jsonschema schema to add polymorphic items to.
        """
        discriminator_field = cls().discriminator_field
        polymorphic_mappings = {}

        # Generate json schema for all polymorphic shapes
        for key, PolymorphicItemSerializer in cls().serializer_mapping.items():
            item_schema = to_jsonschema(PolymorphicItemSerializer())
            item_schema = _camelize_required(item_schema)

            polymorphic_mappings[key.value] = item_schema

        # Add custom (not supported by JSON schema) discriminator mapping to json_schema
        json_schema["discriminator"] = {
            "propertyName": discriminator_field,
            "mappings": polymorphic_mappings,
        }
        # Add polymorphic shapes as anyOf to json_schema, supported by JSON schema
        json_schema["anyOf"] = list(polymorphic_mappings.values())

    @classmethod
    def display_as_jsonschema(cls):
        json_schema = to_jsonschema(cls())

        if issubclass(cls, PolymorphicSerializer):
            cls()._add_polymorphic_items_to_jsonschema(json_schema)

        json_schema = _camelize_required(json_schema)
        return json_schema


class UserIsStaffMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff
