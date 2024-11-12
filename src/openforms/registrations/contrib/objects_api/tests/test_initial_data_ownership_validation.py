from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.test import TestCase, tag

from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory
from openforms.forms.tests.factories import FormFactory, FormRegistrationBackendFactory
from openforms.logging.models import TimelineLogProxy
from openforms.submissions.constants import PostSubmissionEvents
from openforms.submissions.tasks.registration import pre_registration
from openforms.submissions.tests.factories import SubmissionFactory


@tag("gh-4398")
class ObjectsAPIPrefillDataOwnershipCheckTests(TestCase):
    def setUp(self):
        super().setUp()

        self.objects_api_group_used = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True
        )
        self.objects_api_group_unused = ObjectsAPIGroupConfigFactory.create()

        self.form = FormFactory.create()

        # An objects API backend with a different API group
        FormRegistrationBackendFactory.create(
            form=self.form,
            backend="objects_api",
            options={
                "version": 2,
                "objecttype": "3edfdaf7-f469-470b-a391-bb7ea015bd6f",
                "objects_api_group": self.objects_api_group_unused.pk,
                "objecttype_version": 1,
                "auth_attribute_path": ["bsn"],
            },
        )
        # Another backend that should be ignored
        FormRegistrationBackendFactory.create(form=self.form, backend="email")
        # The backend that should be used to perform the check
        self.backend = FormRegistrationBackendFactory.create(
            form=self.form,
            backend="objects_api",
            options={
                "version": 2,
                "objecttype": "3edfdaf7-f469-470b-a391-bb7ea015bd6f",
                "objects_api_group": self.objects_api_group_used.pk,
                "objecttype_version": 1,
                "auth_attribute_path": ["nested", "bsn"],
            },
        )

    def test_verify_initial_data_ownership_not_called_if_initial_data_reference_missing(
        self,
    ):
        submission = SubmissionFactory.create(
            form=self.form,
            completed_not_preregistered=True,
        )

        with patch(
            "openforms.registrations.contrib.objects_api.plugin.validate_object_ownership",
            side_effect=PermissionDenied,
        ) as mock_validate_object_ownership:
            pre_registration(submission.id, PostSubmissionEvents.on_completion)

        mock_validate_object_ownership.assert_not_called()

    def test_verify_initial_data_ownership_called_if_initial_data_reference_specified(
        self,
    ):
        submission = SubmissionFactory.create(
            form=self.form,
            completed_not_preregistered=True,
            initial_data_reference="1234",
            finalised_registration_backend_key=self.backend.key,
        )

        with patch(
            "openforms.registrations.contrib.objects_api.plugin.validate_object_ownership"
        ) as mock_validate_object_ownership:
            pre_registration(submission.id, PostSubmissionEvents.on_completion)

            self.assertEqual(mock_validate_object_ownership.call_count, 1)

            # Cannot compare with `.assert_has_calls`, because the client objects
            # won't match
            call = mock_validate_object_ownership.mock_calls[0]

            self.assertEqual(call.args[0], submission)
            self.assertEqual(
                call.args[1].base_url,
                self.objects_api_group_used.objects_service.api_root,
            )
            self.assertEqual(call.args[2], ["nested", "bsn"])

    def test_verify_initial_data_ownership_raising_error_causes_failing_pre_registration(
        self,
    ):
        submission = SubmissionFactory.create(
            form=self.form,
            completed_not_preregistered=True,
            initial_data_reference="1234",
        )

        with patch(
            "openforms.registrations.contrib.objects_api.plugin.validate_object_ownership",
            side_effect=PermissionDenied,
        ) as mock_validate_object_ownership:
            with self.assertRaises(PermissionDenied):
                pre_registration(submission.id, PostSubmissionEvents.on_completion)
            self.assertEqual(mock_validate_object_ownership.call_count, 1)

            # Cannot compare with `.assert_has_calls`, because the client objects
            # won't match
            call = mock_validate_object_ownership.mock_calls[0]

            self.assertEqual(call.args[0], submission)
            self.assertEqual(
                call.args[1].base_url,
                self.objects_api_group_unused.objects_service.api_root,
            )
            self.assertEqual(call.args[2], ["bsn"])

    def test_verify_initial_data_ownership_missing_auth_attribute_path_causes_failing_pre_registration(
        self,
    ):
        del self.backend.options["auth_attribute_path"]
        self.backend.save()

        submission = SubmissionFactory.create(
            form=self.form,
            completed_not_preregistered=True,
            initial_data_reference="1234",
            finalised_registration_backend_key=self.backend.key,
        )

        with patch(
            "openforms.registrations.contrib.objects_api.plugin.validate_object_ownership",
        ) as mock_validate_object_ownership:
            with self.assertRaises(ImproperlyConfigured):
                pre_registration(submission.id, PostSubmissionEvents.on_completion)

            # Not called, due to missing `auth_attribute_path`
            self.assertEqual(mock_validate_object_ownership.call_count, 0)

        logs = TimelineLogProxy.objects.filter(object_id=submission.id)
        self.assertEqual(
            logs.filter(
                extra_data__log_event="object_ownership_check_improperly_configured"
            ).count(),
            1,
        )
