import json

from django.core.files.base import ContentFile
from django.test import TestCase

from privates.test import temp_private_root

from ..subprocesses import compile_messages_file
from .factories import TranslationsMetaDataFactory


@temp_private_root()
class CompileCustomTranslationFileTests(TestCase):
    # Note that we can't really test for cleanup of temp files, because we don't know
    # the location of the tempdir that will be created by `compile_messages_file`

    def test_uploaded_messages_are_successfully_compiled(self):
        translation_metadata = TranslationsMetaDataFactory.create()

        result, compiled_json = compile_messages_file(
            translation_metadata.messages_file
        )

        assert compiled_json is not None

        self.assertTrue(result)
        self.assertEqual(
            json.loads(compiled_json),
            {
                "abc123": [
                    {
                        "offset": 0,
                        "options": {
                            "one": {"value": [{"type": 0, "value": "1 item"}]},
                            "other": {
                                "value": [
                                    {"type": 1, "value": "count"},
                                    {"type": 0, "value": " items"},
                                ]
                            },
                        },
                        "pluralType": "cardinal",
                        "type": 6,
                        "value": "count",
                    }
                ],
                "skjd8uh": [
                    {
                        "type": 0,
                        "value": "A modified translated text",
                    }
                ],
            },
        )

    def test_invalid_uploaded_messages_fail_and_return_errors(self):
        messages = {
            "skjd8uh": [{"type": 0, "value": "A modified translated text"}],
            "abc123": [
                {
                    "type": 6,
                    "options": {
                        "one": [{"type": 0, "value": "1 item"}],
                        "other": [{"type": 0, "value": "{count} items"}],
                    },
                }
            ],
        }
        json_bytes = json.dumps(messages, ensure_ascii=False).encode("utf-8")

        translation_metadata = TranslationsMetaDataFactory.create(
            messages_file=ContentFile(json_bytes, name="messages_test_en.json")
        )

        result, error_msg = compile_messages_file(translation_metadata.messages_file)

        self.assertFalse(result)
        self.assertIsInstance(error_msg, str)


class RealFileSystemStorageTranslationCompilationTests(TestCase):
    """
    Run tests that rely on the real filesystem storage being used.
    """

    def test_uploaded_messages_are_successfully_compiled(self):
        translation_metadata = TranslationsMetaDataFactory.create()

        def delete_files():
            translation_metadata.messages_file.delete(save=False)

        self.addCleanup(delete_files)

        result, compiled_json = compile_messages_file(
            translation_metadata.messages_file
        )

        assert compiled_json is not None

        self.assertTrue(result)
