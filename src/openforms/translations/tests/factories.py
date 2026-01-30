import json

from django.core.files.base import ContentFile
from django.utils import timezone

import factory

from ..constants import StatusChoices
from ..models import TranslationsMetaData


def create_temp_messages_file() -> ContentFile:
    messages = {
        "skjd8uh": {
            "defaultMessage": "A modified translated text",
            "description": "A description",
            "originalDefault": "Completed",
        },
        "abc123": {
            "defaultMessage": "{count, plural, one {1 item} other {{count} items}}",
            "description": "Another description",
            "originalDefault": "{count, plural, one {1 item} other {{count} items}}",
        },
    }

    json_bytes = json.dumps(messages, ensure_ascii=False).encode("utf-8")
    return ContentFile(json_bytes, name="messages_test_en.json")


def create_temp_compiled_file() -> ContentFile:
    compiled_data = {
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

    json_bytes = json.dumps(compiled_data, ensure_ascii=False).encode("utf-8")
    return ContentFile(json_bytes, name="compiled_test_en.json")


class TranslationsMetaDataFactory(factory.django.DjangoModelFactory):
    language_code = "en"
    messages_file = factory.LazyFunction(create_temp_messages_file)
    app_release = "dev"

    class Meta:
        model = TranslationsMetaData

    class Params:
        with_compiled_asset = factory.Trait(
            compiled_asset=factory.LazyFunction(create_temp_compiled_file),
            processing_status=StatusChoices.done,
            last_updated=factory.LazyFunction(timezone.now),
            messages_count=2,
        )
