import json
import zipfile
from typing import Any

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone

from rest_framework.test import APIRequestFactory

from openforms.forms.models import Form, FormDefinition, FormLogic, FormStep
from openforms.variables.constants import FormVariableSources

from .constants import EXPORT_META_KEY
from .serializers import (
    FormDefinitionExportSerializer,
    FormExportSerializer,
    FormLogicExportSerializer,
    FormStepExportSerializer,
    FormVariableExportSerializer,
)
from .typing import FormExportOptions
from .utils import get_additional_form_configuration_data


def _get_mock_request():
    factory = APIRequestFactory()
    first_allowed_host = (
        settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else "testserver"
    )
    server_name = first_allowed_host if first_allowed_host != "*" else "testserver"
    request = factory.get("/", SERVER_NAME=server_name)
    request.is_mock_request = True  # pyright: ignore[reportAttributeAccessIssue]
    return request


def export_form(
    form_id, export_options: FormExportOptions, archive_name=None, response=None
):
    resources = form_to_json(form_id, export_options)

    outfile = response or archive_name
    with zipfile.ZipFile(outfile, "w") as zip_file:
        for name, data in resources.items():
            zip_file.writestr(f"{name}.json", data)
    return outfile


def form_to_json(form_id: int, export_options: FormExportOptions) -> dict:
    form = Form.objects.get(pk=form_id)

    # Reset the submission counter
    form.submission_counter = 0

    form_steps = FormStep.objects.filter(form__pk=form_id).select_related(
        "form_definition"
    )

    form_definitions = FormDefinition.objects.filter(
        pk__in=form_steps.values_list("form_definition", flat=True)
    )

    form_logic = FormLogic.objects.filter(form=form)

    # Export only user defined variables
    # The component variables should be regenerated from the form definition configuration
    # The static variables should be created for each form
    form_variables = form.formvariable_set.filter(
        source=FormVariableSources.user_defined
    )

    request = _get_mock_request()

    forms = [
        FormExportSerializer(
            instance=form,
            context={"request": request, "export_options": export_options},
        ).data
    ]
    form_definitions = FormDefinitionExportSerializer(
        instance=form_definitions,
        many=True,
        context={
            "request": request,
            "export_options": export_options,
            "form": form,
        },
    ).data
    form_steps = FormStepExportSerializer(
        instance=form_steps,
        many=True,
        context={"request": request, "export_options": export_options},
    ).data
    form_logic = FormLogicExportSerializer(
        instance=form_logic,
        many=True,
        context={"request": request, "export_options": export_options},
    ).data
    form_variables = FormVariableExportSerializer(
        instance=form_variables,
        many=True,
        context={"request": request, "export_options": export_options},
    ).data

    resources = {
        "forms": to_json(forms),
        "formSteps": to_json(form_steps),
        "formDefinitions": to_json(form_definitions),
        "formLogic": to_json(form_logic),
        "formVariables": to_json(form_variables),
        # Include additional configuration data in the export resources, based on the form.
        **(
            get_additional_form_configuration_data(form, export_options)
            if export_options is not None
            else {}
        ),
        EXPORT_META_KEY: to_json(
            {
                "of_release": settings.RELEASE,
                "of_git_sha": settings.GIT_SHA,
                "created": timezone.now().isoformat(),
            }
        ),
    }

    return resources


def to_json(obj: Any):
    return json.dumps(obj, cls=DjangoJSONEncoder)
