from unittest.mock import patch

from django.core.exceptions import PermissionDenied
from django.test import TestCase, tag

from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory
from openforms.forms.tests.factories import FormFactory, FormRegistrationBackendFactory
from openforms.submissions.constants import PostSubmissionEvents
from openforms.submissions.tasks.registration import pre_registration
from openforms.submissions.tests.factories import SubmissionFactory


class ObjectsAPIPreRegistrationTests(TestCase):
    @tag("gh-4398")
    def test_verify_initial_data_ownership(self):
        objects_api_group_used = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True
        )
        objects_api_group_unused = ObjectsAPIGroupConfigFactory.create()

        form = FormFactory.create()
        # An objects API backend that is missing `auth_attribute_path`
        FormRegistrationBackendFactory.create(
            form=form,
            backend="objects_api",
            options={
                "version": 2,
                "objecttype": "3edfdaf7-f469-470b-a391-bb7ea015bd6f",
                "objects_api_group": objects_api_group_unused.pk,
                "objecttype_version": 1,
            },
        )
        # An objects API backend with a different API group
        FormRegistrationBackendFactory.create(
            form=form,
            backend="objects_api",
            options={
                "version": 2,
                "objecttype": "3edfdaf7-f469-470b-a391-bb7ea015bd6f",
                "objects_api_group": objects_api_group_unused.pk,
                "objecttype_version": 1,
                "auth_attribute_path": ["bsn"],
            },
        )
        # Another backend that should be ignored
        FormRegistrationBackendFactory.create(form=form, backend="email")
        # The backend that should be used to perform the check
        FormRegistrationBackendFactory.create(
            form=form,
            backend="objects_api",
            options={
                "version": 2,
                "objecttype": "3edfdaf7-f469-470b-a391-bb7ea015bd6f",
                "objects_api_group": objects_api_group_used.pk,
                "objecttype_version": 1,
                "auth_attribute_path": ["nested", "bsn"],
            },
        )

        with self.subTest(
            "verify_initial_data_ownership is not called if no initial_data_reference is specified"
        ):
            submission = SubmissionFactory.create(
                form=form,
                completed_not_preregistered=True,
            )

            with patch(
                "openforms.registrations.contrib.objects_api.plugin.validate_object_ownership",
                side_effect=PermissionDenied,
            ) as mock_validate_object_ownership:
                pre_registration(submission.id, PostSubmissionEvents.on_completion)

            mock_validate_object_ownership.assert_not_called()

        with self.subTest(
            "verify_initial_data_ownership is called if initial_data_reference exists is specified"
        ):
            submission = SubmissionFactory.create(
                form=form,
                completed_not_preregistered=True,
                initial_data_reference="1234",
            )

            with patch(
                "openforms.registrations.contrib.objects_api.plugin.validate_object_ownership"
            ) as mock_validate_object_ownership:
                pre_registration(submission.id, PostSubmissionEvents.on_completion)

                self.assertEqual(mock_validate_object_ownership.call_count, 2)

                # Cannot compare with `.assert_has_calls`, because the client objects
                # won't match
                call1, call2 = mock_validate_object_ownership.mock_calls

                self.assertEqual(call1.args[0], submission)
                self.assertEqual(
                    call1.args[1].base_url,
                    objects_api_group_unused.objects_service.api_root,
                )
                self.assertEqual(call1.args[2], ["bsn"])

                self.assertEqual(call2.args[0], submission)
                self.assertEqual(
                    call2.args[1].base_url,
                    objects_api_group_used.objects_service.api_root,
                )
                self.assertEqual(call2.args[2], ["nested", "bsn"])

        with self.subTest(
            "verify_initial_data_ownership raising error causes pre registration to fail"
        ):
            submission = SubmissionFactory.create(
                form=form,
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
                    objects_api_group_unused.objects_service.api_root,
                )
                self.assertEqual(call.args[2], ["bsn"])
