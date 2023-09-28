from django.apps import AppConfig


class EmailsConfig(AppConfig):
    name = "openforms.emails"
    verbose_name = "Emails"

    def ready(self):
        # load the signal receivers
        from . import signals  # noqa
