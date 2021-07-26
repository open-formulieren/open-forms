from dataclasses import asdict

from django.test import TestCase

from openforms.payments.contrib.ogone.client import OgoneClient
from openforms.payments.contrib.ogone.tests.factories import OgoneMerchantFactory


class OgoneClientTest(TestCase):
    maxDiff = None

    def test_get_payment_info(self):
        merchant = OgoneMerchantFactory()
        client = OgoneClient(merchant)

        return_url = "http://foo.bar/return?bazz=buzz"
        info = client.get_payment_info("123", 1000, return_url, "action")

        self.assertEqual(info.url, merchant.endpoint)
        self.assertEqual(info.type, "form")
        self.assertEqual(info.method, "post")

        expected = {
            "PSPID": "merchant",
            "ORDERID": "123",
            "AMOUNT": "1000",
            "CURRENCY": "EUR",
            "LANGUAGE": "nl_NL",
            "ACCEPTURL": "http://foo.bar/return?bazz=buzz&action=accept",
            "DECLINEURL": "http://foo.bar/return?bazz=buzz&action=cancel",
            "EXCEPTIONURL": "http://foo.bar/return?bazz=buzz&action=exception",
            "CANCELURL": "http://foo.bar/return?bazz=buzz&action=cancel",
            "BACKURL": "http://foo.bar/return?bazz=buzz&action=cancel",
            "SHASIGN": "DB8CCD089DE77C498BC3EAC263B00301D171F73F602D38556AC58EBBAE3AF9FF1FCCBF667393680D86F270F948000B0630A327EA840F4F522AA513EED57FA8C0",
        }
        self.assertEqual(expected, info.data)
