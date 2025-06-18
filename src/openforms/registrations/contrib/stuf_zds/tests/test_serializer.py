from django.test import SimpleTestCase

from ..options import ZaakOptionsSerializer


class StufZDSOptionsSerializerTest(SimpleTestCase):
    def test_valid_fields(self):
        options = ZaakOptionsSerializer(
            data={
                "zds_zaaktype_code": "123",
                "zds_documenttype_omschrijving_inzending": "aa",
            },
        )
        is_valid = options.is_valid()

        self.assertTrue(is_valid)

    def test_invalid_fields(self):
        options = ZaakOptionsSerializer(
            data={},
        )
        is_valid = options.is_valid()
        errors = options.errors

        self.assertFalse(is_valid)
        self.assertIn("zds_zaaktype_code", errors)
        self.assertIn("zds_documenttype_omschrijving_inzending", errors)

    def test_valid_variables_mapping(self):
        options = ZaakOptionsSerializer(
            data={
                "zds_zaaktype_code": "123",
                "zds_documenttype_omschrijving_inzending": "aa",
                "variables_mapping": [
                    {
                        "variable_key": "partners",
                        "registerAs": "zaakbetrokkene",
                    }
                ],
            },
        )
        is_valid = options.is_valid()

        self.assertTrue(is_valid)

    def test_invalid_variables_mapping(self):
        options = ZaakOptionsSerializer(
            data={
                "zds_zaaktype_code": "123",
                "zds_documenttype_omschrijving_inzending": "aa",
                "variables_mapping": [
                    {
                        "variable_key": "",
                        "registerAs": "",
                    }
                ],
            },
        )
        is_valid = options.is_valid()
        errors = options.errors

        self.assertFalse(is_valid)
        self.assertIn("variables_mapping", errors)
