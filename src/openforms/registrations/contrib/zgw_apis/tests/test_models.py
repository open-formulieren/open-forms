from django.core.exceptions import ValidationError
from django.test import TestCase

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
