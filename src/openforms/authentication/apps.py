from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AuthenticationConfig(AppConfig):
    name = "openforms.authentication"
    label = "of_authentication"
    verbose_name = _("Authentication module")

    def ready(self):
        # ensure signal receivers are registered
        from . import signals  # noqa
