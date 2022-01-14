import json
import os
import re

from django.conf import settings
from django.core.management import BaseCommand
from django.core.management.base import CommandError

TRANSLATION_REGEX_PATTERNS = {
    "labels": "label: '([^']+)'",
    "other": "\.t\('([^']+)'[\),]",
    "tooltips": "tooltip: '([^']+)'",
    "errors": "errorMessage\('([^']+)'[\),]",
}


def separator_label(label):
    return {
        f"---------- {label.upper()} ----------": f"---------- {label.upper()} ----------",
    }


class Command(BaseCommand):
    help = (
        "Best effort to extract messages from FormIO javascript source code. "
        "Existing translations (even unknown keys) will remain untouched."
    )

    def add_arguments(self, parser):
        super().add_arguments(parser)

        parser.add_argument(
            "--file",
            help="Point to a specific translation file to use as source and target.",
            default=os.path.join(settings.DJANGO_PROJECT_DIR, "js/lang/formio/nl.json"),
        )
        parser.add_argument(
            "--formio",
            action="append",
            help="Point to a specific folder where FormIO components are located.",
            default=[
                os.path.join(settings.DJANGO_PROJECT_DIR, "js/components"),
                os.path.join(settings.DJANGO_PROJECT_DIR, "static/bundles"),
            ],
        )
        parser.add_argument(
            "--dryrun",
            "--dry-run",
            action="store_true",
            help="Do not write translations back to file.",
        )
        parser.add_argument(
            "--no-empty-values",
            action="store_true",
            help="Set the untranslated text as translated text to prevent empty values (for new keys only).",
        )

    def _find_translations(self, filepath, no_empty_values):

        # Using `dict`` here to retain ordering.
        result = {}
        with open(filepath, "r") as f:
            data = f.read()
            data = data.replace("\\'", "OPENFORMS-ESCAPED-SINGLEQUOTE")
            for separator, pattern in TRANSLATION_REGEX_PATTERNS.items():
                matches = re.findall(pattern, data)
                matches = [
                    m.replace("OPENFORMS-ESCAPED-SINGLEQUOTE", "\\'") for m in matches
                ]
                if no_empty_values:
                    result.update(zip(matches, matches))
                else:
                    result.update(dict.fromkeys(matches, ""))
        return result

    def handle(self, **options):
        self.verbosity = options.get("verbosity")
        no_empty_values = options.get("no_empty_values")
        dryrun = options.get("dryrun")

        translations_filepath = options.get("file")

        if not os.path.exists(translations_filepath):
            raise CommandError(
                f"Translations file {translations_filepath} does not exist."
            )

        # Load existing translations.
        try:
            with open(translations_filepath, "r", encoding="utf-8") as f:
                existing_translations = json.load(f)
        except Exception as exc:
            self.stderr.write(f"Could not load translations: {exc}")
            return

        if self.verbosity > 0:
            self.stdout.write(f"Using translations file: {translations_filepath}")

        # Find new translations.
        formio_folders = options.get("formio")
        for formio_folder in formio_folders:
            if not os.path.exists(formio_folder):
                raise CommandError(f"FormIO folder {formio_folder} does not exist.")
            if self.verbosity > 0:
                self.stdout.write(f"Using FormIO folder: {formio_folder}")

        # This entry helps to identify newly found translations.
        found_translations = separator_label("new")

        for formio_folder in formio_folders:
            for root, subFolders, files in os.walk(formio_folder, topdown=True):
                for file in files:
                    if file.endswith(".js"):
                        filepath = os.path.join(root, file)
                        if self.verbosity > 1:
                            self.stdout.write(f"Scanning file: {filepath}")

                        result = self._find_translations(filepath, no_empty_values)
                        found_translations.update(result)

        # Report unknown
        diff = set(existing_translations).difference(set(found_translations))
        self.stdout.write(
            f"WARNING: Could not find matches for {len(diff)} existing translations."
        )
        if self.verbosity > 1:
            for item in diff:
                self.stdout.write(f"Not found: {item}")

        # Merge
        result = {}

        # Use order of existing translations.
        result.update(existing_translations)

        # Update with new and existing translations (new will go at the bottom)
        result.update(found_translations)

        # Overwrite the existing translation keys with their existing
        # translation values
        result.update(existing_translations)

        if not dryrun:
            with open(translations_filepath, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
        else:
            if self.verbosity > 1:
                self.stdout.write(json.dumps(result, indent=2))
