from typing import List

from django.conf import settings


def get_language_codes() -> List[str]:
    return [language[0] for language in settings.LANGUAGES]
