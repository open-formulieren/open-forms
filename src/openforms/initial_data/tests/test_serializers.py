from hypothesis import given, strategies as st
from rest_framework.test import APISimpleTestCase

from ..api.serializers import RepresenteeSerializer
from ..constants import SupportedAuthAttributes


class RepresenteeSerializerTests(APISimpleTestCase):
    @given(
        invalid_bsn=st.one_of(
            st.text(min_size=0, max_size=8, alphabet="0123456789"),  # too short
            st.text(min_size=10, max_size=10, alphabet="0123456789"),  # too long
            st.just("123456789"),  # does not pass 11-test
        )
    )
    def test_validates_bsn_format(self, invalid_bsn: str):
        serializer = RepresenteeSerializer(
            data={
                "auth_attribute": SupportedAuthAttributes.bsn,
                "value": invalid_bsn,
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("value", serializer.errors)

    @given(
        invalid_kvk=st.one_of(
            st.text(min_size=0, max_size=7, alphabet="0123456789"),  # too short
            st.text(min_size=9, max_size=9, alphabet="0123456789"),  # too long
        )
    )
    def test_validates_kvk_format(self, invalid_kvk: str):
        serializer = RepresenteeSerializer(
            data={
                "auth_attribute": SupportedAuthAttributes.kvk,
                "value": invalid_kvk,
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("value", serializer.errors)

    @given(
        invalid_branch_number=st.one_of(
            st.text(min_size=1, max_size=11, alphabet="0123456789"),  # too short
            st.text(min_size=13, max_size=13, alphabet="0123456789"),  # too long
        )
    )
    def test_validates_branch_number_format(self, invalid_branch_number: str):
        serializer = RepresenteeSerializer(
            data={
                "auth_attribute": SupportedAuthAttributes.kvk,
                "value": "12345678",
                "branch_number": invalid_branch_number,
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("branch_number", serializer.errors)

    def test_non_kvk_does_not_allow_branch_number(self):
        serializer = RepresenteeSerializer(
            data={
                "auth_attribute": SupportedAuthAttributes.bsn,
                "value": "000000000",
                "branch_number": "123456123456",
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("branch_number", serializer.errors)
