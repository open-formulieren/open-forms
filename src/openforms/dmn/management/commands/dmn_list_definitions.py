import argparse

from django.core.management import BaseCommand

from tabulate import tabulate

from ...registry import register


class Command(BaseCommand):
    help = "List the available decision definitions for a given engine"

    def add_arguments(self, parser) -> None:
        engines = [plugin.identifier for plugin in register.iter_enabled_plugins()]
        parser.add_argument(
            "--engine",
            required=len(engines) != 1,
            choices=engines,
            default=engines[0] if len(engines) == 1 else argparse.SUPPRESS,
            help="The engine/plugin to query",
        )
        parser.add_argument(
            "--show-versions", action="store_true", help="Show available versions"
        )
        parser.add_argument(
            "--definition-id", help="Limit the versions to this definition ID"
        )

    def handle(self, **options):
        engine = options["engine"]
        definition_id = options["definition_id"]
        show_versions = options["show_versions"]

        plugin = register[engine]

        definitions = plugin.get_available_decision_definitions()
        if definition_id:
            definitions = [
                definition
                for definition in definitions
                if definition.identifier == definition_id
            ]
            if not definitions:
                self.stderr.write("No definition with this ID found!")
                return

        headers = ["ID", "Label"]
        if show_versions:
            headers += ["Version ID", "Version label"]

        data = []
        extra = ["", ""] if show_versions else []
        for definition in definitions:
            data.append([definition.identifier, definition.label, *extra])

            if show_versions:
                versions = plugin.get_decision_definition_versions(
                    definition.identifier
                )
                for version in versions:
                    data.append(["", "", version.id, version.label])

        self.stdout.write(f"Found {len(definitions)} definition(s).\n\n")

        table = tabulate(data, headers=headers)
        for line in table.splitlines():
            self.stdout.write(line)
