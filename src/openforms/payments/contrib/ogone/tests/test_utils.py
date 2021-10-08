from django.test import TestCase

from ..data import OgoneRequestParams
from ..plugin import case_insensitive_get
from ..signing import calculate_sha_in, calculate_sha_out


class OgoneUtilsTest(TestCase):
    def test_calculate_sha_in_sign_example(self):
        # example from the documentation
        params = OgoneRequestParams(
            AMOUNT=1500,
            CURRENCY="EUR",
            LANGUAGE="en_US",
            ORDERID=1234,
            PSPID="MyPSPID",
            PMLISTTYPE=None,  # not used in the online example
        )
        passphrase = "Mysecretsig1875!?"
        data = params.get_dict()

        actual = calculate_sha_in(data, passphrase, "sha1")
        expected = "F4CC376CD7A834D997B91598FA747825A238BE0A"
        self.assertEqual(expected, actual)

        # check if hashing skips unhashed/unknown params
        data["FOO_XYZ_"] = 123

        actual = calculate_sha_in(data, passphrase, "sha1")
        self.assertEqual(expected, actual)

        # check if hashing fails bad params
        data["ORDERID"] = 9999

        actual = calculate_sha_in(data, passphrase, "sha1")
        self.assertNotEqual(expected, actual)

    def test_return_url_sha_out_sign(self):
        data = dict(
            orderID=202100031,
            STATUS=9,
            PAYID=3138700369,
            NCERROR=0,
            SHASIGN="F21EC101D04FD8F43662F4C5BE87F5E3E1B08293B15D61DC9E779392F4D411B40471311BAF53B8C656E1FD4C770999C40B512D35CBDA46BE30C0B91BFB9F272B",
        )
        passphrase = "q8B4Pms_MJEUlRo_Icu&"
        actual = calculate_sha_out(data, passphrase, "sha512")
        expected = data["SHASIGN"]
        self.assertEqual(expected, actual)

    def test_webhook_sha_out_sign(self):
        data = dict(
            orderID=202100040,
            STATUS=9,
            PAYID=3138705649,
            NCERROR=0,
            SHASIGN="56448FC7468D8B4220B2404BFDE4E63E6F0592142457585358CD0815E258550FF0EC0A93C6B5F87BC528C98B0B87557C13DE4A2C15B8FCB5868CA1D820B77CDB",
        )
        passphrase = "308dd075-813c-40fc-ad97-b2a45ecbd5ae"
        actual = calculate_sha_out(data, passphrase, "sha512")
        expected = data["SHASIGN"]
        self.assertEqual(expected, actual)

    def test_case_insensitive_get(self):
        self.assertEqual(123, case_insensitive_get({"foo": 123}, "foo"))
        self.assertEqual(123, case_insensitive_get({"foo": 123}, "FOO"))
        self.assertEqual(123, case_insensitive_get({"FOO": 123}, "foo"))
        self.assertEqual(123, case_insensitive_get({"fOO": 123}, "Foo"))

        # defined first
        self.assertEqual(123, case_insensitive_get({"foo": 123, "FOO": 321}, "foo"))

        # default
        self.assertEqual(None, case_insensitive_get({"foo": 123}, "bar"))
        self.assertEqual(321, case_insensitive_get({"foo": 123}, "bar", default=321))
