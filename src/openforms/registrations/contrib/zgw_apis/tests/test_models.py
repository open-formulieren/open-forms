from django.core.exceptions import ValidationError
from django.test import TestCase

from .factories import ZGWApiGroupConfigFactory


class ZGWApiGroupModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        config = ZGWApiGroupConfigFactory.create(
            zrc_service__api_root="https://zaken.nl/api/v1/",
            drc_service__api_root="https://documenten.nl/api/v1/",
            ztc_service__api_root="https://catalogus.nl/api/v1/",
        )
        config.full_clean()
        cls.config = config

    def test_model_validate(self):
        self.config.rsin = "619183020"
        self.config.full_clean()

    def test_model_invalid_rsin(self):
        with self.assertRaises(ValidationError):
            self.config.organisatie_rsin = "063-08836"
            self.config.full_clean()

    def test_model_string(self):
        api_group = ZGWApiGroupConfigFactory.create(name="ZGW API test")

        self.assertEqual(str(api_group), "ZGW API test")
