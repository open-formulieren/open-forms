from django.apps import AppConfig

from openforms.setup import monkeypatch_cookie_consent, mute_deprecation_warnings


class UtilsConfig(AppConfig):
    name = "openforms.utils"

    def ready(self):
        from . import checks  # noqa

        # register custom converters
        from .api import drf_jsonschema  # noqa

        mute_deprecation_warnings()
        monkeypatch_cookie_consent()

        from openforms.utils.admin import replace_cookie_log_admin  # noqa

        replace_cookie_log_admin()
