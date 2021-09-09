from django.test import TestCase

from openforms.payments.contrib.ogone.client import OgoneClient
from openforms.payments.contrib.ogone.plugin import RETURN_ACTION_PARAM
from openforms.payments.contrib.ogone.tests.factories import OgoneMerchantFactory


class OgoneClientTest(TestCase):
    maxDiff = None

    def test_get_payment_info(self):
        merchant = OgoneMerchantFactory()
        client = OgoneClient(merchant)

        return_url = "http://foo.bar/return?bazz=buzz"
        info = client.get_payment_info("123", 1000, return_url, RETURN_ACTION_PARAM)

        self.assertEqual(info.url, merchant.endpoint)
        self.assertEqual(info.type, "post")

        expected = {
            "PSPID": "merchant",
            "ORDERID": "123",
            "AMOUNT": "1000",
            "CURRENCY": "EUR",
            "LANGUAGE": "nl_NL",
            "PMLISTTYPE": "2",
            "ACCEPTURL": "http://foo.bar/return?bazz=buzz&action=accept",
            "DECLINEURL": "http://foo.bar/return?bazz=buzz&action=cancel",
            "EXCEPTIONURL": "http://foo.bar/return?bazz=buzz&action=exception",
            "CANCELURL": "http://foo.bar/return?bazz=buzz&action=cancel",
            "BACKURL": "http://foo.bar/return?bazz=buzz&action=cancel",
            "SHASIGN": "F2DE59B21C28C38F7E60C065FA915FE32E7C7A10BD6A2116F8C44CC9E58AB56F76018FA18FB90C1973E53BD6A14D868C89888F4A6EECBD0470CD204C34B68C5F",
        }
        self.assertEqual(expected, info.data)
