from unittest.mock import patch

from django.core.exceptions import PermissionDenied
from django.test import TestCase, override_settings, tag

from requests.exceptions import HTTPError, RequestException

from openforms.authentication.service import AuthAttribute
from openforms.logging.models import TimelineLogProxy
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.utils.tests.vcr import OFVCRMixin, with_setup_test_data_vcr

from ..clients import get_objects_client
from ..helpers import prepare_data_for_registration
from ..ownership_validation import validate_object_ownership
from .factories import ObjectsAPIGroupConfigFactory


@override_settings(
    CORS_ALLOW_ALL_ORIGINS=False,
    ALLOWED_HOSTS=["*"],
    CORS_ALLOWED_ORIGINS=["http://testserver.com"],
)
class ObjectsAPIInitialDataOwnershipValidatorTests(OFVCRMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.objects_api_group_used = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True
        )

        with (
            with_setup_test_data_vcr(cls),
            get_objects_client(cls.objects_api_group_used) as client,
        ):
            obj = client.create_object(
                record_data=prepare_data_for_registration(
                    data={"bsn": "111222333", "foo": "bar"},
                    objecttype_version=1,
                ),
                objecttype_url="http://objecttypes-web:8000/api/v2/objecttypes/8faed0fa-7864-4409-aa6d-533a37616a9e",
            )
        cls.object_ref = obj["uuid"]

    @tag("gh-4398")
    def test_user_is_owner_of_object(self):
        submission = SubmissionFactory.create(
            auth_info__value="111222333",
            auth_info__attribute=AuthAttribute.bsn,
            initial_data_reference=self.object_ref,
        )

        with get_objects_client(self.objects_api_group_used) as client:
            try:
                validate_object_ownership(submission, client, ["bsn"])
            except PermissionDenied as exc:
                raise self.failureException(
                    "BSN in submission is owner of data"
                ) from exc

    @tag("gh-4398")
    def test_permission_denied_if_user_is_not_logged_in(self):
        submission = SubmissionFactory.create(initial_data_reference=self.object_ref)
        assert not submission.is_authenticated

        with (
            get_objects_client(self.objects_api_group_used) as client,
            self.assertRaisesMessage(
                PermissionDenied, "Cannot pass data reference as anonymous user"
            ),
        ):
            validate_object_ownership(submission, client, ["bsn"])

        logs = TimelineLogProxy.objects.for_object(submission)
        self.assertEqual(
            logs.filter_event("object_ownership_check_anonymous_user").count(), 1
        )

    @tag("gh-4398")
    def test_user_is_not_owner_of_object(self):
        submission = SubmissionFactory.create(
            auth_info__value="123456782",
            auth_info__attribute=AuthAttribute.bsn,
            initial_data_reference=self.object_ref,
        )

        with (
            get_objects_client(self.objects_api_group_used) as client,
            self.assertRaisesMessage(
                PermissionDenied, "User is not the owner of the referenced object"
            ),
        ):
            validate_object_ownership(submission, client, ["bsn"])

        logs = TimelineLogProxy.objects.for_object(submission)
        self.assertEqual(logs.filter_event("object_ownership_check_failure").count(), 1)

    @tag("gh-4398")
    def test_user_is_not_owner_of_object_nested_auth_attribute(self):
        with get_objects_client(self.objects_api_group_used) as client:
            object = client.create_object(
                record_data=prepare_data_for_registration(
                    data={"nested": {"bsn": "111222333"}, "foo": "bar"},
                    objecttype_version=1,
                ),
                objecttype_url="http://objecttypes-web:8000/api/v2/objecttypes/8faed0fa-7864-4409-aa6d-533a37616a9e",
            )
            object_ref = object["uuid"]

        submission = SubmissionFactory.create(
            auth_info__value="123456782",
            auth_info__attribute=AuthAttribute.bsn,
            initial_data_reference=object_ref,
        )

        with (
            get_objects_client(self.objects_api_group_used) as client,
            self.assertRaisesMessage(
                PermissionDenied, "User is not the owner of the referenced object"
            ),
        ):
            validate_object_ownership(submission, client, ["nested", "bsn"])

    @tag("gh-4398")
    def test_ownership_check_fails_if_auth_attribute_path_is_badly_configured(self):
        with get_objects_client(self.objects_api_group_used) as client:
            object = client.create_object(
                record_data=prepare_data_for_registration(
                    data={"nested": {"bsn": "111222333"}, "foo": "bar"},
                    objecttype_version=1,
                ),
                objecttype_url="http://objecttypes-web:8000/api/v2/objecttypes/8faed0fa-7864-4409-aa6d-533a37616a9e",
            )
            object_ref = object["uuid"]

        submission = SubmissionFactory.create(
            auth_info__value="123456782",
            auth_info__attribute=AuthAttribute.bsn,
            initial_data_reference=object_ref,
        )

        with get_objects_client(self.objects_api_group_used) as client:
            with (
                self.subTest("empty path"),
                self.assertRaisesMessage(
                    PermissionDenied,
                    "Could not verify if user is owner of the referenced object",
                ),
            ):
                validate_object_ownership(submission, client, [])

            with (
                self.subTest("non existent path"),
                self.assertRaisesMessage(
                    PermissionDenied,
                    "Could not verify if user is owner of the referenced object",
                ),
            ):
                validate_object_ownership(
                    submission, client, ["this", "does", "not", "exist"]
                )

    @tag("gh-4398")
    @patch(
        "openforms.contrib.objects_api.clients.objects.ObjectsClient.get_object",
        side_effect=RequestException,
    )
    def test_request_exception_when_doing_permission_check(self, mock_get_object):
        """
        If the object could not be fetched due to request errors, the ownership check
        should fail
        """
        submission = SubmissionFactory.create(
            auth_info__value="111222333",
            auth_info__attribute=AuthAttribute.bsn,
            initial_data_reference="irrelevant",
        )
        with get_objects_client(self.objects_api_group_used) as client:
            with self.assertRaises(PermissionDenied):
                validate_object_ownership(submission, client, ["bsn"])

    @tag("gh-4398")
    @patch(
        "openforms.contrib.objects_api.clients.objects.ObjectsClient.get_object",
        side_effect=HTTPError("404"),
    )
    def test_object_not_found_when_doing_permission_check(self, mock_get_object):
        """
        If the object could not be fetched due to request errors, the ownership check
        should fail
        """
        submission = SubmissionFactory.create(
            auth_info__value="111222333",
            auth_info__attribute=AuthAttribute.bsn,
            initial_data_reference="irrelevant",
        )

        with get_objects_client(self.objects_api_group_used) as client:
            with self.assertRaises(PermissionDenied):
                validate_object_ownership(submission, client, ["bsn"])
