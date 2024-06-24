from pathlib import Path

from django.core.management import call_command
from django.test import TestCase

from openforms.forms.models import FormRegistrationBackend
from openforms.forms.tests.factories import FormRegistrationBackendFactory
from openforms.utils.tests.vcr import OFVCRMixin

from .test_objecttypes_client import get_test_config

FILES_DIR = Path(__file__).parent / "files"


class MigrateObjectsAPIObjecttypesURLSTest(OFVCRMixin, TestCase):

    VCR_TEST_FILES = FILES_DIR

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        cls.group = get_test_config()
        cls.group.objecttypes_service.save()
        cls.group.save()

    def test_existing_objecttype(self):
        FormRegistrationBackendFactory.create(
            backend="objects_api",
            options={
                "objects_api_group": self.group.pk,
                "objecttype_url": "http://localhost:8001/api/v2/objecttypes/8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
            },
        )

        call_command("migrate_objects_api_objecttype_urls")

        backend = FormRegistrationBackend.objects.get()

        self.assertNotIn("objecttype_url", backend.options)

        self.assertEqual(backend.options["objecttype_name"], "Person")

    def test_objecttype_does_not_exist(self):
        FormRegistrationBackendFactory.create(
            backend="objects_api",
            options={
                "objects_api_group": self.group.pk,
                "objecttype_url": "http://localhost:8001/api/v2/objecttypes/123",
            },
        )

        call_command("migrate_objects_api_objecttype_urls")

        backend = FormRegistrationBackend.objects.get()

        self.assertNotIn("objecttype_name", backend.options)

        self.assertEqual(
            backend.options["objecttype_url"],
            "http://localhost:8001/api/v2/objecttypes/123",
        )
