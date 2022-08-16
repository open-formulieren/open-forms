from django.apps import AppConfig


class StaticVariables(AppConfig):
    name = "openforms.variables.static_variables"
    verbose_name = "Static variables"

    def ready(self):
        from . import static_variables  # noqa
