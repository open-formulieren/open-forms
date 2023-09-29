from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class EmailsConfig(AppConfig):
    name = "openforms.emails"
    verbose_name = _("Emails")

    def ready(self):
        # load the signal receivers
        from . import signals  # noqa
