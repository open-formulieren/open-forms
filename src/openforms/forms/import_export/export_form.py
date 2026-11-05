from collections.abc import Mapping
from os import PathLike

from django.http.response import HttpResponseBase

import msgspec
from tablib import Dataset

from openforms.variables.constants import FormVariableSources

from ..models import Form, FormLogic, FormStep
from ._mock_request import get_mock_request as _get_mock_request
from .constants import AdditionalFormConfigurationOptions
from .datastructures import FormExportOptions
from .resources import ADDITIONAL_FORM_CONFIGURATION_RESOURCES
from .serializers import (
    FormDefinitionExportSerializer,
    FormExportSerializer,
    FormLogicExportSerializer,
    FormStepExportSerializer,
    FormVariableExportSerializer,
)
from .structs import Artifact


def export_form(
    form_id: int,
    export_options: FormExportOptions,
    archive_name: str | PathLike[str] | None = None,
    response: HttpResponseBase | None = None,
):
    form = Form.objects.get(pk=form_id)
    artifact = get_export_artifact(form, export_options)
    outfile = response or archive_name
    assert outfile, "Either response or archive_name must be provided"
    artifact.write_zip(target=outfile)  # pyright: ignore[reportArgumentType]
    return outfile


def get_export_artifact(form: Form, export_options: FormExportOptions) -> Artifact:
    """
    Prepare a single form export artifact.
    """
    form_steps = FormStep.objects.filter(form__pk=form.pk).select_related(
        "form_definition"
    )
    form_definitions = [form_step.form_definition for form_step in form_steps]
    form_logic = FormLogic.objects.filter(form=form)

    # Export only user defined variables
    # The component variables should be regenerated from the form definition configuration
    # The static variables should be created for each form
    form_variables = form.formvariable_set.filter(
        source=FormVariableSources.user_defined
    ).order_by("pk")

    request = _get_mock_request()
    context = {
        "request": request,
        "export_options": export_options,
        "form": form,
        "is_exporting": True,
    }

    forms = [FormExportSerializer(instance=form, context=context).data]
    form_definitions = FormDefinitionExportSerializer(
        instance=form_definitions, many=True, context=context
    ).data
    form_steps = FormStepExportSerializer(
        instance=form_steps, many=True, context=context
    ).data
    form_logic = FormLogicExportSerializer(
        instance=form_logic, many=True, context=context
    ).data
    form_variables = FormVariableExportSerializer(
        instance=form_variables, many=True, context=context
    ).data

    additional_form_configuration_data = get_additional_form_configuration_data(
        form, export_options
    )
    return Artifact(
        forms=list(forms),
        form_steps=list(form_steps),
        form_definitions=list(form_definitions),
        form_logic=list(form_logic),
        form_variables=list(form_variables),
        product=additional_form_configuration_data.get(
            AdditionalFormConfigurationOptions.product,
            msgspec.UNSET,
        ),
        wms_tile_layers=additional_form_configuration_data.get(
            AdditionalFormConfigurationOptions.wms_tile_layers,
            msgspec.UNSET,
        ),
        wmts_tile_layers=additional_form_configuration_data.get(
            AdditionalFormConfigurationOptions.wmts_tile_layers,
            msgspec.UNSET,
        ),
        yivi_attribute_groups=additional_form_configuration_data.get(
            AdditionalFormConfigurationOptions.yivi_attribute_groups,
            msgspec.UNSET,
        ),
    )


def get_additional_form_configuration_data(
    form: Form, export_options: FormExportOptions
) -> Mapping[AdditionalFormConfigurationOptions, Dataset]:
    """
    Create a dictionary of additional form configuration data for the given form.

    The keys are the additional export resource option enums, and the values are the
    datasets representing the resource data.
    """
    options_to_include = set(export_options.additional_form_configuration)
    if unknown_options := options_to_include - set(
        ADDITIONAL_FORM_CONFIGURATION_RESOURCES
    ):
        raise ValueError(
            f"Invalid additional form configuration option(s): {unknown_options}"
        )
    additional_data: dict[AdditionalFormConfigurationOptions, Dataset] = {
        option: ADDITIONAL_FORM_CONFIGURATION_RESOURCES[option]().export_for_form(form)
        for option in options_to_include
    }
    return additional_data
