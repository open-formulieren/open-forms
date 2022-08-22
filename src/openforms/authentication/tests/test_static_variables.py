from django.test import TestCase

from openforms.authentication.constants import AuthAttribute
from openforms.authentication.tests.factories import AuthInfoFactory
from openforms.forms.models import FormVariable


class TestStaticVariables(TestCase):
    def test_auth_static_data(self):
        auth_info = AuthInfoFactory.create(
            plugin="test-plugin",
            attribute=AuthAttribute.bsn,
            value="111222333",
            machtigen={AuthAttribute.bsn: "123456789"},
        )

        static_data = FormVariable.get_static_data(auth_info.submission)

        self.assertEqual(5, len(static_data))
        (
            form_auth_var,
            auth_identifier_var,
            auth_bsn_var,
            auth_kvk_var,
            auth_pseudo_var,
        ) = static_data
        self.assertEqual(
            {
                "plugin": "test-plugin",
                "attribute": AuthAttribute.bsn,
                "value": "111222333",
                "machtigen": {AuthAttribute.bsn: "123456789"},
            },
            auth_identifier_var.initial_value,
        )

        self.assertEqual(
            "auth_bsn",
            static_data[2].key,
        )
        self.assertEqual(
            "111222333",
            static_data[2].initial_value,
        )
        self.assertEqual(
            "auth_kvk",
            static_data[3].key,
        )
        self.assertEqual(
            "",
            static_data[3].initial_value,
        )
        self.assertEqual(
            "auth_pseudo",
            static_data[4].key,
        )
        self.assertEqual(
            "",
            static_data[4].initial_value,
        )

    def test_auth_static_data_no_submission(self):
        static_data = FormVariable.get_static_data()

        self.assertEqual(5, len(static_data))
        self.assertIsNone(static_data[1].initial_value)

        self.assertEqual(
            "auth_bsn",
            static_data[2].key,
        )
        self.assertEqual(
            "",
            static_data[2].initial_value,
        )
        self.assertEqual(
            "auth_kvk",
            static_data[3].key,
        )
        self.assertEqual(
            "",
            static_data[3].initial_value,
        )
        self.assertEqual(
            "auth_pseudo",
            static_data[4].key,
        )
        self.assertEqual(
            "",
            static_data[4].initial_value,
        )
