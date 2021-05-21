import io
import json
import zipfile
from uuid import uuid4

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.translation import ugettext_lazy as _

from rest_framework.exceptions import ValidationError
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

                        try:
                            deserialized.is_valid(raise_exception=True)
                            deserialized.save()
                            if resource == "forms":
                                created_form = deserialized.instance
                        except ValidationError as e:
                            if (
                                resource == "formDefinitions"
                                and "slug" in e.detail
                                and e.detail["slug"][0].code == "unique"
                            ):
                                existing_fd = FormDefinition.objects.get(
                                    slug=entry["slug"]
                                )
                                existing_fd_hash = existing_fd.get_hash()
                                imported_fd_hash = FormDefinition(
                                    configuration=entry["configuration"]
                                ).get_hash()

                                if existing_fd_hash == imported_fd_hash:
                                    # The form definition that is being imported
                                    # is identical to the existing form definition
                                    # with the same slug, use existing instead
                                    # of creating new definition
                                    uuid_mapping[old_uuid] = existing_fd.uuid
                                else:
                                    # The imported form definition configuration
                                    # is different, create a new form definition
                                    entry.pop("url")
                                    entry.pop("uuid")
                                    new_fd = FormDefinition(**entry)
                                    new_fd.save()
                                    uuid_mapping[old_uuid] = str(new_fd.uuid)
                            else:
                                raise CommandError(
                                    _(
                                        "Something went wrong while importing form: {}"
                                    ).format(e)
                                ) from e
