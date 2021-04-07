import io
import json
import zipfile

from django.core.management.base import BaseCommand
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _

from rest_framework.test import APIRequestFactory

from ...api.serializers import (
    FormDefinitionSerializer,
    FormSerializer,
    FormStepSerializer,
)
from ...models import Form, FormDefinition, FormStep


class Command(BaseCommand):
    help = "Export the objects with the ids for the specified resource as json"

    def add_arguments(self, parser):
        parser.add_argument(
            "--archive_name", help=_("Name of the archive to write data to"), type=str
        )
        parser.add_argument(
            "--response",
            help=_("HttpResponse object to which the output data should be written"),
            type=HttpResponse,
        )
        parser.add_argument(
            "--form_id",
            help=_("ID of the Form to be exported"),
            type=int,
        )

    def handle(self, *args, **options):
        archive_name = options.pop("archive_name")
        response = options.pop("response")
        form_id = options.pop("form_id")

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

        forms = [FormSerializer(instance=form, context={"request": request}).data]
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

        if response:
            f = io.BytesIO()
            for name, data in resources.items():
                with zipfile.ZipFile(f, "a") as zip_file:
                    zip_file.writestr(f"{name}.json", data)
            response.content = f.getvalue()
        else:
            for name, data in resources.items():
                with zipfile.ZipFile(archive_name, "a") as zip_file:
                    zip_file.writestr(f"{name}.json", data)
