from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings

from openforms.utils.tests.vcr import OFVCRMixin

from .factories import ZGWApiGroupConfigFactory


class ZGWApiGroupModelTests(TestCase):
    def test_model_validate(self):
        config = ZGWApiGroupConfigFactory.create(organisatie_rsin="619183020")
        config.full_clean()

    def test_model_invalid_rsin(self):
        config = ZGWApiGroupConfigFactory.create()
        config.organisatie_rsin = "063-08836"

        with self.assertRaises(ValidationError):
            config.full_clean()

    def test_model_string(self):
        api_group = ZGWApiGroupConfigFactory.create(name="ZGW API test")

        self.assertEqual(str(api_group), "ZGW API test")

    def test_can_save_without_catalogue_information(self):
        # checks that the check constraints are defined correctly
        instance = ZGWApiGroupConfigFactory.create(
            catalogue_domain="",
            catalogue_rsin="",
        )

        self.assertIsNotNone(instance.pk)

    def test_can_save_with_catalogue_information(self):
        # checks that the check constraints are defined correctly
        instance = ZGWApiGroupConfigFactory.create(
            catalogue_domain="Test",
            catalogue_rsin="123456782",
        )

        self.assertIsNotNone(instance.pk)

    def test_cannot_save_with_partial_information(self):
        # checks that the check constraints are defined correctly
        with self.assertRaises(IntegrityError), transaction.atomic():
            ZGWApiGroupConfigFactory.create(catalogue_domain="Test", catalogue_rsin="")

        with self.assertRaises(IntegrityError), transaction.atomic():
            ZGWApiGroupConfigFactory.create(
                catalogue_domain="", catalogue_rsin="123456782"
            )


@override_settings(LANGUAGE_CODE="en")
class ZGWAPIGroupValidationTests(OFVCRMixin, TestCase):
    def test_validate_no_catalogue_specified(self):
        config = ZGWApiGroupConfigFactory.create(catalogue_domain="", catalogue_rsin="")

        try:
            config.full_clean()
        except ValidationError as exc:
            raise self.failureException("Not specifying a catalogue is valid.") from exc

    def test_validate_catalogue_exists(self):
        # validates against the fixtures in docker/open-zaak
        config = ZGWApiGroupConfigFactory.create(
            for_test_docker_compose=True,
            catalogue_domain="NOPE",  # does not exist in fixtures
            catalogue_rsin="000000000",
        )

        with self.subTest("invalid catalogue"):
            with self.assertRaisesMessage(
                ValidationError,
                "The specified catalogue does not exist. Maybe you made a typo in the "
                "domain or RSIN?",
            ):
                config.full_clean()

        with self.subTest("valid catalogue"):
            config.catalogue_domain = "TEST"  # exists in the fixture
            try:
                config.full_clean()
            except ValidationError as exc:
                raise self.failureException(
                    "Catalogue exists and should validate"
                ) from exc
