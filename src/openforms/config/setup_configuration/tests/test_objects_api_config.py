from pathlib import Path

from django.test import TestCase

from django_setup_configuration.test_utils import load_step_config_from_source
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from openforms.contrib.objects_api.models import ObjectsAPIGroupConfig
from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory
from openforms.utils.tests.vcr import OFVCRMixin

from ..steps import ObjectsAPIConfigurationStep

TEST_FILES = (Path(__file__).parent / "files").resolve()
CONFIG_FILE_PATH = str(TEST_FILES / "setup_config_objects_api.yaml")
CONFIG_FILE_PATH_REQUIRED_FIELDS = str(
    TEST_FILES / "setup_config_objects_api_required_fields.yaml"
)
CONFIG_FILE_PATH_ALL_FIELDS = str(
    TEST_FILES / "setup_config_objects_api_all_fields.yaml"
)


def get_config_model(path):
    return load_step_config_from_source(ObjectsAPIConfigurationStep, path)


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
        step_config_model = get_config_model(CONFIG_FILE_PATH)
        step = ObjectsAPIConfigurationStep()

        step.execute(step_config_model)

        self.assertEqual(ObjectsAPIGroupConfig.objects.count(), 2)

        config1, config2 = ObjectsAPIGroupConfig.objects.all()

        self.assertEqual(config1.name, "Config 1")
        self.assertEqual(config1.identifier, "config-1")
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
        self.assertEqual(config2.identifier, "config-2")
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

    def test_execute_update_existing_config(self):
        ObjectsAPIGroupConfigFactory.create(name="old name", identifier="config-1")

        step_config_model = get_config_model(CONFIG_FILE_PATH)
        step = ObjectsAPIConfigurationStep()

        step.execute(step_config_model)

        self.assertEqual(ObjectsAPIGroupConfig.objects.count(), 2)

        config1, config2 = ObjectsAPIGroupConfig.objects.all()

        self.assertEqual(config1.name, "Config 1")
        self.assertEqual(config1.identifier, "config-1")
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
        self.assertEqual(config2.identifier, "config-2")
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

    def test_execute_with_required_fields(self):
        step_config_model = get_config_model(CONFIG_FILE_PATH_REQUIRED_FIELDS)
        step = ObjectsAPIConfigurationStep()

        step.execute(step_config_model)

        self.assertEqual(ObjectsAPIGroupConfig.objects.count(), 1)

        config = ObjectsAPIGroupConfig.objects.get()

        self.assertEqual(config.name, "Config 1")
        self.assertEqual(config.identifier, "config-1")
        self.assertEqual(config.objects_service, self.objects_service)
        self.assertEqual(config.objecttypes_service, self.objecttypes_service)

        self.assertEqual(config.drc_service, None)
        self.assertEqual(config.catalogi_service, None)
        self.assertEqual(config.catalogue_domain, "")
        self.assertEqual(config.catalogue_rsin, "")
        self.assertEqual(config.organisatie_rsin, "")
        self.assertEqual(config.iot_submission_report, "")
        self.assertEqual(config.iot_submission_csv, "")
        self.assertEqual(config.iot_attachment, "")

    def test_execute_with_all_fields(self):
        step_config_model = get_config_model(CONFIG_FILE_PATH_ALL_FIELDS)
        step = ObjectsAPIConfigurationStep()

        step.execute(step_config_model)

        self.assertEqual(ObjectsAPIGroupConfig.objects.count(), 1)

        config = ObjectsAPIGroupConfig.objects.get()

        self.assertEqual(config.name, "Config 1")
        self.assertEqual(config.identifier, "config-1")
        self.assertEqual(config.objects_service, self.objects_service)
        self.assertEqual(config.objecttypes_service, self.objecttypes_service)
        self.assertEqual(config.drc_service, self.drc_service)
        self.assertEqual(config.catalogi_service, self.catalogi_service)
        self.assertEqual(config.catalogue_domain, "TEST")
        self.assertEqual(config.catalogue_rsin, "000000000")
        self.assertEqual(config.organisatie_rsin, "000000000")
        self.assertEqual(config.iot_submission_report, "PDF Informatieobjecttype")
        self.assertEqual(config.iot_submission_csv, "CSV Informatieobjecttype")
        self.assertEqual(config.iot_attachment, "Attachment Informatieobjecttype")

    def test_execute_is_idempotent(self):
        step_config_model = get_config_model(CONFIG_FILE_PATH_ALL_FIELDS)
        step = ObjectsAPIConfigurationStep()

        def make_assertions():
            self.assertEqual(ObjectsAPIGroupConfig.objects.count(), 1)

            config = ObjectsAPIGroupConfig.objects.get()

            self.assertEqual(config.name, "Config 1")
            self.assertEqual(config.identifier, "config-1")
            self.assertEqual(config.objects_service, self.objects_service)
            self.assertEqual(config.objecttypes_service, self.objecttypes_service)
            self.assertEqual(config.drc_service, self.drc_service)
            self.assertEqual(config.catalogi_service, self.catalogi_service)
            self.assertEqual(config.catalogue_domain, "TEST")
            self.assertEqual(config.catalogue_rsin, "000000000")
            self.assertEqual(config.organisatie_rsin, "000000000")
            self.assertEqual(config.iot_submission_report, "PDF Informatieobjecttype")
            self.assertEqual(config.iot_submission_csv, "CSV Informatieobjecttype")
            self.assertEqual(config.iot_attachment, "Attachment Informatieobjecttype")

        step.execute(step_config_model)

        make_assertions()

        step.execute(step_config_model)

        make_assertions()
