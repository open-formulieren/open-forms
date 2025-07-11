from django.test import SimpleTestCase

from ..models import OgoneMerchant


class OgoneMerchantTests(SimpleTestCase):
    def test_model_str_for_unsaved_instance(self):
        instance = OgoneMerchant()

        result = str(instance)

        self.assertIsInstance(result, str)
