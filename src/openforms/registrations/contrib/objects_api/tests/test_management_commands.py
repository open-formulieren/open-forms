from pathlib import Path

from django.core.management import call_command
from django.test import TestCase

from openforms.forms.models import FormRegistrationBackend
from openforms.forms.tests.factories import FormRegistrationBackendFactory
from openforms.utils.tests.vcr import OFVCRMixin

from ..management.commands.migrate_objects_api_config import (
    InvalidBackend,
    SkipBackend,
    migrate_registration_backend,
)
from ..plugin import PLUGIN_IDENTIFIER
from .factories import ObjectsAPIGroupConfigFactory

FILES_DIR = Path(__file__).parent / "files"


class MigrateObjectsAPIV2ConfigTests(OFVCRMixin, TestCase):

    VCR_TEST_FILES = FILES_DIR

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        cls.objects_api_group = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True
        )

    def test_already_migrated(self):
        with self.assertRaises(SkipBackend):
            migrate_registration_backend(
                {
                    "objects_api_group": self.objects_api_group.pk,
                    "catalogus_domein": "TEST DOMEIN",
                    "catalogus_rsin": "000000000",
                }
            )

    def test_invalid_objects_api_group(self):
        with self.assertRaises(InvalidBackend):
            migrate_registration_backend(
                {
                    "objects_api_group": -1,
                }
            )

    def test_no_iot_fields(self):
        options = {
            "objects_api_group": self.objects_api_group.pk,
        }
        migrate_registration_backend(options)

        self.assertEqual(
            options,
            {
                "objects_api_group": self.objects_api_group.pk,
            },
        )

    def test_invalid_iot(self):
        options = {
            # This should be an URL:
            "objects_api_group": self.objects_api_group.pk,
            "informatieobjecttype_attachment": "--wrong--",
        }
        with self.assertRaises(InvalidBackend):
            migrate_registration_backend(options)

    def test_unknown_iot(self):
        options = {
            "objects_api_group": self.objects_api_group.pk,
            # 996946c4-92e8-4bf2-a18f-3ef41dbb423f does not exist on the Docker Compose instance:
            "informatieobjecttype_attachment": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/996946c4-92e8-4bf2-a18f-3ef41dbb423f",
        }
        with self.assertRaises(InvalidBackend):
            migrate_registration_backend(options)

    def test_iots_different_catalogs(self):
        options = {
            "objects_api_group": self.objects_api_group.pk,
            # Belongs to Catalogus PK 1:
            "informatieobjecttype_attachment": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/531f6c1a-97f7-478c-85f0-67d2f23661c7",
            # Belongs to Catalogus PK 2:
            "informatieobjecttype_submission_csv": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/d1cfb1d8-8593-4814-919d-72e38e80388f",
        }
        with self.assertRaises(InvalidBackend):
            migrate_registration_backend(options)

    def test_valid_config(self):
        backend: FormRegistrationBackend = FormRegistrationBackendFactory.create(
            backend=PLUGIN_IDENTIFIER,
            options={
                "objects_api_group": self.objects_api_group.pk,
                # Same catalog for all:
                "informatieobjecttype_attachment": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/531f6c1a-97f7-478c-85f0-67d2f23661c7",
                "informatieobjecttype_submission_csv": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/b2d83b94-9b9b-4e80-a82f-73ff993c62f3",
                "informatieobjecttype_submission_report": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/7a474713-0833-402a-8441-e467c08ac55b",
            },
        )

        call_command("migrate_objects_api_config")

        backend.refresh_from_db()

        self.assertEqual(
            backend.options,
            {
                "objects_api_group": self.objects_api_group.pk,
                "informatieobjecttype_attachment": "Attachment Informatieobjecttype",
                "informatieobjecttype_submission_csv": "CSV Informatieobjecttype",
                "informatieobjecttype_submission_report": "PDF Informatieobjecttype",
                "catalogus_domein": "TEST",
                "catalogus_rsin": "000000000",
            },
        )
