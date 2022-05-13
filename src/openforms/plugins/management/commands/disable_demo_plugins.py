from django.core.management import BaseCommand

from openforms.config.models import GlobalConfiguration


class Command(BaseCommand):
    help = "Disable demo plugins"

    def handle(self, **options):
        config = GlobalConfiguration.get_solo()
        config.enable_demo_plugins = False
        config.plugin_configuration = {}
        config.save()
