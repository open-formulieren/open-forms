from django.test import SimpleTestCase

from ..config import ObjectsAPIOptionsSerializer


class ObjectsAPIOptionsSerializerTest(SimpleTestCase):
    def test_invalid_fields_v1(self):
        options = ObjectsAPIOptionsSerializer(
            data={
                "version": 1,
                "objecttype": "https://objecttypen.nl/api/v2/objecttypes/2c77babf-a967-4057-9969-0200320d23f1",
                "objecttype_version": 1,
                "variables_mapping": [],
            }
        )
        self.assertFalse(options.is_valid())

    def test_invalid_fields_v2(self):
        options = ObjectsAPIOptionsSerializer(
            data={
                "version": 2,
                "objecttype": "https://objecttypen.nl/api/v2/objecttypes/2c77babf-a967-4057-9969-0200320d23f1",
                "objecttype_version": 1,
                "content_json": "dummy",
            }
        )
        self.assertFalse(options.is_valid())

    def test_valid_serializer(self):
        options = ObjectsAPIOptionsSerializer(
            data={
                "version": 1,
                "objecttype": "https://objecttypen.nl/api/v2/objecttypes/2c77babf-a967-4057-9969-0200320d23f1",
                "objecttype_version": 1,
                "content_json": "dummy",
            }
        )
        self.assertTrue(options.is_valid())
