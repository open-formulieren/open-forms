from pathlib import Path
from unittest.mock import patch

from rest_framework import status
from rest_framework.reverse import reverse_lazy
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import StaffUserFactory, UserFactory
from openforms.utils.tests.vcr import OFVCRMixin

from .test_objecttypes_client import get_test_config


class ObjecttypesAPIEndpointTests(OFVCRMixin, APITestCase):

    VCR_TEST_FILES = Path(__file__).parent / "files"

    def setUp(self) -> None:
        super().setUp()

        self.endpoint = reverse_lazy("api:objects_api:object-types")

        patcher = patch(
            "openforms.registrations.contrib.objects_api.client.ObjectsAPIConfig.get_solo",
            return_value=get_test_config(),
        )

        self.config_mock = patcher.start()
        self.addCleanup(patcher.stop)

    def test_auth_required(self):
        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_user_required(self):
        user = UserFactory.create()
        staff_user = StaffUserFactory.create()

        with self.subTest(staff=False):
            self.client.force_authenticate(user=user)

            response = self.client.get(self.endpoint)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        with self.subTest(staff=True):
            self.client.force_authenticate(user=staff_user)

            response = self.client.get(self.endpoint)

            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_objecttypes(self):
        staff_user = StaffUserFactory.create()
        self.client.force_authenticate(user=staff_user)

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            [
                {
                    "dataClassification": "confidential",
                    "name": "Tree",
                    "namePlural": "Trees",
                    "url": "http://localhost:8001/api/v2/objecttypes/3edfdaf7-f469-470b-a391-bb7ea015bd6f",
                    "uuid": "3edfdaf7-f469-470b-a391-bb7ea015bd6f",
                },
                {
                    "dataClassification": "open",
                    "name": "Person",
                    "namePlural": "Persons",
                    "url": "http://localhost:8001/api/v2/objecttypes/8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                    "uuid": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                },
            ],
        )


class ObjecttypeVersionsAPIEndpointTests(OFVCRMixin, APITestCase):

    VCR_TEST_FILES = Path(__file__).parent / "files"

    def setUp(self) -> None:
        super().setUp()
        self.objecttype_uuid = "3edfdaf7-f469-470b-a391-bb7ea015bd6f"
        self.endpoint = reverse_lazy(
            "api:objects_api:object-type-versions", args=[self.objecttype_uuid]
        )

        patcher = patch(
            "openforms.registrations.contrib.objects_api.client.ObjectsAPIConfig.get_solo",
            return_value=get_test_config(),
        )

        self.config_mock = patcher.start()
        self.addCleanup(patcher.stop)

    def test_auth_required(self):
        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_user_required(self):
        user = UserFactory.create()
        staff_user = StaffUserFactory.create()

        with self.subTest(staff=False):
            self.client.force_authenticate(user=user)

            response = self.client.get(self.endpoint)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        with self.subTest(staff=True):
            self.client.force_authenticate(user=staff_user)

            response = self.client.get(self.endpoint)

            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_objecttype_versions(self):
        staff_user = StaffUserFactory.create()
        self.client.force_authenticate(user=staff_user)

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [{"status": "published", "version": 1}])

    def test_list_objecttype_verions_unknown_objecttype(self):
        staff_user = StaffUserFactory.create()
        self.client.force_authenticate(user=staff_user)

        # This UUID doesn't exist:
        response = self.client.get(
            reverse_lazy(
                "api:objects_api:object-type-versions",
                args=["39da819c-ac6c-4037-ae2b-6bfc39f6564b"],
            )
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])


class TargetPathsAPIEndpointTests(OFVCRMixin, APITestCase):

    VCR_TEST_FILES = Path(__file__).parent / "files"

    def setUp(self) -> None:
        super().setUp()
        self.user = UserFactory.create()
        self.staff_user = StaffUserFactory.create()

        self.endpoint = reverse_lazy("api:objects_api:target-paths")

        patcher = patch(
            "openforms.registrations.contrib.objects_api.client.ObjectsAPIConfig.get_solo",
            return_value=get_test_config(),
        )

        self.config_mock = patcher.start()
        self.addCleanup(patcher.stop)

    def test_auth_required(self):
        response = self.client.post(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_user_required(self):

        with self.subTest(staff=False):
            self.client.force_authenticate(user=self.user)

            response = self.client.post(self.endpoint)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        with self.subTest(staff=True):
            self.client.force_authenticate(user=self.staff_user)

            response = self.client.post(self.endpoint)

            # Should be a 400 as permissions are ok but missing body
            # (but this is tested in `test_missing_body` and not relevant for this test)
            self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_missing_body(self):
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.post(self.endpoint, data={})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_target_paths(self):
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.post(
            self.endpoint,
            data={
                "objecttypeUrl": "http://localhost:8001/api/v2/objecttypes/8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                "objecttypeVersion": 2,
                "variableJsonSchema": {"type": "string"},
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # The list of targets is constructed from a JSON mapping, which isn't guaranteed
        # to be ordered. So `assertCountEqual` is used (horrible naming, but is <=> unordered `assertListEqual`)
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
