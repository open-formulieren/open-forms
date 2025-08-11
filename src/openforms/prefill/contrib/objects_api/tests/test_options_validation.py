import uuid

from rest_framework.test import APITestCase

from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory

from ..api.serializers import ObjectsAPIOptionsSerializer


class OptionValidationTests(APITestCase):
    """
    Test the serializer used for options validation.
    """

    def test_auth_attribute_not_required(self):
        api_group = ObjectsAPIGroupConfigFactory.create()
        data = {
            "objects_api_group": api_group.identifier,
            "objecttype_uuid": uuid.uuid4(),
            "objecttype_version": 3,
            "skip_ownership_check": True,
            "auth_attribute_path": [],
            "variables_mapping": [],
        }
        serializer = ObjectsAPIOptionsSerializer(data=data)

        is_valid = serializer.is_valid()

        self.assertTrue(is_valid)

    def test_auth_attribute_required(self):
        api_group = ObjectsAPIGroupConfigFactory.create()
        data = {
            "objects_api_group": api_group.identifier,
            "objecttype_uuid": uuid.uuid4(),
            "objecttype_version": 3,
            "skip_ownership_check": False,
            "auth_attribute_path": [],
            "variables_mapping": [],
        }
        serializer = ObjectsAPIOptionsSerializer(data=data)

        is_valid = serializer.is_valid()

        self.assertFalse(is_valid)
        error = serializer.errors["auth_attribute_path"][0]
        self.assertEqual(error.code, "empty")
