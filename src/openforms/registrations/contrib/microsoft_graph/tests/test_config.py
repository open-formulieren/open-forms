from django.test import TestCase, override_settings

from ..config import MicrosoftGraphOptionsSerializer


@override_settings(LANGUAGE_CODE="en")
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
        self.assertEqual(
            serializer.errors["folder_path"][0],
            "The path needs to be absolute - i.e. it needs to start with a /",
        )

    def test_folder_path_with_wrong_curly_braces_is_invalid(self):
        serializer = MicrosoftGraphOptionsSerializer(
            data={"folder_path": "/open-forms/{{% test %}}"}
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors["folder_path"][0],
            "Could not parse the remainder: '% test %' from '% test %'",
        )
