from pathlib import Path

from rest_framework import status
from rest_framework.reverse import reverse_lazy
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import StaffUserFactory, UserFactory
from openforms.utils.tests.vcr import OFVCRMixin

from .test_objecttypes_client import get_test_config


class ObjecttypesAPIEndpointTests(OFVCRMixin, APITestCase):

    VCR_TEST_FILES = Path(__file__).parent / "files"
    endpoint = reverse_lazy("api:objects_api:object-types")

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        cls.config = get_test_config()
        cls.config.objecttypes_service.save()
        cls.config.save()

    def test_auth_required(self):
        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_user_required(self):
        user = UserFactory.create()

        with self.subTest(staff=False):
            self.client.force_authenticate(user=user)

            response = self.client.get(self.endpoint)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_objecttypes(self):
        staff_user = StaffUserFactory.create()
        self.client.force_authenticate(user=staff_user)

        response = self.client.get(
            self.endpoint, data={"objects_api_group": self.config.pk}
        )

        tree_objecttype = next(obj for obj in response.json() if obj["name"] == "Tree")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            tree_objecttype,
            {
                "dataClassification": "confidential",
                "name": "Tree",
                "namePlural": "Trees",
                "url": "http://localhost:8001/api/v2/objecttypes/3edfdaf7-f469-470b-a391-bb7ea015bd6f",
                "uuid": "3edfdaf7-f469-470b-a391-bb7ea015bd6f",
            },
        )

    def test_list_objecttypes_missing_api_group(self):
        staff_user = StaffUserFactory.create()
        self.client.force_authenticate(user=staff_user)

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ObjecttypeVersionsAPIEndpointTests(OFVCRMixin, APITestCase):

    VCR_TEST_FILES = Path(__file__).parent / "files"
    endpoint = reverse_lazy(
        "api:objects_api:object-type-versions",
        args=["3edfdaf7-f469-470b-a391-bb7ea015bd6f"],
    )

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        cls.config = get_test_config()
        cls.config.objecttypes_service.save()
        cls.config.save()

    def test_auth_required(self):
        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_user_required(self):
        user = UserFactory.create()

        with self.subTest(staff=False):
            self.client.force_authenticate(user=user)

            response = self.client.get(self.endpoint)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_objecttype_versions(self):
        staff_user = StaffUserFactory.create()
        self.client.force_authenticate(user=staff_user)

        response = self.client.get(
            self.endpoint, data={"objects_api_group": self.config.pk}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [{"status": "published", "version": 1}])

    def test_list_objecttype_versions_unknown_objecttype(self):
        staff_user = StaffUserFactory.create()
        self.client.force_authenticate(user=staff_user)

        # This UUID doesn't exist:
        response = self.client.get(
            reverse_lazy(
                "api:objects_api:object-type-versions",
                args=["39da819c-ac6c-4037-ae2b-6bfc39f6564b"],
            ),
            data={"objects_api_group": self.config.pk},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])


class TargetPathsAPIEndpointTests(OFVCRMixin, APITestCase):

    VCR_TEST_FILES = Path(__file__).parent / "files"
    endpoint = reverse_lazy("api:objects_api:target-paths")

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        cls.config = get_test_config()
        cls.config.objecttypes_service.save()
        cls.config.save()

    def test_auth_required(self):
        response = self.client.post(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_user_required(self):
        user = UserFactory.create()

        with self.subTest(staff=False):
            self.client.force_authenticate(user=user)

            response = self.client.get(self.endpoint)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_missing_body(self):
        staff_user = StaffUserFactory.create()
        self.client.force_authenticate(user=staff_user)

        response = self.client.post(self.endpoint, data={})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_wrong_uuid_parsing(self):
        staff_user = StaffUserFactory.create()
        self.client.force_authenticate(user=staff_user)

        response = self.client.post(
            self.endpoint,
            data={
                "objecttypeUrl": "http://localhost:8001/api/v2/objecttypes/bad_uuid",
                "objecttypeVersion": 1,
                "variableJsonSchema": {"type": "string"},
                "objects_api_group": self.config.pk,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual("objecttypeUrl", response.json()["invalidParams"][0]["name"])

    def test_list_target_paths(self):
        staff_user = StaffUserFactory.create()
        self.client.force_authenticate(user=staff_user)

        response = self.client.post(
            self.endpoint,
            data={
                "objecttypeUrl": "http://localhost:8001/api/v2/objecttypes/8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                "objecttypeVersion": 2,
                "variableJsonSchema": {"type": "string"},
                "objects_api_group": self.config.pk,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # The list of targets is constructed from a JSON mapping, which isn't guaranteed
        # to be ordered. So `assertCountEqual` is used (a.k.a. unordered `assertListEqual`).
        self.assertCountEqual(
            response.json(),
            [
                {
                    "targetPath": ["firstName"],
                    "isRequired": False,
                    "jsonSchema": {
                        "type": "string",
                        "description": "The person's first name.",
                    },
                },
                {
                    "targetPath": ["lastName"],
                    "isRequired": False,
                    "jsonSchema": {
                        "type": "string",
                        "description": "The person's last name.",
                    },
                },
            ],
        )
