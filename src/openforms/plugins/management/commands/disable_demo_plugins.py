from django.core.management import BaseCommand

from flags.models import FlagState

from openforms.config.models import GlobalConfiguration


class Command(BaseCommand):
    help = "Disable demo plugins"

    def handle(self, **options):
        config = GlobalConfiguration.get_solo()
        config.plugin_configuration = {}
        config.save()
        FlagState.objects.all().delete()
