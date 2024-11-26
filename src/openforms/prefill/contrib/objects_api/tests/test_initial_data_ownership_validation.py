from pathlib import Path
from unittest.mock import patch

from django.core.exceptions import PermissionDenied
from django.test import TestCase, tag

from openforms.authentication.service import AuthAttribute
from openforms.contrib.objects_api.clients import get_objects_client
from openforms.contrib.objects_api.helpers import prepare_data_for_registration
from openforms.contrib.objects_api.models import ObjectsAPIGroupConfig
from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory
from openforms.forms.tests.factories import (
    FormFactory,
    FormRegistrationBackendFactory,
    FormStepFactory,
    FormVariableFactory,
)
from openforms.logging.models import TimelineLogProxy
from openforms.prefill.service import prefill_variables
from openforms.submissions.tests.factories import SubmissionStepFactory
from openforms.utils.tests.vcr import OFVCRMixin, with_setup_test_data_vcr

TEST_FILES = (Path(__file__).parent / "files").resolve()


@tag("gh-4398")
class ObjectsAPIPrefillDataOwnershipCheckTests(OFVCRMixin, TestCase):
    VCR_TEST_FILES = TEST_FILES

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.objects_api_group_used = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True
        )

        with with_setup_test_data_vcr(cls.VCR_TEST_FILES, cls.__qualname__):
            with get_objects_client(cls.objects_api_group_used) as client:
                object = client.create_object(
                    record_data=prepare_data_for_registration(
                        data={"bsn": "111222333", "some": {"path": "foo"}},
                        objecttype_version=1,
                    ),
                    objecttype_url="http://objecttypes-web:8000/api/v2/objecttypes/8faed0fa-7864-4409-aa6d-533a37616a9e",
                )
            cls.object_ref = object["uuid"]

        cls.objects_api_group_used = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True
        )
        cls.objects_api_group_unused = ObjectsAPIGroupConfigFactory.create()

        cls.form = FormFactory.create()
        # An objects API backend with a different API group
        FormRegistrationBackendFactory.create(
            form=cls.form,
            backend="objects_api",
            options={
                "version": 2,
                "objecttype": "3edfdaf7-f469-470b-a391-bb7ea015bd6f",
                "objects_api_group": cls.objects_api_group_unused.pk,
                "objecttype_version": 1,
            },
        )
        # Another backend that should be ignored
        FormRegistrationBackendFactory.create(form=cls.form, backend="email")
        # The backend that should be used to perform the check
        FormRegistrationBackendFactory.create(
            form=cls.form,
            backend="objects_api",
            options={
                "version": 2,
                "objecttype": "3edfdaf7-f469-470b-a391-bb7ea015bd6f",
                "objects_api_group": cls.objects_api_group_used.pk,
                "objecttype_version": 1,
            },
        )

        cls.form_step = FormStepFactory.create(
            form_definition__configuration={
                "components": [
                    {
                        "type": "postcode",
                        "key": "postcode",
                        "inputMask": "9999 AA",
                    }
                ]
            }
        )
        cls.variable = FormVariableFactory.create(
            key="voornamen",
            form=cls.form_step.form,
            prefill_plugin="objects_api",
            prefill_attribute="",
            prefill_options={
                "version": 2,
                "objecttype": "3edfdaf7-f469-470b-a391-bb7ea015bd6f",
                "objects_api_group": cls.objects_api_group_used.pk,
                "objecttype_version": 1,
                "auth_attribute_path": ["nested", "bsn"],
                "variables_mapping": [
                    {"variable_key": "voornamen", "target_path": ["some", "path"]},
                ],
            },
        )

    def test_verify_initial_data_ownership_called_if_initial_data_reference_specified(
        self,
    ):
        submission_step = SubmissionStepFactory.create(
            submission__form=self.form_step.form,
            form_step=self.form_step,
            submission__auth_info__value="999990676",
            submission__auth_info__attribute=AuthAttribute.bsn,
            submission__initial_data_reference=self.object_ref,
        )

        with patch(
            "openforms.prefill.contrib.objects_api.plugin.validate_object_ownership"
        ) as mock_validate_object_ownership:
            prefill_variables(submission=submission_step.submission)

            self.assertEqual(mock_validate_object_ownership.call_count, 1)

            # Cannot compare with `.assert_has_calls`, because the client objects
            # won't match
            call = mock_validate_object_ownership.mock_calls[0]

            self.assertEqual(call.args[0], submission_step.submission)
            self.assertEqual(
                call.args[1].base_url,
                self.objects_api_group_used.objects_service.api_root,
            )
            self.assertEqual(call.args[2], ["nested", "bsn"])

        logs = TimelineLogProxy.objects.filter(object_id=submission_step.submission.id)

        self.assertEqual(
            logs.filter(extra_data__log_event="prefill_retrieve_success").count(), 1
        )

    def test_verify_initial_data_ownership_raising_errors_causes_prefill_to_fail(self):
        submission_step = SubmissionStepFactory.create(
            submission__form=self.form_step.form,
            form_step=self.form_step,
            submission__auth_info__value="999990676",
            submission__auth_info__attribute=AuthAttribute.bsn,
            submission__initial_data_reference=self.object_ref,
        )

        with patch(
            "openforms.prefill.contrib.objects_api.plugin.validate_object_ownership",
            side_effect=PermissionDenied,
        ) as mock_validate_object_ownership:
            prefill_variables(submission=submission_step.submission)

            self.assertEqual(mock_validate_object_ownership.call_count, 1)

            # Cannot compare with `.assert_has_calls`, because the client objects
            # won't match
            call = mock_validate_object_ownership.mock_calls[0]

            self.assertEqual(call.args[0], submission_step.submission)
            self.assertEqual(
                call.args[1].base_url,
                self.objects_api_group_used.objects_service.api_root,
            )
            self.assertEqual(call.args[2], ["nested", "bsn"])

        logs = TimelineLogProxy.objects.filter(object_id=submission_step.submission.id)
        self.assertEqual(
            logs.filter(extra_data__log_event="prefill_retrieve_success").count(), 0
        )
        self.assertEqual(
            logs.filter(extra_data__log_event="prefill_retrieve_failure").count(), 1
        )

    def test_verify_initial_data_ownership_missing_auth_attribute_path_causes_failing_prefill(
        self,
    ):
        del self.variable.prefill_options["auth_attribute_path"]
        self.variable.save()
        submission_step = SubmissionStepFactory.create(
            submission__form=self.form_step.form,
            form_step=self.form_step,
            submission__auth_info__value="999990676",
            submission__auth_info__attribute=AuthAttribute.bsn,
            submission__initial_data_reference=self.object_ref,
        )

        with patch(
            "openforms.prefill.contrib.objects_api.plugin.validate_object_ownership",
        ) as mock_validate_object_ownership:
            prefill_variables(submission=submission_step.submission)

            self.assertEqual(mock_validate_object_ownership.call_count, 0)

        logs = TimelineLogProxy.objects.filter(object_id=submission_step.submission.id)
        self.assertEqual(
            logs.filter(extra_data__log_event="prefill_retrieve_success").count(), 0
        )
        self.assertEqual(
            logs.filter(extra_data__log_event="prefill_retrieve_failure").count(), 1
        )
        self.assertEqual(
            logs.filter(
                extra_data__log_event="object_ownership_check_improperly_configured"
            ).count(),
            1,
        )

    def test_verify_initial_data_ownership_does_not_raise_errors_without_api_group(
        self,
    ):
        self.variable.prefill_options["objects_api_group"] = (
            ObjectsAPIGroupConfig.objects.last().pk + 1
        )
        self.variable.save()
        submission_step = SubmissionStepFactory.create(
            submission__form=self.form_step.form,
            form_step=self.form_step,
            submission__auth_info__value="999990676",
            submission__auth_info__attribute=AuthAttribute.bsn,
            submission__initial_data_reference=self.object_ref,
        )

        with patch(
            "openforms.prefill.contrib.objects_api.plugin.validate_object_ownership",
        ) as mock_validate_object_ownership:
            prefill_variables(submission=submission_step.submission)

            self.assertEqual(mock_validate_object_ownership.call_count, 0)

        logs = TimelineLogProxy.objects.filter(object_id=submission_step.submission.id)
        self.assertEqual(
            logs.filter(extra_data__log_event="prefill_retrieve_success").count(), 0
        )
        # Prefilling fails, because the API group does not exist
        self.assertEqual(
            logs.filter(extra_data__log_event="prefill_retrieve_failure").count(), 1
        )
