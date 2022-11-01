from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class TranslationsConfig(AppConfig):
    name = "openforms.translations"
    label = "of_translations"
    verbose_name = _("Translation module")

    def ready(self):
        # ensure signal receivers are registered
        from . import signals  # noqa
