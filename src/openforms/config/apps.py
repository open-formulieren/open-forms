from io import StringIO

from django.apps import AppConfig
from django.core.management import call_command
from django.db.models.signals import post_migrate
from django.dispatch import receiver


class OpenFormsConfigConfig(AppConfig):
    name = "openforms.config"
    verbose_name = "Configuration"


@receiver(post_migrate, dispatch_uid="load_default_map_tile_layers")
def update_map_tile_layers(sender, **kwargs):
    call_command("loaddata", "default_map_tile_layers", verbosity=0, stdout=StringIO())
