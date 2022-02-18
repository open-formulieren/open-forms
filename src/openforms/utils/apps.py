from django.apps import AppConfig
from django.core.signals import setting_changed

from django_sendfile.utils import _get_sendfile

from openforms.setup import mute_deprecation_warnings


class UtilsConfig(AppConfig):
    name = "openforms.utils"

    def ready(self):
        from . import checks  # noqa

        # register custom converters
        from .api import drf_jsonschema  # noqa

        setting_changed.connect(clear_lru_cache_on_settings_changed)

        mute_deprecation_warnings()

        from openforms.utils.admin import replace_cookie_log_admin  # noqa

        replace_cookie_log_admin()


def clear_lru_cache_on_settings_changed(setting, **kwargs):
    if setting != "SENDFILE_BACKEND":
        return
    _get_sendfile.cache_clear()
