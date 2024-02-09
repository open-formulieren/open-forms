from unittest.mock import patch

import requests_mock
from rest_framework import status
from rest_framework.reverse import reverse_lazy
from rest_framework.test import APITestCase
from zgw_consumers.models import Service

from openforms.accounts.tests.factories import StaffUserFactory, UserFactory

from ..models import ObjectsAPIConfig


@requests_mock.Mocker()
class ObjecttypesAPIEndpointsTests(APITestCase):

    def setUp(self) -> None:
        super().setUp()

        self.endpoint = reverse_lazy("api:objects_api:object-types")

        patcher = patch(
            "openforms.registrations.contrib.objects_api.client.ObjectsAPIConfig.get_solo",
            return_value=ObjectsAPIConfig(
                objecttypes_service=Service(api_root="https://objecttypen.nl/api/v2/")
            ),
        )

        self.config_mock = patcher.start()
        self.addCleanup(patcher.stop)

    def test_auth_required(self, m):
        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_user_required(self, m: requests_mock.Mocker):
        m.get(
            "https://objecttypen.nl/api/v2/objecttypes",
            json={"count": 0, "next": None, "previous": None, "results": []},
        )

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

    def test_list_objecttypes(self, m: requests_mock.Mocker):
        m.get(
            "https://objecttypen.nl/api/v2/objecttypes",
            json={
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    {
                        "url": "https://objecttypen.nl/api/v2/objecttypes/2c77babf-a967-4057-9969-0200320d23f1",
                        "uuid": "2c77babf-a967-4057-9969-0200320d23f1",
                        "name": "Tree",
                        "namePlural": "Trees",
                    }
                ],
            },
        )

        staff_user = StaffUserFactory.create()
        self.client.force_authenticate(user=staff_user)

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            [
                {
                    "url": "https://objecttypen.nl/api/v2/objecttypes/2c77babf-a967-4057-9969-0200320d23f1",
                    "uuid": "2c77babf-a967-4057-9969-0200320d23f1",
                    "name": "Tree",
                    "namePlural": "Trees",
                }
            ],
        )


@requests_mock.Mocker()
class ObjecttypeVersionsAPIEndpointsTests(APITestCase):

    def setUp(self) -> None:
        super().setUp()
        self.objecttype_uuid = "2c77babf-a967-4057-9969-0200320d23f1"
        self.endpoint = reverse_lazy(
            "api:objects_api:object-type-versions", args=[self.objecttype_uuid]
        )

        patcher = patch(
            "openforms.registrations.contrib.objects_api.client.ObjectsAPIConfig.get_solo",
            return_value=ObjectsAPIConfig(
                objecttypes_service=Service(api_root="https://objecttypen.nl/api/v2/")
            ),
        )

        self.config_mock = patcher.start()
        self.addCleanup(patcher.stop)

    def test_auth_required(self, m):
        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_user_required(self, m: requests_mock.Mocker):
        m.get(
            f"https://objecttypen.nl/api/v2/objecttypes/{self.objecttype_uuid}/versions",
            json={"count": 0, "next": None, "previous": None, "results": []},
        )

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

    def test_list_objecttype_versions(self, m: requests_mock.Mocker):
        m.get(
            f"https://objecttypen.nl/api/v2/objecttypes/{self.objecttype_uuid}/versions",
            json={
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    {
                        "url": f"https://objecttypen.nl/api/v2/objecttypes/{self.objecttype_uuid}/versions",
                        "version": 1,
                        "status": "published",
                    }
                ],
            },
        )

        staff_user = StaffUserFactory.create()
        self.client.force_authenticate(user=staff_user)

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            [
                {
                    "version": 1,
                    "status": "published",
                }
            ],
        )
