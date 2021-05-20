import io
import json
import zipfile

from django.core.management.base import BaseCommand, CommandError
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
    help = "Export form as JSON using the API specification."

    def add_arguments(self, parser):
        parser.add_argument(
            "form_id",
            help=_("ID of the form to be exported"),
            type=int,
        )
        parser.add_argument(
            "--archive_name",
            help=_("Write the output to the specified ZIP-file"),
            type=str,
        )
        parser.add_argument(
            "--response",
            help=_("HttpResponse object to which the output data should be written"),
            type=HttpResponse,
        )

    def handle(self, *args, **options):
        archive_name = options["archive_name"]
        response = options.get("response", None)
        form_id = options["form_id"]

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

        outfile = response or archive_name
        with zipfile.ZipFile(outfile, "w") as zip_file:
            for name, data in resources.items():
                zip_file.writestr(f"{name}.json", data)
