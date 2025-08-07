from pathlib import Path

from django.core.exceptions import PermissionDenied
from django.test import TestCase, tag

from openforms.authentication.service import AuthAttribute
from openforms.contrib.objects_api.clients import get_objects_client
from openforms.contrib.objects_api.helpers import prepare_data_for_registration
from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory
from openforms.forms.tests.factories import FormFactory, FormVariableFactory
from openforms.logging.models import TimelineLogProxy
from openforms.prefill.service import prefill_variables
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.utils.tests.vcr import OFVCRMixin, with_setup_test_data_vcr

TEST_FILES = (Path(__file__).parent / "files").resolve()


@tag("gh-4398")
class ObjectsAPIPrefillDataOwnershipCheckTests(OFVCRMixin, TestCase):
    VCR_TEST_FILES = TEST_FILES

    @classmethod
    def setUpTestData(cls):
        """
        Set up a form with basic configuration:

        * 1 formstep, with a component 'postcode'
        * 3 registration backends (email: irrelevant, objects API: different group,
          objects API: relevant)
        * 2 user defined form variables:

            * one to to the objects API prefill
            * one to get the mapped variable assigned to
        """
        super().setUpTestData()

        cls.objects_api_group_used = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True
        )
        cls.objects_api_group_unused = ObjectsAPIGroupConfigFactory.create()

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

        cls.form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "postcode",
                        "key": "postcode",
                        "inputMask": "9999 AA",
                    }
                ],
            },
        )
        FormVariableFactory.create(form=cls.form, key="voornamen", user_defined=True)
        cls.variable = FormVariableFactory.create(
            form=cls.form,
            key="prefillData",
            user_defined=True,
            prefill_plugin="objects_api",
            prefill_attribute="",
            prefill_options={
                "version": 2,
                "objects_api_group": cls.objects_api_group_used.identifier,
                "objecttype_uuid": "3edfdaf7-f469-470b-a391-bb7ea015bd6f",
                "objecttype_version": 1,
                "auth_attribute_path": ["bsn"],
                "variables_mapping": [
                    {"variable_key": "voornamen", "target_path": ["some", "path"]},
                ],
            },
        )

    def test_verify_initial_data_ownership_called_if_initial_data_reference_specified(
        self,
    ):
        submission = SubmissionFactory.create(
            form=self.form,
            auth_info__value="111222333",
            auth_info__attribute=AuthAttribute.bsn,
            initial_data_reference=self.object_ref,
        )

        prefill_variables(submission=submission)

        logs = TimelineLogProxy.objects.for_object(submission)
        self.assertEqual(logs.filter_event("object_ownership_check_success").count(), 1)
        self.assertEqual(logs.filter_event("prefill_retrieve_success").count(), 1)

    def test_verify_initial_data_ownership_raising_errors_causes_prefill_to_fail(self):
        # configure an invalid path, which causes errors during validation
        self.variable.prefill_options["auth_attribute_path"] = ["nested", "bsn"]
        self.variable.save()
        submission = SubmissionFactory.create(
            form=self.form,
            # valid BSN, invalid config
            auth_info__value="111222333",
            auth_info__attribute=AuthAttribute.bsn,
            initial_data_reference=self.object_ref,
        )

        with self.assertRaises(PermissionDenied):
            prefill_variables(submission=submission)

        logs = TimelineLogProxy.objects.for_object(submission)
        self.assertEqual(logs.filter_event("prefill_retrieve_failure").count(), 1)
        self.assertFalse(logs.filter_event("object_ownership_check_success").exists())
        self.assertFalse(logs.filter_event("prefill_retrieve_success").exists())

    def test_verify_initial_data_ownership_missing_auth_attribute_path_causes_failing_prefill(
        self,
    ):
        with self.subTest("missing auth_attribute_path config option"):
            # doesn't pass serializer validation, so prefill fails
            del self.variable.prefill_options["auth_attribute_path"]
            self.variable.save()
            submission = SubmissionFactory.create(
                form=self.form,
                auth_info__value="111222333",
                auth_info__attribute=AuthAttribute.bsn,
                initial_data_reference=self.object_ref,
            )

            prefill_variables(submission=submission)

            logs = TimelineLogProxy.objects.for_object(submission)
            self.assertEqual(logs.filter_event("prefill_retrieve_failure").count(), 1)
            self.assertFalse(
                logs.filter_event("object_ownership_check_success").exists()
            )
            self.assertFalse(logs.filter_event("prefill_retrieve_success").exists())

        with self.subTest("empty auth_attribute_path config option value"):
            self.variable.prefill_options["auth_attribute_path"] = []
            self.variable.save()
            submission = SubmissionFactory.create(
                form=self.form,
                auth_info__value="111222333",
                auth_info__attribute=AuthAttribute.bsn,
                initial_data_reference=self.object_ref,
            )

            prefill_variables(submission=submission)

            logs = TimelineLogProxy.objects.for_object(submission)
            self.assertEqual(logs.filter_event("prefill_retrieve_failure").count(), 1)
            self.assertFalse(
                logs.filter_event("object_ownership_check_success").exists()
            )
            self.assertFalse(logs.filter_event("prefill_retrieve_success").exists())

    def test_allow_prefill_when_ownership_check_is_skipped(self):
        self.variable.prefill_options["skip_ownership_check"] = True
        self.variable.save()
        submission = SubmissionFactory.create(
            form=self.form,
            # invalid BSN
            auth_info__value="000XXX000",
            auth_info__attribute=AuthAttribute.bsn,
            initial_data_reference=self.object_ref,
        )

        try:
            prefill_variables(submission=submission)
        except PermissionDenied as exc:
            raise self.failureException("Ownership check should be skipped") from exc
