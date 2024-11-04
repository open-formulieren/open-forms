from pathlib import Path
from unittest.mock import patch

from django.core.exceptions import PermissionDenied
from django.test import TestCase, tag

from vcr.config import VCR

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
from openforms.utils.tests.vcr import OFVCRMixin

TEST_FILES = (Path(__file__).parent / "files").resolve()


class ObjectsAPIPrefillDataOwnershipCheckTests(OFVCRMixin, TestCase):
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
                        data={"bsn": "111222333", "some": {"path": "foo"}},
                        objecttype_version=1,
                    ),
                    objecttype_url="http://objecttypes-web:8000/api/v2/objecttypes/8faed0fa-7864-4409-aa6d-533a37616a9e",
                )
            cls.object_ref = object["uuid"]

    @tag("gh-4398")
    def test_verify_initial_data_ownership(self):
        objects_api_group_used = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True
        )
        objects_api_group_unused = ObjectsAPIGroupConfigFactory.create()

        form = FormFactory.create()
        # An objects API backend with a different API group
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
            },
        )

        form_step = FormStepFactory.create(
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
        variable = FormVariableFactory.create(
            key="voornamen",
            form=form_step.form,
            prefill_plugin="objects_api",
            prefill_attribute="",
            prefill_options={
                "version": 2,
                "objecttype": "3edfdaf7-f469-470b-a391-bb7ea015bd6f",
                "objects_api_group": objects_api_group_used.pk,
                "objecttype_version": 1,
                "variables_mapping": [
                    {"variable_key": "voornamen", "target_path": ["some", "path"]},
                ],
            },
        )

        with self.subTest(
            "verify_initial_data_ownership is called if initial_data_reference is specified"
        ):
            submission_step = SubmissionStepFactory.create(
                submission__form=form_step.form,
                form_step=form_step,
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
                    objects_api_group_used.objects_service.api_root,
                )
                self.assertEqual(call.args[2], ["bsn"])

            logs = TimelineLogProxy.objects.filter(
                object_id=submission_step.submission.id
            )

            self.assertEqual(
                logs.filter(extra_data__log_event="prefill_retrieve_success").count(), 1
            )

        with self.subTest(
            "verify_initial_data_ownership raising error causes prefill to fail"
        ):
            submission_step = SubmissionStepFactory.create(
                submission__form=form_step.form,
                form_step=form_step,
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
                    objects_api_group_used.objects_service.api_root,
                )
                self.assertEqual(call.args[2], ["bsn"])

            logs = TimelineLogProxy.objects.filter(
                object_id=submission_step.submission.id
            )
            self.assertEqual(
                logs.filter(extra_data__log_event="prefill_retrieve_success").count(), 0
            )
            self.assertEqual(
                logs.filter(extra_data__log_event="prefill_retrieve_failure").count(), 1
            )

        with self.subTest(
            "verify_initial_data_ownership does not raise errors if no API group is found"
        ):
            variable.prefill_options["objects_api_group"] = (
                ObjectsAPIGroupConfig.objects.last().pk + 1
            )
            variable.save()
            submission_step = SubmissionStepFactory.create(
                submission__form=form_step.form,
                form_step=form_step,
                submission__auth_info__value="999990676",
                submission__auth_info__attribute=AuthAttribute.bsn,
                submission__initial_data_reference=self.object_ref,
            )

            with patch(
                "openforms.prefill.contrib.objects_api.plugin.validate_object_ownership",
            ) as mock_validate_object_ownership:
                prefill_variables(submission=submission_step.submission)

                self.assertEqual(mock_validate_object_ownership.call_count, 0)

            logs = TimelineLogProxy.objects.filter(
                object_id=submission_step.submission.id
            )
            self.assertEqual(
                logs.filter(extra_data__log_event="prefill_retrieve_success").count(), 0
            )
            # Prefilling fails, because the API group does not exist
            self.assertEqual(
                logs.filter(extra_data__log_event="prefill_retrieve_failure").count(), 1
            )
