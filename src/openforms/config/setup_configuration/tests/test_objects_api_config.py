from pathlib import Path

from django.test import TestCase

from django_setup_configuration.exceptions import SelfTestFailed
from django_setup_configuration.test_utils import load_step_config_from_source
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from openforms.contrib.objects_api.models import ObjectsAPIGroupConfig
from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory
from openforms.utils.tests.vcr import OFVCRMixin

from ..steps import ObjectsAPIConfigurationStep

TEST_FILES = (Path(__file__).parent / "files").resolve()
CONFIG_FILE_PATH = str(TEST_FILES / "objects_api.yaml")
INVALID_CONFIG_FILE_PATH = str(TEST_FILES / "objects_api_invalid.yaml")

OTHER_CATALOGUS = "http://localhost:8003/catalogi/api/v1/catalogussen/630271f6-568a-485e-b1c4-4ed2d6ab3a58"


def get_config_model():
    return load_step_config_from_source(ObjectsAPIConfigurationStep, CONFIG_FILE_PATH)


class ObjectsAPIConfigurationStepTests(OFVCRMixin, TestCase):
    VCR_TEST_FILES = TEST_FILES
    maxDiff = None

    def setUp(self):
        super().setUp()

        self.objecttypes_service = ServiceFactory.create(
            slug="objecttypen-test",
            label="Objecttypen API test",
            api_root="http://localhost:8001/api/v2/",
            api_type=APITypes.orc,
            auth_type=AuthTypes.api_key,
            header_key="Authorization",
            header_value="Token foo",
        )
        self.objects_service = ServiceFactory.create(
            slug="objecten-test",
            label="Objecten API test",
            api_root="http://localhost:8002/api/v2/",
            api_type=APITypes.orc,
            auth_type=AuthTypes.api_key,
            header_key="Authorization",
            header_value="Token bar",
        )
        self.drc_service = ServiceFactory.create(
            slug="documenten-test",
            label="Documenten API test",
            api_root="http://localhost:8003/documenten/api/v1/",
            api_type=APITypes.drc,
            auth_type=AuthTypes.zgw,
            client_id="test_client_id",
            secret="test_secret_key",
        )
        self.catalogi_service = ServiceFactory.create(
            slug="catalogi-test",
            label="Catalogi API test",
            api_root="http://localhost:8003/catalogi/api/v1/",
            api_type=APITypes.ztc,
            auth_type=AuthTypes.zgw,
            client_id="test_client_id",
            secret="test_secret_key",
        )

    def test_execute_success(self):
        step_config_model = get_config_model()
        step = ObjectsAPIConfigurationStep()

        self.assertFalse(step.is_configured(step_config_model))

        step.execute(step_config_model)

        self.assertTrue(step.is_configured(step_config_model))
        self.assertEqual(ObjectsAPIGroupConfig.objects.count(), 2)

        config1, config2 = ObjectsAPIGroupConfig.objects.all()

        self.assertEqual(config1.name, "Config 1")
        self.assertEqual(config1.objects_service, self.objects_service)
        self.assertEqual(config1.objecttypes_service, self.objecttypes_service)
        self.assertEqual(config1.drc_service, self.drc_service)
        self.assertEqual(config1.catalogi_service, self.catalogi_service)
        self.assertEqual(config1.catalogue_domain, "TEST")
        self.assertEqual(config1.catalogue_rsin, "000000000")
        self.assertEqual(config1.organisatie_rsin, "000000000")
        self.assertEqual(config1.iot_submission_report, "PDF Informatieobjecttype")
        self.assertEqual(config1.iot_submission_csv, "CSV Informatieobjecttype")
        self.assertEqual(config1.iot_attachment, "Attachment Informatieobjecttype")

        self.assertEqual(config2.name, "Config 2")
        self.assertEqual(config2.objects_service, self.objects_service)
        self.assertEqual(config2.objecttypes_service, self.objecttypes_service)
        self.assertEqual(config2.drc_service, self.drc_service)
        self.assertEqual(config2.catalogi_service, self.catalogi_service)
        self.assertEqual(config2.catalogue_domain, "OTHER")
        self.assertEqual(config2.catalogue_rsin, "000000000")
        self.assertEqual(config2.organisatie_rsin, "000000000")
        self.assertEqual(config2.iot_submission_report, "")
        self.assertEqual(config2.iot_submission_csv, "")
        self.assertEqual(config2.iot_attachment, "")

    def test_already_configured(self):
        ObjectsAPIGroupConfigFactory.create(name="Config 1")
        ObjectsAPIGroupConfigFactory.create(name="Config 2")

        step_config_model = get_config_model()
        step = ObjectsAPIConfigurationStep()

        self.assertTrue(step.is_configured(step_config_model))

    def test_execute_update_existing_config(self):
        ObjectsAPIGroupConfigFactory.create(
            name="Config 1",
        )

        step_config_model = get_config_model()
        step = ObjectsAPIConfigurationStep()

        self.assertFalse(step.is_configured(step_config_model))

        step.execute(step_config_model)

        self.assertTrue(step.is_configured(step_config_model))
        self.assertEqual(ObjectsAPIGroupConfig.objects.count(), 2)

        config1, config2 = ObjectsAPIGroupConfig.objects.all()

        self.assertEqual(config1.name, "Config 1")
        self.assertEqual(config1.objects_service, self.objects_service)
        self.assertEqual(config1.objecttypes_service, self.objecttypes_service)
        self.assertEqual(config1.drc_service, self.drc_service)
        self.assertEqual(config1.catalogi_service, self.catalogi_service)
        self.assertEqual(config1.catalogue_domain, "TEST")
        self.assertEqual(config1.catalogue_rsin, "000000000")
        self.assertEqual(config1.organisatie_rsin, "000000000")
        self.assertEqual(config1.iot_submission_report, "PDF Informatieobjecttype")
        self.assertEqual(config1.iot_submission_csv, "CSV Informatieobjecttype")
        self.assertEqual(config1.iot_attachment, "Attachment Informatieobjecttype")

        self.assertEqual(config2.name, "Config 2")
        self.assertEqual(config2.objects_service, self.objects_service)
        self.assertEqual(config2.objecttypes_service, self.objecttypes_service)
        self.assertEqual(config2.drc_service, self.drc_service)
        self.assertEqual(config2.catalogi_service, self.catalogi_service)
        self.assertEqual(config2.catalogue_domain, "OTHER")
        self.assertEqual(config2.catalogue_rsin, "000000000")
        self.assertEqual(config2.organisatie_rsin, "000000000")
        self.assertEqual(config2.iot_submission_report, "")
        self.assertEqual(config2.iot_submission_csv, "")
        self.assertEqual(config2.iot_attachment, "")

    def test_validate_result_success(self):
        step_config_model = get_config_model()
        step = ObjectsAPIConfigurationStep()

        self.assertFalse(step.is_configured(step_config_model))

        step.execute(step_config_model)

        step.validate_result(step_config_model)

    def test_validate_result_failure(self):
        step_config_model = load_step_config_from_source(
            ObjectsAPIConfigurationStep, INVALID_CONFIG_FILE_PATH
        )
        step = ObjectsAPIConfigurationStep()

        self.assertFalse(step.is_configured(step_config_model))

        step.execute(step_config_model)

        expected_exc = (
            "The following issue(s) occurred while testing the configuration:\n"
            f"- No Informatieobjecttype found for catalogus {OTHER_CATALOGUS} and description PDF Informatieobjecttype\n"
            f"- No Informatieobjecttype found for catalogus {OTHER_CATALOGUS} and description CSV Informatieobjecttype\n"
            f"- No Informatieobjecttype found for catalogus {OTHER_CATALOGUS} and description Attachment Informatieobjecttype\n"
            "- No catalogus found for domain WRONG and RSIN 000000000\n"
        )

        with self.assertRaises(SelfTestFailed) as exc_info:
            step.validate_result(step_config_model)
        self.assertEqual(str(exc_info.exception), expected_exc)
