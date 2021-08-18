from django.apps import AppConfig

from openforms.setup import monkeypatch_cookie_consent


class UtilsConfig(AppConfig):
    name = "openforms.utils"

    def ready(self):
        from . import checks  # noqa

        # register custom converters
        from .api import drf_jsonschema  # noqa

        monkeypatch_cookie_consent()
