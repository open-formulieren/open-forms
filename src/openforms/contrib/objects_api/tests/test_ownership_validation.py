from pathlib import Path
from unittest.mock import patch

from django.core.exceptions import PermissionDenied
from django.test import TestCase, override_settings, tag

from requests.exceptions import RequestException
from vcr.config import VCR

from openforms.authentication.service import AuthAttribute
from openforms.contrib.objects_api.clients import get_objects_client
from openforms.contrib.objects_api.helpers import prepare_data_for_registration
from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory
from openforms.forms.tests.factories import FormRegistrationBackendFactory
from openforms.logging.models import TimelineLogProxy
from openforms.registrations.contrib.objects_api.plugin import ObjectsAPIRegistration
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.utils.tests.vcr import OFVCRMixin

from ..ownership_validation import validate_object_ownership

TEST_FILES = (Path(__file__).parent / "files").resolve()


PLUGIN = ObjectsAPIRegistration("test")


@override_settings(
    CORS_ALLOW_ALL_ORIGINS=False,
    ALLOWED_HOSTS=["*"],
    CORS_ALLOWED_ORIGINS=["http://testserver.com"],
)
class ObjectsAPIInitialDataOwnershipValidatorTests(OFVCRMixin, TestCase):
    VCR_TEST_FILES = TEST_FILES

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.objects_api_group_used = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True
        )

        # Explicitly define a cassette for Object creation, because running this in
        # setUpTestData doesn't record cassettes by default
        cassette_path = Path(
            cls.VCR_TEST_FILES
            / "vcr_cassettes"
            / cls.__qualname__
            / "setUpTestData.yaml"
        )
        with VCR().use_cassette(cassette_path):
            with get_objects_client(cls.objects_api_group_used) as client:
                object = client.create_object(
                    record_data=prepare_data_for_registration(
                        data={"bsn": "111222333", "foo": "bar"},
                        objecttype_version=1,
                    ),
                    objecttype_url="http://objecttypes-web:8000/api/v2/objecttypes/8faed0fa-7864-4409-aa6d-533a37616a9e",
                )
            cls.object_ref = object["uuid"]

    @tag("gh-4398")
    def test_user_is_owner_of_object(self):
        submission = SubmissionFactory.create(
            auth_info__value="111222333",
            auth_info__attribute=AuthAttribute.bsn,
            initial_data_reference=self.object_ref,
        )

        # An objects API backend with a different API group
        FormRegistrationBackendFactory.create(
            form=submission.form,
            backend="objects_api",
            options={
                "version": 2,
                "objecttype": "3edfdaf7-f469-470b-a391-bb7ea015bd6f",
                "objects_api_group": 5,
                "objecttype_version": 1,
            },
        )
        # Another backend that should be ignored
        FormRegistrationBackendFactory.create(form=submission.form, backend="email")
        # The backend that should be used to perform the check
        FormRegistrationBackendFactory.create(
            form=submission.form,
            backend="objects_api",
            options={
                "version": 2,
                "objecttype": "3edfdaf7-f469-470b-a391-bb7ea015bd6f",
                "objects_api_group": self.objects_api_group_used.pk,
                "objecttype_version": 1,
            },
        )

        with get_objects_client(self.objects_api_group_used) as client:
            validate_object_ownership(submission, client, ["bsn"], PLUGIN)

    @tag("gh-4398")
    def test_permission_denied_if_user_is_not_logged_in(self):
        submission = SubmissionFactory.create(initial_data_reference=self.object_ref)

        with get_objects_client(self.objects_api_group_used) as client:
            with self.assertRaises(PermissionDenied) as cm:
                validate_object_ownership(submission, client, ["bsn"], PLUGIN)
        self.assertEqual(
            str(cm.exception), "Cannot pass data reference as anonymous user"
        )

        logs = TimelineLogProxy.objects.filter(object_id=submission.id)
        self.assertEqual(
            logs.filter(
                extra_data__log_event="object_ownership_check_anonymous_user"
            ).count(),
            1,
        )

    @tag("gh-4398")
    def test_user_is_not_owner_of_object(self):
        submission = SubmissionFactory.create(
            auth_info__value="123456782",
            auth_info__attribute=AuthAttribute.bsn,
            initial_data_reference=self.object_ref,
        )

        # The backend that should be used to perform the check
        FormRegistrationBackendFactory.create(
            form=submission.form,
            backend="objects_api",
            options={
                "version": 2,
                "objecttype": "3edfdaf7-f469-470b-a391-bb7ea015bd6f",
                "objects_api_group": self.objects_api_group_used.pk,
                "objecttype_version": 1,
            },
        )

        with get_objects_client(self.objects_api_group_used) as client:
            with self.assertRaises(PermissionDenied) as cm:
                validate_object_ownership(submission, client, ["bsn"], PLUGIN)
        self.assertEqual(
            str(cm.exception), "User is not the owner of the referenced object"
        )

        logs = TimelineLogProxy.objects.filter(object_id=submission.id)
        self.assertEqual(
            logs.filter(extra_data__log_event="object_ownership_check_failure").count(),
            1,
        )

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

        # The backend that should be used to perform the check
        FormRegistrationBackendFactory.create(
            form=submission.form,
            backend="objects_api",
            options={
                "version": 2,
                "objecttype": "3edfdaf7-f469-470b-a391-bb7ea015bd6f",
                "objects_api_group": self.objects_api_group_used.pk,
                "objecttype_version": 1,
            },
        )

        with get_objects_client(self.objects_api_group_used) as client:
            with self.assertRaises(PermissionDenied) as cm:
                validate_object_ownership(submission, client, ["nested", "bsn"], PLUGIN)
        self.assertEqual(
            str(cm.exception), "User is not the owner of the referenced object"
        )

    @tag("gh-4398")
    @patch(
        "openforms.contrib.objects_api.clients.objects.ObjectsClient.get_object",
        side_effect=RequestException,
    )
    def test_request_exception_when_doing_permission_check(self, mock_get_object):
        """
        If the object could not be fetched due to request errors, the ownership check
        should not fail
        """
        submission = SubmissionFactory.create(
            auth_info__value="111222333",
            auth_info__attribute=AuthAttribute.bsn,
            initial_data_reference=self.object_ref,
        )

        # The backend that should be used to perform the check
        FormRegistrationBackendFactory.create(
            form=submission.form,
            backend="objects_api",
            options={
                "version": 2,
                "objecttype": "3edfdaf7-f469-470b-a391-bb7ea015bd6f",
                "objects_api_group": self.objects_api_group_used.pk,
                "objecttype_version": 1,
            },
        )

        with get_objects_client(self.objects_api_group_used) as client:
            validate_object_ownership(submission, client, ["bsn"], PLUGIN)

    @tag("gh-4398")
    def test_no_backends_configured_does_not_raise_error(
        self,
    ):
        """
        If the object could not be fetched due to misconfiguration, the ownership check
        should not fail
        """
        submission = SubmissionFactory.create(
            auth_info__value="111222333",
            auth_info__attribute=AuthAttribute.bsn,
            initial_data_reference=self.object_ref,
        )
        FormRegistrationBackendFactory.create(form=submission.form, backend="email")

        with get_objects_client(self.objects_api_group_used) as client:
            validate_object_ownership(submission, client, ["bsn"], PLUGIN)

    @tag("gh-4398")
    def test_backend_without_options_does_not_raise_error(
        self,
    ):
        """
        If the object could not be fetched due to missing API group configuration,
        the ownership check should not fail
        """
        submission = SubmissionFactory.create(
            auth_info__value="111222333",
            auth_info__attribute=AuthAttribute.bsn,
            initial_data_reference=self.object_ref,
        )
        ObjectsAPIGroupConfigFactory.create(for_test_docker_compose=True)
        FormRegistrationBackendFactory.create(
            form=submission.form, backend="objects_api", options={}
        )

        with get_objects_client(self.objects_api_group_used) as client:
            validate_object_ownership(submission, client, ["bsn"], PLUGIN)
