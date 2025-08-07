from pathlib import Path

from rest_framework import status
from rest_framework.reverse import reverse_lazy
from rest_framework.test import APITestCase
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from openforms.accounts.tests.factories import StaffUserFactory, UserFactory
from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory
from openforms.utils.tests.feature_flags import enable_feature_flag
from openforms.utils.tests.vcr import OFVCRMixin

TEST_FILES = Path(__file__).parent / "files"


class ObjecttypesAPIEndpointTests(OFVCRMixin, APITestCase):
    VCR_TEST_FILES = TEST_FILES
    endpoint = reverse_lazy("api:objects_api:object-types")

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        cls.config = ObjectsAPIGroupConfigFactory.create(for_test_docker_compose=True)

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
            self.endpoint, data={"objects_api_group": self.config.identifier}
        )

        tree_objecttype = next(obj for obj in response.json() if obj["name"] == "Tree")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            tree_objecttype,
            {
                "dataClassification": "confidential",
                "name": "Tree",
                "namePlural": "Trees",
                "url": "http://objecttypes-web:8000/api/v2/objecttypes/3edfdaf7-f469-470b-a391-bb7ea015bd6f",
                "uuid": "3edfdaf7-f469-470b-a391-bb7ea015bd6f",
            },
        )

    def test_list_objecttypes_missing_api_group(self):
        staff_user = StaffUserFactory.create()
        self.client.force_authenticate(user=staff_user)

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ObjecttypeVersionsAPIEndpointTests(OFVCRMixin, APITestCase):
    VCR_TEST_FILES = TEST_FILES
    endpoint = reverse_lazy(
        "api:objects_api:object-type-versions",
        args=["3edfdaf7-f469-470b-a391-bb7ea015bd6f"],
    )

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        cls.config = ObjectsAPIGroupConfigFactory.create(for_test_docker_compose=True)

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
            self.endpoint, data={"objects_api_group": self.config.identifier}
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
    VCR_TEST_FILES = TEST_FILES
    endpoint = reverse_lazy("api:registrations_objects_api:target-paths")

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        cls.config = ObjectsAPIGroupConfigFactory.create(for_test_docker_compose=True)

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

    def test_list_target_paths(self):
        staff_user = StaffUserFactory.create()
        self.client.force_authenticate(user=staff_user)

        response = self.client.post(
            self.endpoint,
            data={
                "objecttype": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                "objecttypeVersion": 2,
                "variableJsonSchema": {"type": "string"},
                "objects_api_group": self.config.identifier,
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


class CatalogusAPIEndpointTests(OFVCRMixin, APITestCase):
    VCR_TEST_FILES = TEST_FILES
    endpoint = reverse_lazy("api:objects_api:catalogue-list")

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # create services for the docker-compose Open Zaak instance.
        catalogi_service = ServiceFactory.create(
            api_root="http://localhost:8003/catalogi/api/v1/",
            api_type=APITypes.ztc,
            auth_type=AuthTypes.zgw,
            client_id="test_client_id",
            secret="test_secret_key",
        )
        cls.objects_api_group = ObjectsAPIGroupConfigFactory.create(
            catalogi_service=catalogi_service,
        )

    def test_auth_required(self):
        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_user_required(self):
        user = UserFactory.create()

        with self.subTest(staff=False):
            self.client.force_authenticate(user=user)

            response = self.client.get(self.endpoint)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_catalogus(self):
        staff_user = StaffUserFactory.create()
        self.client.force_authenticate(user=staff_user)

        response = self.client.get(
            self.endpoint,
            data={
                "objects_api_group": self.objects_api_group.pk,
            },
        )

        test_catalogus = [obj for obj in response.json() if obj["domain"] == "TEST"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(test_catalogus), 1)


class GetInformatieObjecttypesViewTests(OFVCRMixin, APITestCase):
    VCR_TEST_FILES = TEST_FILES
    endpoint = reverse_lazy("api:objects_api:document-type-list")

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # create services for the docker-compose Open Zaak instance.
        cls.objects_api_group = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True
        )

    def test_must_be_logged_in_as_admin(self):
        user = UserFactory.create()
        self.client.force_login(user)

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_filter_with_invalid_objects_api_group(self):
        user = StaffUserFactory.create()
        self.client.force_login(user)

        response = self.client.get(self.endpoint, {"objects_api_group": "INVALID"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_objects_api_group(self):
        user = StaffUserFactory.create()
        self.client.force_login(user)

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_with_explicit_objects_api_group(self):
        user = StaffUserFactory.create()
        self.client.force_login(user)

        response = self.client.get(
            self.endpoint, {"objects_api_group": self.objects_api_group.identifier}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        num_document_types = len(data)
        # at least 6 distinct document types are defined in the fixture
        self.assertGreaterEqual(num_document_types, 6)
        # assert that multiple versions are de-duplicated
        num_unique = len(
            {(item["description"], item["catalogueLabel"]) for item in data}
        )
        self.assertEqual(num_unique, num_document_types)

        # check the data types of returned information
        record = data[0]
        expected = {
            "catalogueLabel": str,
            "description": str,
            "url": str,
        }
        for key, type in expected.items():
            with self.subTest(key=key):
                self.assertIsInstance(record[key], type)

    def test_retrieve_filter_by_catalogus(self):
        user = StaffUserFactory.create()
        self.client.force_login(user)

        response = self.client.get(
            self.endpoint,
            {
                "objects_api_group": self.objects_api_group.identifier,
                "catalogue_url": "http://localhost:8003/catalogi/api/v1/catalogussen/bd58635c-793e-446d-a7e0-460d7b04829d",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertGreaterEqual(len(data), 3)
        # we expect only one catalogue to be returned
        catalogi_labels_seen = {item["catalogueLabel"] for item in data}
        self.assertEqual(len(catalogi_labels_seen), 1)
        # check the data types of returned information
        record = data[0]
        expected = {
            "catalogueLabel": str,
            "description": str,
            "url": str,
        }
        for key, type in expected.items():
            with self.subTest(key=key):
                self.assertIsInstance(record[key], type)

    @enable_feature_flag("ZGW_APIS_INCLUDE_DRAFTS")
    def test_allow_unpublished_document_types(self):
        user = StaffUserFactory.create()
        self.client.force_login(user)

        response = self.client.get(
            self.endpoint,
            {
                "objects_api_group": self.objects_api_group.identifier,
                # catalogue in fixture with draft document types
                "catalogue_url": "http://localhost:8003/catalogi/api/v1/catalogussen/aa0e0a50-33f6-4473-99a1-b92bab94e749",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertGreater(len(data), 0)
        has_any_drafts = any(item for item in data if item["isPublished"] is False)
        self.assertTrue(has_any_drafts)
