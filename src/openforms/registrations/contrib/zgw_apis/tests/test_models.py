from django.core.exceptions import ValidationError
from django.test import TestCase

from zgw_consumers.constants import APITypes

from .factories import ServiceFactory, ZgwConfigFactory


class ZGWBackendTests(TestCase):
    def setUp(self):
        self.config = ZgwConfigFactory.create(
            zrc_service__api_root="https://zaken.nl/api/v1/",
            drc_service__api_root="https://documenten.nl/api/v1/",
            ztc_service__api_root="https://catalogus.nl/api/v1/",
        )
        self.config.full_clean()

    def test_model_validate(self):
        self.config.zaaktype = "https://zaken.nl/api/v1/zaak/1"
        self.config.informatieobjecttype = "https://catalogus.nl/api/v1/info/1"
        self.config.rsin = "619183020"
        self.config.full_clean()

    def test_model_invalid_zaaktype(self):
        with self.assertRaises(ValidationError):
            self.config.zaaktype = "https://BAD_DOMAIN.nl/api/v1/zaak/1"
            self.config.full_clean()

    def test_model_invalid_informatieobjecttype(self):
        with self.assertRaises(ValidationError):
            self.config.informatieobjecttype = "https://BAD_DOMAIN.nl/api/v1/info/1"
            self.config.full_clean()

    def test_model_invalid_rsin(self):
        with self.assertRaises(ValidationError):
            self.config.organisatie_rsin = "063-08836"
            self.config.full_clean()
