from io import StringIO

from django.core.files.base import ContentFile
from django.core.management import call_command
from django.test import TestCase, override_settings

from digid_eherkenning.models import DigidConfiguration, EherkenningConfiguration

from openforms.contrib.digid_eherkenning.tests.test_csp_update import (
    DIGID_METADATA_POST,
    EHERKENNING_METADATA_POST,
)
from openforms.payments.contrib.ogone.models import OgoneMerchant
from openforms.payments.contrib.ogone.tests.factories import OgoneMerchantFactory
from openforms.utils.tests.cache import clear_caches

from ..models import CSPSetting


def parse_csp_policy(header_value):
    # quick and dirty
    # "frame-ancestors 'self'; frame-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data: https://service.pdok.nl/ http://bazz.bar http://foo.bar; base-uri 'self'; default-src 'self'; report-uri /csp/report/"
    csp_values = dict()
    for line in header_value.split("; "):
        directive, v = line.split(" ", maxsplit=1)
        csp_values[directive] = v.split(" ")
    return csp_values


@override_settings(CSP_REPORT_ONLY=False)
class CSPUpdateTests(TestCase):
    def test_middleware_applies_cspsetting_models(self):
        CSPSetting.objects.create(directive="img-src", value="http://foo.bar")
        CSPSetting.objects.create(directive="img-src", value="http://bazz.bar")
        CSPSetting.objects.create(directive="default-src", value="http://buzz.bazz")

        response = self.client.get("/")
        self.assertIn("Content-Security-Policy", response.headers)
        csp_policy = parse_csp_policy(response.headers["Content-Security-Policy"])

        self.assertIn("http://foo.bar", csp_policy["img-src"])
        self.assertIn("http://bazz.bar", csp_policy["img-src"])
        self.assertIn("http://buzz.bazz", csp_policy["default-src"])


class CreateCSPFormActionFromConfigTests(TestCase):
    def setUp(self):
        super().setUp()

        self.addCleanup(clear_caches)

    def test_no_ogone_nor_digid_eherkenning_config(self):
        assert not OgoneMerchant.objects.exists()
        assert not DigidConfiguration.objects.exists()
        assert not EherkenningConfiguration.objects.exists()

        call_command(
            "create_csp_form_action_directives_from_config",
            stdout=StringIO(),
            stderr=StringIO(),
        )

        self.assertFalse(CSPSetting.objects.exists())

    def test_config_records_exists_but_are_incomplete(self):
        OgoneMerchant.objects.create(
            endpoint_preset="",  # not realistic, but the DB allows it
            endpoint_custom="",
        )
        digid_configuration = DigidConfiguration.objects.create()
        assert not digid_configuration.idp_metadata_file
        eherkenning_configuration = EherkenningConfiguration.objects.create()
        assert not eherkenning_configuration.idp_metadata_file
        CSPSetting.objects.all().delete()  # delete creates from test data setup

        call_command(
            "create_csp_form_action_directives_from_config",
            stdout=StringIO(),
            stderr=StringIO(),
        )

        self.assertFalse(CSPSetting.objects.exists())

    def test_config_created_when_ogone_merchants_with_url_exist(self):
        ogone_merchant = OgoneMerchantFactory.create()
        CSPSetting.objects.all().delete()  # delete creates from test data setup

        call_command(
            "create_csp_form_action_directives_from_config",
            stdout=StringIO(),
            stderr=StringIO(),
        )

        csp_setting = CSPSetting.objects.get()
        self.assertEqual(csp_setting.content_object, ogone_merchant)

    def test_digid_eherkenning_config_creates_cspsetting_records(self):
        digid_metadata = ContentFile(
            DIGID_METADATA_POST.read_bytes(), name="digid_metadata.xml"
        )
        digid_configuration = DigidConfiguration.objects.create(
            idp_metadata_file=digid_metadata
        )
        assert digid_configuration.idp_metadata_file
        eherkenning_metadata = ContentFile(
            EHERKENNING_METADATA_POST.read_bytes(), name="eh_metadata.xml"
        )
        eherkenning_configuration = EherkenningConfiguration.objects.create(
            idp_metadata_file=eherkenning_metadata
        )
        assert eherkenning_configuration.idp_metadata_file
        CSPSetting.objects.all().delete()  # delete creates from test data setup

        call_command(
            "create_csp_form_action_directives_from_config",
            stdout=StringIO(),
            stderr=StringIO(),
        )

        csp_settings = CSPSetting.objects.all()
        self.assertEqual(len(csp_settings), 2)

        by_content_object = {
            csp_setting.content_object: csp_setting for csp_setting in csp_settings
        }
        self.assertIn(digid_configuration, by_content_object)
        self.assertIn(eherkenning_configuration, by_content_object)
