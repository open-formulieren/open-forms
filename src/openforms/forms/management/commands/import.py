import io
import zipfile
from uuid import uuid4

from django.core import serializers
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.translation import ugettext_lazy as _

from ...models import Form, FormDefinition, FormStep

IMPORT_ORDER = {
    "formDefinitions": FormDefinition,
    "forms": Form,
    "formSteps": FormStep,
}


class Command(BaseCommand):
    help = "Import Catalogi data from a .zip file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--import_file",
            type=str,
            help=_("The name of the .zip file to import from"),
        )
        parser.add_argument(
            "--import_file_content",
            type=bytes,
            help=_("The .zip file content to import from"),
        )

    @transaction.atomic
    def handle(self, *args, **options):
        import_file = options.pop("import_file")
        import_file_content = options.pop("import_file_content")

        if import_file and import_file_content:
            raise CommandError(
                _(
                    "Please use either the --import_file or --import_file_content argument"
                )
            )

        if import_file_content:
            import_file = io.BytesIO(import_file_content)

        uuid_mapping = {}
        pk_mapping = {"forms": {}, "formDefinitions": {}}

        with zipfile.ZipFile(import_file, "r") as zip_file:
            for resource, model in IMPORT_ORDER.items():
                if f"{resource}.json" in zip_file.namelist():
                    data = zip_file.read(f"{resource}.json").decode()

                    for old, new in uuid_mapping.items():
                        data = data.replace(old, new)

                    try:
                        deserialized = serializers.deserialize("json", data)
                    except serializers.DeserializationError as e:
                        raise CommandError(
                            _(
                                "A validation error occurred while deserializing {}:\n{}"
                            ).format(resource, e)
                        )

                    for entry in deserialized:
                        if resource == "formSteps":
                            entry.object.form = pk_mapping["forms"][
                                entry.object.form_id
                            ]
                            entry.object.form_definition = pk_mapping[
                                "formDefinitions"
                            ][entry.object.form_definition_id]

                        old_pk = entry.object.pk
                        entry.object.pk = None

                        old_uuid = entry.object.uuid
                        entry.object.uuid = str(uuid4())
                        entry.save()

                        uuid_mapping[old_uuid] = entry.object.uuid

                        if resource != "formSteps":
                            pk_mapping[resource][old_pk] = entry.object
