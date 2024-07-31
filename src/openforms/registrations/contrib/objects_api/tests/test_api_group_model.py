from pathlib import Path

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from openforms.utils.tests.vcr import OFVCRMixin

from .factories import ObjectsAPIGroupConfigFactory

VCR_TEST_FILES = Path(__file__).parent / "files"


class ObjectsAPIGroupTests(TestCase):

    def test_can_save_without_catalogue_information(self):
        # checks that the check constraints are defined correctly
        instance = ObjectsAPIGroupConfigFactory.create(
            catalogue_domain="",
            catalogue_rsin="",
        )

        self.assertIsNotNone(instance.pk)

    def test_can_save_with_catalogue_information(self):
        # checks that the check constraints are defined correctly
        instance = ObjectsAPIGroupConfigFactory.create(
            catalogue_domain="Test",
            catalogue_rsin="123456782",
        )

        self.assertIsNotNone(instance.pk)

    def test_cannot_save_with_partial_information(self):
        # checks that the check constraints are defined correctly
        with self.assertRaises(IntegrityError), transaction.atomic():
            ObjectsAPIGroupConfigFactory.create(
                catalogue_domain="Test", catalogue_rsin=""
            )

        with self.assertRaises(IntegrityError), transaction.atomic():
            ObjectsAPIGroupConfigFactory.create(
                catalogue_domain="", catalogue_rsin="123456782"
            )


class ObjectsAPIGroupValidationTests(OFVCRMixin, TestCase):
    VCR_TEST_FILES = VCR_TEST_FILES

    def test_validate_catalogue_exists(self):
        # validates against the fixtures in docker/open-zaak
        config = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True,
            catalogue_domain="Nope",  # does not exist in fixtures
            catalogue_rsin="000000000",
        )

        with self.subTest("invalid catalogue"):
            with self.assertRaisesMessage(
                ValidationError,
                "The specified catalogue does not exist. Maybe you made a typo in the "
                "domain or RSIN?",
            ):
                config.clean()

        with self.subTest("valid catalogue"):
            config.catalogue_domain = "TEST"  # exists in the fixture
            try:
                config.clean()
            except ValidationError as exc:
                raise self.failureException(
                    "Catalogue exists and should vlaidate"
                ) from exc
