from django.test import TestCase

from ..config import MicrosoftGraphOptionsSerializer


class MicrosoftGraphConfigTest(TestCase):
    def test_absolute_base_path_is_valid(self):
        serializer = MicrosoftGraphOptionsSerializer(data={"base_path": "/open-forms/"})

        self.assertTrue(serializer.is_valid())

    def test_relative_base_path_is_invalid(self):
        serializer = MicrosoftGraphOptionsSerializer(data={"base_path": "open-forms/"})

        self.assertFalse(serializer.is_valid())

    def test_absolute_additional_path_is_invalid(self):
        serializer = MicrosoftGraphOptionsSerializer(
            data={"additional_path": "/test/{year}/"}
        )

        self.assertFalse(serializer.is_valid())

    def test_relative_additional_path_is_valid(self):
        serializer = MicrosoftGraphOptionsSerializer(
            data={"additional_path": "test/{year}/"}
        )

        self.assertTrue(serializer.is_valid())
