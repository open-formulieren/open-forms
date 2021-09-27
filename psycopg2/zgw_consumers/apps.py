from django.apps import AppConfig


class ZgwConsumersConfig(AppConfig):
    name = "zgw_consumers"

    def ready(self):
        from .cache import install_schema_fetcher_cache

        install_schema_fetcher_cache()
