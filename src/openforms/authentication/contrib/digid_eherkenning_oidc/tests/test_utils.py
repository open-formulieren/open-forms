from django.test import TestCase

from ..utils import obfuscate_claim


class ObfuscateClaimsTestCase(TestCase):
    def test_obfuscate_bsn_claim(self):
        bsn = "123456782"
        result = obfuscate_claim(bsn)

        self.assertEqual(result, "*******82")

    def test_obfuscate_non_string(self):
        value = 12345
        result = obfuscate_claim(value)

        self.assertEqual(result, "****5")
