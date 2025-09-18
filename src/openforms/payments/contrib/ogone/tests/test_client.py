import os
from pathlib import Path

from django.test import TestCase

import requests

from openforms.utils.tests.vcr import OFVCRMixin

from ..client import OgoneClient
from ..plugin import RETURN_ACTION_PARAM
from .factories import OgoneMerchantFactory


class OgoneClientTest(OFVCRMixin, TestCase):
    VCR_TEST_FILES = Path(__file__).parent / "files"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.merchant = OgoneMerchantFactory.build(
            pspid=os.getenv("OGONE_PSPID", "maykinmedia"),
            sha_in_passphrase=os.getenv("OGONE_SHA_IN", "placeholder_sha_in"),
            sha_out_passphrase=os.getenv("OGONE_SHA_OUT", "placeholder_sha_out"),
        )

    def test_payment_request_valid_order_id(self):
        client = OgoneClient(self.merchant)

        info = client.get_payment_info(
            "2024/OF-5HEBWV/84",
            5000,
            "http://foo.bar/return?bazz=buzz",
            RETURN_ACTION_PARAM,
        )

        payment_request = requests.post(info.url, data=info.data)

        # Response is always a 200, so we assert on the content instead
        self.assertNotIn("Er is een fout opgetreden", payment_request.text)

    def test_payment_request_invalid_order_id(self):
        client = OgoneClient(self.merchant)

        info = client.get_payment_info(
            "xyz2024/OF-123456/987654321THISISPROBABLYTOOLONG",
            1000,
            "http://foo.bar/return?bazz=buzz",
            RETURN_ACTION_PARAM,
        )

        payment_request = requests.post(info.url, data=info.data)

        self.assertIn("Er is een fout opgetreden", payment_request.text)

    def test_com_title_unicode_chars(self):
        client = OgoneClient(self.merchant)

        info = client.get_payment_info(
            "2024/OF-5HEBWV/84",
            5000,
            "http://foo.bar/return?bazz=buzz",
            RETURN_ACTION_PARAM,
            title="läääääääääääääämp! " * 10,  # 190 chars
            com="brøther i desire lööps",
        )

        payment_request = requests.post(info.url, data=info.data)

        # Response is always a 200, so we assert on the content instead
        self.assertNotIn("Er is een fout opgetreden", payment_request.text)


class OgoneGetPaymentInfoTest(TestCase):
    maxDiff = None

    def test_get_payment_info(self):
        """This test does not make any request and is here to test the ``get_payment_info`` method."""
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
