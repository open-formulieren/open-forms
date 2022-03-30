from django.apps import AppConfig


class CustomFieldTypesConfig(AppConfig):
    name = "openforms.custom_field_types"

    def ready(self):
        from . import family_members  # noqa
