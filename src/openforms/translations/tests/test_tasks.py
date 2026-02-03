from datetime import UTC, datetime
from unittest.mock import patch

from django.core.files.base import ContentFile
from django.test import TestCase, override_settings

from freezegun import freeze_time

from ..constants import StatusChoices
from ..tasks import process_custom_translation_assets
from .factories import TranslationsMetaDataFactory


@override_settings(LANGUAGE_CODE="en")
class ProcessingCustomTranslationAssetTests(TestCase):
    @freeze_time("2026-01-27T18:00:00+01:00")
    def test_input_messages_file_successfully_processed(self):
        translations_metadata = TranslationsMetaDataFactory.create()

        process_custom_translation_assets(translations_metadata.pk)

        translations_metadata.refresh_from_db()

        self.assertIsNotNone(translations_metadata.compiled_asset)
        self.assertEqual(translations_metadata.processing_status, StatusChoices.done)
        self.assertEqual(translations_metadata.debug_output, "")
        self.assertEqual(
            translations_metadata.last_updated,
            datetime(2026, 1, 27, 17, 0, tzinfo=UTC),
        )
        self.assertEqual(translations_metadata.messages_count, 2)
        self.assertEqual(translations_metadata.app_release, "dev")

    @patch("openforms.translations.tasks.compile_messages_file")
    def test_input_messages_file_fails_compiling(self, m):
        m.return_value = False, "An error produced by formatjs"

        translations_metadata = TranslationsMetaDataFactory.create()

        process_custom_translation_assets(translations_metadata.pk)

        translations_metadata.refresh_from_db()

        self.assertRaises(ValueError, lambda: translations_metadata.compiled_asset.path)
        self.assertEqual(translations_metadata.processing_status, StatusChoices.failed)
        self.assertEqual(
            translations_metadata.debug_output, "An error produced by formatjs"
        )
        self.assertIsNone(translations_metadata.last_updated)
        self.assertIsNone(translations_metadata.messages_count)
        self.assertEqual(translations_metadata.app_release, "dev")

    def test_invalid_json_input_messages_file_fails(self):
        translations_metadata = TranslationsMetaDataFactory.create(
            messages_file=ContentFile(b"Invalid data", name="test_en.txt")
        )

        result = process_custom_translation_assets(translations_metadata.pk)

        self.assertIsNone(result)

        translations_metadata.refresh_from_db()

        self.assertRaises(ValueError, lambda: translations_metadata.compiled_asset.path)
        self.assertEqual(translations_metadata.processing_status, StatusChoices.failed)
        self.assertEqual(
            translations_metadata.debug_output,
            "JSON parsing failed (the file should be in a valid JSON format): Expecting value: line 1 column 1 (char 0)",
        )
        self.assertIsNone(translations_metadata.last_updated)
        self.assertIsNone(translations_metadata.messages_count)
        self.assertEqual(translations_metadata.app_release, "dev")
