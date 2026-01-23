import json

from django.core.files.base import ContentFile

import factory

from ..models import TranslationsMetaData


class TranslationsMetaDataFactory(factory.django.DjangoModelFactory):
    language_code = "en"
    messages_file = factory.LazyAttribute(
        lambda _: ContentFile(
            json.dumps(
                {
                    "skjd8uh": [{"type": 0, "value": "A translated text"}],
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
            ).encode("utf-8"),
            name="test.json",
        )
    )

    class Meta:
        model = TranslationsMetaData
