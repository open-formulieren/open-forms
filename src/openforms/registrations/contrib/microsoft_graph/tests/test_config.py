from django.test import TestCase

from ..config import MicrosoftGraphOptionsSerializer


class MicrosoftGraphConfigTest(TestCase):
    def test_absolute_folder_path_is_valid(self):
        serializer = MicrosoftGraphOptionsSerializer(
            data={"folder_path": "/open-forms/"}
        )

        self.assertTrue(serializer.is_valid())

    def test_relative_folder_path_is_invalid(self):
        serializer = MicrosoftGraphOptionsSerializer(
            data={"folder_path": "open-forms/"}
        )

        self.assertFalse(serializer.is_valid())
