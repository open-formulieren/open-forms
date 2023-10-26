from django.test import TestCase

from openforms.config.constants import CSPDirective
from openforms.config.models import CSPSetting

from ..constants import OgoneEndpoints
from .factories import OgoneMerchantFactory


class CSPUpdateTests(TestCase):
    def test_csp_is_saved_for_new_merchant_and_url_preset(self):
        self.assertTrue(CSPSetting.objects.none)

        merchant = OgoneMerchantFactory()

        csp = CSPSetting.objects.get()

        self.assertEqual(csp.content_object, merchant)
        self.assertEqual(csp.directive, CSPDirective.FORM_ACTION)
        self.assertEqual(csp.value, OgoneEndpoints.test)

    def test_csp_is_saved_for_new_merchant_and_custom_url(self):
        self.assertTrue(CSPSetting.objects.none)

        merchant = OgoneMerchantFactory(endpoint_custom="http://example.com")

        csp = CSPSetting.objects.get()

        self.assertEqual(csp.content_object, merchant)
        self.assertEqual(csp.directive, CSPDirective.FORM_ACTION)
        self.assertEqual(csp.value, "http://example.com")

    def test_csp_is_updated_for_existing_merchant_and_url_preset(self):
        self.assertTrue(CSPSetting.objects.none)

        # initial values
        merchant = OgoneMerchantFactory()

        csp = CSPSetting.objects.get()

        self.assertEqual(csp.content_object, merchant)
        self.assertEqual(csp.directive, CSPDirective.FORM_ACTION)
        self.assertEqual(csp.value, OgoneEndpoints.test)

        # updated values
        merchant.endpoint_preset = OgoneEndpoints.live
        merchant.save()

        # assert the original value has been deleted
        self.assertEqual(CSPSetting.objects.count(), 1)

        csp = CSPSetting.objects.get()

        self.assertEqual(csp.content_object, merchant)
        self.assertEqual(csp.directive, CSPDirective.FORM_ACTION)
        self.assertEqual(csp.value, OgoneEndpoints.live)

    def test_csp_is_updated_for_existing_merchant_and_custom_url(self):
        self.assertTrue(CSPSetting.objects.none)

        # initial values
        merchant = OgoneMerchantFactory(endpoint_custom="http://example.com")

        csp = CSPSetting.objects.get()

        self.assertEqual(csp.content_object, merchant)
        self.assertEqual(csp.directive, CSPDirective.FORM_ACTION)
        self.assertEqual(csp.value, "http://example.com")

        # updated values
        merchant.endpoint_preset = OgoneEndpoints.live
        merchant.save()

        # assert the original value has been deleted
        self.assertEqual(CSPSetting.objects.count(), 1)

        csp = CSPSetting.objects.get()

        self.assertEqual(csp.content_object, merchant)
        self.assertEqual(csp.directive, CSPDirective.FORM_ACTION)
        self.assertEqual(csp.value, "http://example.com")
