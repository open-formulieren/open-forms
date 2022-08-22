from django.apps import AppConfig


class AuthStaticVariables(AppConfig):
    name = "openforms.authentication.static_variables"
    label = "authentication_static_variables"
    verbose_name = "Authentication static variables"

    def ready(self):
        from . import static_variables  # noqa
