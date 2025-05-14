from django.db import models
from django.test import TestCase

from drf_polymorphic.serializers import PolymorphicSerializer
from rest_framework import serializers

from openforms.accounts.models import User
from openforms.accounts.tests.factories import UserFactory
from openforms.utils.mixins import JsonSchemaSerializerMixin

from ..fields import PrimaryKeyRelatedAsChoicesField


class PrimaryKeyRelatedAsChoicesFieldConverterTests(TestCase):
    def test_db_objects_serialized_as_enum(self):
        user1 = UserFactory.create(username="bob")
        user2 = UserFactory.create(username="alice")

        class TestSerializer(JsonSchemaSerializerMixin, serializers.Serializer):
            user = PrimaryKeyRelatedAsChoicesField(
                queryset=User.objects.order_by("id"),
                required=False,
                help_text="Select user",
            )

        schema = TestSerializer.display_as_jsonschema()

        expected_schema = {
            "type": "integer",
            "title": "User",
            "description": "Select user",
            "enum": [user1.id, user2.id],
            "enumNames": ["bob", "alice"],
        }
        self.assertEqual(schema["properties"]["user"], expected_schema)


class PolymorphicSerializerConverterTests(TestCase):
    def test_converted_polymorphic_object_contains_all_polymorphic_shapes(self):
        class TestPolymorphicTypes(models.TextChoices):
            a = "a", "A"
            b = "b", "B"

        class TestPolymorphicShapeASerializer(serializers.Serializer):
            field_of_shape_a = serializers.CharField(
                label="Shape A field", required=False
            )

        class TestPolymorphicShapeBSerializer(serializers.Serializer):
            field_of_shape_b = serializers.CharField(
                label="Shape B field", required=True
            )

        class TestPolymorphicSerializer(
            JsonSchemaSerializerMixin, PolymorphicSerializer, serializers.Serializer
        ):
            field = serializers.CharField(label="Field", required=True)
            type = serializers.ChoiceField(
                label="Type", choices=TestPolymorphicTypes.choices, required=False
            )

            discriminator_field = "type"
            serializer_mapping = {
                TestPolymorphicTypes.a: TestPolymorphicShapeASerializer,
                TestPolymorphicTypes.b: TestPolymorphicShapeBSerializer,
            }

        schema = TestPolymorphicSerializer.display_as_jsonschema()

        expected_schema = {
            "type": "object",
            "properties": {
                "field": {
                    "title": "Field",
                    "type": "string",
                    "minLength": 1,
                },
                "type": {
                    "title": "Type",
                    "type": "string",
                    "enum": ["a", "b"],
                    "enumNames": ["A", "B"],
                },
            },
            "required": ["field"],
            "discriminator": {
                "propertyName": "type",
                "mappings": {
                    "a": {
                        "type": "object",
                        "properties": {
                            "field_of_shape_a": {
                                "title": "Shape A field",
                                "type": "string",
                                "minLength": 1,
                            },
                        },
                    },
                    "b": {
                        "type": "object",
                        "properties": {
                            "field_of_shape_b": {
                                "title": "Shape B field",
                                "type": "string",
                                "minLength": 1,
                            },
                        },
                        "required": ["fieldOfShapeB"],
                    },
                },
            },
            "anyOf": [
                {
                    "type": "object",
                    "properties": {
                        "field_of_shape_a": {
                            "title": "Shape A field",
                            "type": "string",
                            "minLength": 1,
                        },
                    },
                },
                {
                    "type": "object",
                    "properties": {
                        "field_of_shape_b": {
                            "title": "Shape B field",
                            "type": "string",
                            "minLength": 1,
                        },
                    },
                    "required": ["fieldOfShapeB"],
                },
            ],
        }

        self.assertEqual(schema, expected_schema)
