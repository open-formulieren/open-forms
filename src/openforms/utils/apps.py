from django.apps import AppConfig

from openforms.setup import monkeypatch_cookie_consent


class UtilsConfig(AppConfig):
    name = "openforms.utils"

    def ready(self):
        from . import checks  # noqa

        monkeypatch_cookie_consent()
