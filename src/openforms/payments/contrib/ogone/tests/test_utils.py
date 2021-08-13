from django.test import TestCase

from openforms.payments.contrib.ogone.data import OgoneRequestParams
from openforms.payments.contrib.ogone.signing import calculate_shasign


class OgoneUtilsTest(TestCase):
    def test_calculate_shasign_example(self):
        # example from the documentation
        params = OgoneRequestParams(
            AMOUNT=1500,
            CURRENCY="EUR",
            LANGUAGE="en_US",
            ORDERID=1234,
            PSPID="MyPSPID",
        )
        passphrase = "Mysecretsig1875!?"
        data = params.get_dict()

        actual = calculate_shasign(data, passphrase, "sha1")
        expected = "F4CC376CD7A834D997B91598FA747825A238BE0A"
        self.assertEqual(expected, actual)

        # check if hashing skips unhashed/unknown params
        data["FOO_XYZ_"] = 123

        actual = calculate_shasign(data, passphrase, "sha1")
        self.assertEqual(expected, actual)
