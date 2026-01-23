from django.test import TestCase

from ..config import OIDCOptionsSerializer


class OIDCOptionsSerializerTest(TestCase):
    """
    Test validation of the Yivi options serializer.
    """

    def test_valid_empty_options(self):
        serializer = OIDCOptionsSerializer(data={})

        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data,
            {"visible": True},
        )

    def test_valid_filled_in_options(self):
        serializer = OIDCOptionsSerializer(
            data={"visible": False},
        )

        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data,
            {"visible": False},
        )
