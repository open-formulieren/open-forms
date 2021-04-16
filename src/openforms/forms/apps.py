from django.apps import AppConfig

from openforms.forms.versioning import register_versioned_models


class CoreConfig(AppConfig):
    name = "openforms.forms"
    verbose_name = "OpenForms Form App"

    def ready(self):
        register_versioned_models()
