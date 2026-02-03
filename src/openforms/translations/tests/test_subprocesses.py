import json
import tempfile
from pathlib import Path

from django.core.files.base import ContentFile
from django.test import TestCase, override_settings

from ..subprocesses import compile_messages_file
from .factories import TranslationsMetaDataFactory


class CompileCustomTranslationFileTests(TestCase):
    def test_uploaded_messages_are_successfully_compiled(self):
        tmpdir = tempfile.mkdtemp()
        with override_settings(PRIVATE_MEDIA_ROOT=tmpdir, SENDFILE_ROOT=tmpdir):
            translation_metadata = TranslationsMetaDataFactory.create()

            result, compiled_json = compile_messages_file(
                translation_metadata.messages_file.path
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
        tmpdir = tempfile.mkdtemp()
        with override_settings(PRIVATE_MEDIA_ROOT=tmpdir, SENDFILE_ROOT=tmpdir):
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

            result, error_msg = compile_messages_file(
                translation_metadata.messages_file.path
            )

            self.assertFalse(result)
            self.assertIsInstance(error_msg, str)

    def test_temp_output_file_is_removed_after_subprocess_finished(self):
        tmpdir = tempfile.mkdtemp()
        with override_settings(PRIVATE_MEDIA_ROOT=tmpdir, SENDFILE_ROOT=tmpdir):
            translation_metadata = TranslationsMetaDataFactory.create()
            tmp_path = Path(translation_metadata.messages_file.path)

            self.assertTrue(tmp_path.exists())

            result, compiled_json = compile_messages_file(
                translation_metadata.messages_file.path
            )
            remaining_files = list(Path(tmpdir).rglob("*"))
            remaining_files = [f for f in remaining_files if f.is_file()]

            self.assertTrue(result)
            # only the initial messages file should be present in the directory, the temp
            # output file (compiled asset) should have been removed by now
            self.assertEqual(remaining_files, [tmp_path])
