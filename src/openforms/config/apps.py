from io import StringIO

from django.apps import AppConfig
from django.core.management import call_command
from django.db.models.signals import post_migrate


class OpenFormsConfigConfig(AppConfig):
    name = "openforms.config"
    verbose_name = "Configuration"

    def ready(self):
        post_migrate.connect(update_map_tile_layers, sender=self)


def update_map_tile_layers(sender, **kwargs):
    call_command("loaddata", "default_map_tile_layers", verbosity=0, stdout=StringIO())
