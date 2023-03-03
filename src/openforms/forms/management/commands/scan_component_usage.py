from django.core.management import BaseCommand

from ...models import FormDefinition


class Command(BaseCommand):
    help = "Check how often a certain component type is used"

    def add_arguments(self, parser):
        parser.add_argument(
            "component_type", help="Formio component.type string to scan for."
        )

    def handle(self, **options):
        component_type = options["component_type"]
        count = 0
        for fd in FormDefinition.objects.all().iterator():
            for component in fd.iter_components():
                if component["type"] == component_type:
                    count += 1

        self.stdout.write(f"Component type '{component_type}' is used {count} time(s).")
