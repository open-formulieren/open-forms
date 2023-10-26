from django.test import TestCase

from openforms.config.constants import CSPDirective
from openforms.config.models import CSPSetting
from openforms.payments.contrib.ogone.tests.factories import OgoneMerchantFactory


class CSPSettingManagerTests(TestCase):
    def test_csp_setting_is_set(self):
        merchant = OgoneMerchantFactory()

        CSPSetting.objects.set_for(
            merchant, [(CSPDirective.FORM_ACTION, "http://example.com")]
        )
        csp = CSPSetting.objects.get()

        self.assertEqual(csp.content_object, merchant)
        self.assertEqual(csp.directive, CSPDirective.FORM_ACTION)
        self.assertEqual(csp.value, "http://example.com")

    def test_csp_setting_is_not_set_with_wrong_directive(self):
        merchant = OgoneMerchantFactory()

        with self.assertLogs() as logs:
            CSPSetting.objects.set_for(
                merchant, [("wrong-directive", "http://example.com")]
            )
        message = logs.records[0].getMessage()

        self.assertEqual(
            message,
            f"Could not create csp setting for model '{merchant.__str__()}'. 'wrong-directive' is not a valid directive.",
        )
        self.assertTrue(CSPSetting.objects.none)
