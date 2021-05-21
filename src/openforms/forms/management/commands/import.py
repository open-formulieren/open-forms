import io
import json
import zipfile
from uuid import uuid4

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.translation import ugettext_lazy as _

from rest_framework.test import APIRequestFactory

from ...api import serializers as api_serializers
from ...models import Form, FormDefinition, FormStep

IMPORT_ORDER = {
    "formDefinitions": FormDefinition,
    "forms": Form,
    "formSteps": FormStep,
}


class Command(BaseCommand):
    help = "Import form from a ZIP-file."

    def add_arguments(self, parser):
        parser.add_argument(
            "--import-file",
            type=str,
            help=_("The name of the ZIP-file to import from"),
        )

    @transaction.atomic
    def handle(self, *args, **options):
        import_file = options["import_file"]

        uuid_mapping = {}

        factory = APIRequestFactory()
        request = factory.get("/")

        created_form = None
        with zipfile.ZipFile(import_file, "r") as zip_file:
            for resource, model in IMPORT_ORDER.items():
                if f"{resource}.json" in zip_file.namelist():
                    data = zip_file.read(f"{resource}.json").decode()

                    for old, new in uuid_mapping.items():
                        data = data.replace(old, new)

                    if resource == "formDefinitions":
                        serializer = api_serializers.FormDefinitionSerializer
                    if resource == "forms":
                        serializer = api_serializers.FormSerializer
                    if resource == "formSteps":
                        serializer = api_serializers.FormStepSerializer

                    for entry in json.loads(data):
                        if "uuid" in entry:
                            old_uuid = entry["uuid"]
                            entry["uuid"] = str(uuid4())
                            uuid_mapping[old_uuid] = entry["uuid"]

                        if resource == "forms":
                            entry["active"] = False

                        deserialized = serializer(
                            data=entry,
                            context={"request": request, "form": created_form},
                        )

                        if deserialized.is_valid():
                            deserialized.save()
                            if resource == "forms":
                                created_form = deserialized.instance
                        else:
                            raise CommandError(
                                f"Something went wrong while importing: {deserialized.errors}"
                            )
