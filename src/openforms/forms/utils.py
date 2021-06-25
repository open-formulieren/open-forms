import json
import zipfile
from uuid import uuid4

from django.db import transaction

from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory

from .api import serializers as api_serializers
from .api.serializers import (
    FormDefinitionSerializer,
    FormExportSerializer,
    FormStepSerializer,
)
from .models import Form, FormDefinition, FormStep

IMPORT_ORDER = {
    "formDefinitions": FormDefinition,
    "forms": Form,
    "formSteps": FormStep,
}


def export_form(form_id, archive_name=None, response=None):
    form = Form.objects.get(pk=form_id)

    # Ignore products in the export
    form.product = None

    form_steps = FormStep.objects.filter(form__pk=form_id).select_related(
        "form_definition"
    )

    form_definitions = FormDefinition.objects.filter(
        pk__in=form_steps.values_list("form_definition", flat=True)
    )

    factory = APIRequestFactory()
    request = factory.get("/")

    forms = [FormExportSerializer(instance=form, context={"request": request}).data]
    form_definitions = FormDefinitionSerializer(
        instance=form_definitions,
        many=True,
        context={"request": request, "handle_custom_types": False},
    ).data
    form_steps = FormStepSerializer(
        instance=form_steps, many=True, context={"request": request}
    ).data

    resources = {
        "forms": json.dumps(forms),
        "formSteps": json.dumps(form_steps),
        "formDefinitions": json.dumps(form_definitions),
    }

    outfile = response or archive_name
    with zipfile.ZipFile(outfile, "w") as zip_file:
        for name, data in resources.items():
            zip_file.writestr(f"{name}.json", data)


@transaction.atomic
def import_form(import_file):
    uuid_mapping = {}

    factory = APIRequestFactory()
    request = factory.get("/")
    created_form_definitions = []

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
                            existing_fd = FormDefinition.objects.get(slug=entry["slug"])
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

                                created_form_definitions.append(new_fd.slug)
                        else:
                            raise e
    return created_form_definitions
