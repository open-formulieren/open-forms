from django.test import TestCase

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
