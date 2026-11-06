from collections.abc import Collection, Sequence
from pathlib import Path
from typing import Literal, Required, TypedDict, assert_never
from uuid import UUID

from django.conf import settings
from django.db import transaction
from django.http.request import HttpRequest
from django.utils.translation import override

import msgspec
import tablib
from import_export.results import RowResult

from openforms.formio.typing import FileComponent
from openforms.registrations.contrib.objects_api.constants import (
    PLUGIN_IDENTIFIER as OBJECTS_API_PLUGIN_IDENTIFIER,
)
from openforms.registrations.contrib.stuf_zds.plugin import (
    PLUGIN_IDENTIFIER as STUF_ZDS_PLUGIN_IDENTIFIER,
)
from openforms.registrations.contrib.zgw_apis.plugin import (
    PLUGIN_IDENTIFIER as ZGW_APIS_PLUGIN_IDENTIFIER,
)

from ..api.datastructures import FormVariableWrapper
from ..models import (
    Form,
    FormDefinition,
)
from ._mock_request import get_mock_request as _get_mock_request
from .constants import AdditionalFormConfigurationOptions
from .datastructures import FormImportOptions
from .exceptions import ImportError
from .resources import ADDITIONAL_FORM_CONFIGURATION_RESOURCES
from .serializers import (
    FormDefinitionImportSerializer,
    FormImportSerializer,
    FormLogicImportSerializer,
    FormStepImportSerializer,
    FormVariableImportSerializer,
)
from .structs import Artifact, ShallowJSONObject
from .uuid_map import UUIDMap

EXPECTED_RESOURCES = (
    "forms",
    "formDefinitions",
    "formSteps",
    "formVariables",
    "formLogic",
    "product",
    "wmsTileLayers",
    "wmtsTileLayers",
    "yiviAttributeGroups",
)


@transaction.atomic
def import_form(
    import_file: Path | str,
    import_options: FormImportOptions,
    existing_form_instance: Form | None = None,
) -> Form | None:
    artifact = Artifact.from_zip(import_file)
    return import_form_data(artifact, import_options, existing_form_instance)


class ImportContext(TypedDict):
    request: HttpRequest
    is_import: Literal[True]
    import_options: FormImportOptions
    restoring_previous_version: bool
    form: Form | None


@transaction.atomic
@override(language=settings.LANGUAGE_CODE)
def import_form_data(
    artifact: Artifact,
    import_options: FormImportOptions,
    existing_form_instance: Form | None = None,
) -> Form | None:
    uuid_map = UUIDMap()

    request: HttpRequest = _get_mock_request()
    imported_form: Form | None = None
    restoring_previous_version: bool = existing_form_instance is not None

    context: ImportContext = {
        "request": request,
        "is_import": True,
        "import_options": import_options,
        "restoring_previous_version": restoring_previous_version,
        "form": existing_form_instance,
    }

    # Import additional data
    _import_additional_form_configuration_data(
        artifact=artifact,
        import_options=import_options,
        uuid_map=uuid_map,
        force_deep_compare=restoring_previous_version,
    )

    if not len(forms_data := artifact.forms) == 1:
        raise ImportError("The export artifact must contain exactly one form.")

    imported_form = _import_form_resource(
        data=forms_data,
        uuid_map=uuid_map,
        context=context,
        existing_form_instance=existing_form_instance,
    )

    assert imported_form is not None, "No form data has been imported"
    context["form"] = imported_form

    form_definitions = _import_form_definition_resources(
        data=artifact.form_definitions, uuid_map=uuid_map, context=context
    )
    move_file_registration_options(imported_form, form_definitions)
    _import_form_step_resources(
        data=artifact.form_steps, uuid_map=uuid_map, context=context
    )
    _import_form_variable_resources(
        data=artifact.form_variables, uuid_map=uuid_map, context=context
    )
    _import_form_logic_resources(
        data=artifact.form_logic, uuid_map=uuid_map, context=context
    )
    return imported_form


def _import_additional_form_configuration_data(
    artifact: Artifact,
    import_options: FormImportOptions,
    uuid_map: UUIDMap,
    force_deep_compare: bool = False,
) -> None:
    """
    Import additional form configuration data from the given resources.

    :param resources: A mapping of resource names to their JSON data.
    :param import_options: The import options, specifying which additional form
        configuration data to import.
    :param uuid_map: The UUID mapping to update with the imported data.
    :param force_deep_compare: Whether to force a deep comparison during import.
    """
    resources_to_import = set(import_options.additional_form_configuration)

    for option in resources_to_import:
        dataset: tablib.Dataset | msgspec.UnsetType
        # look up the dataset
        match option:
            case AdditionalFormConfigurationOptions.product:
                dataset = artifact.product
            case AdditionalFormConfigurationOptions.wms_tile_layers:
                dataset = artifact.wms_tile_layers
            case AdditionalFormConfigurationOptions.wmts_tile_layers:
                dataset = artifact.wmts_tile_layers
            case AdditionalFormConfigurationOptions.yivi_attribute_groups:
                dataset = artifact.yivi_attribute_groups
            case _:  # pragma: no cover
                assert_never(option)

        # check if there was import data provided at all
        if dataset is msgspec.UNSET:
            continue

        ResourceCls = ADDITIONAL_FORM_CONFIGURATION_RESOURCES[option]

        # Run the import data through the resource
        resource = ResourceCls(force_deep_compare=force_deep_compare)
        results = resource.import_data(dataset)

        # Add the import results to the uuid mapping
        for result in results:
            identifier_field: str = resource.identifier_field
            # If the old identifier is not present, then something is wrong with the
            # import data
            old_identifier: str | None = result.row_values.get(identifier_field)
            assert old_identifier is not None

            new_identifier: str | UUID | None = None
            match result.import_type:
                case RowResult.IMPORT_TYPE_NEW:
                    new_identifier = getattr(result.instance, identifier_field)

                case RowResult.IMPORT_TYPE_SKIP:
                    new_identifier = getattr(result.original, identifier_field)

                case RowResult.IMPORT_TYPE_INVALID:  # pragma: no cover
                    assert result.validation_error is not None
                    raise result.validation_error

                case RowResult.IMPORT_TYPE_ERROR:
                    exceptions = [error.error for error in result.errors]
                    raise ExceptionGroup(
                        f"Something went wrong importing the '{option}' data",
                        exceptions,
                    )

                case _:  # pragma: no cover
                    # If the import results in anything other than new, skip or an error,
                    # then something is going wrong
                    raise ValueError(f"Invalid import type: {result.import_type}")

            assert new_identifier is not None
            assert isinstance(new_identifier, (str, UUID))
            uuid_map.add(old_identifier, new_identifier)


def _import_form_resource(
    data: Sequence[ShallowJSONObject],
    uuid_map: UUIDMap,
    context: ImportContext,
    existing_form_instance: Form | None,
) -> Form | None:
    assert len(data) == 1, "expected exactly one form in the import data"
    form_data = uuid_map.apply_to(data[0])
    old_uuid: str | None = form_data.get("uuid")

    # only after deserializing do we know something for sure about the shape of the data
    deserialized = FormImportSerializer(
        data=form_data,
        context=context,  # pyright: ignore[reportArgumentType]
        instance=existing_form_instance,
    )

    deserialized.is_valid(raise_exception=True)
    imported_form: Form = deserialized.save()

    if instance := deserialized.instance:
        uuid_map.add(old_uuid, instance.uuid)

    return imported_form


def _import_form_definition_resources(
    data: Sequence[ShallowJSONObject],
    uuid_map: UUIDMap,
    context: ImportContext,
) -> list[FormDefinition]:
    form_definitions: list[FormDefinition] = []
    data = uuid_map.apply_to(data)

    for entry in data:
        old_uuid: str | None = entry.get("uuid")

        instance: FormDefinition | None = FormDefinition.objects.filter(
            configuration=entry.get("configuration"),
            is_reusable=True,
        ).first()

        deserialized = FormDefinitionImportSerializer(
            data=entry,
            context=context,  # pyright: ignore[reportArgumentType]
            instance=instance,
        )
        deserialized.is_valid(raise_exception=True)
        instance = deserialized.save()
        assert instance is not None
        form_definitions.append(instance)
        uuid_map.add(old_uuid, instance.uuid)

    return form_definitions


def _import_form_step_resources(
    data: Sequence[ShallowJSONObject],
    uuid_map: UUIDMap,
    context: ImportContext,
) -> None:
    data = uuid_map.apply_to(data)

    for entry in data:
        old_uuid: str | None = entry.get("uuid")

        deserialized = FormStepImportSerializer(
            data=entry,
            context=context,  # pyright: ignore[reportArgumentType]
        )

        deserialized.is_valid(raise_exception=True)
        instance = deserialized.save()
        assert instance is not None
        uuid_map.add(old_uuid, instance.uuid)


def _import_form_variable_resources(
    data: Sequence[ShallowJSONObject],
    uuid_map: UUIDMap,
    context: ImportContext,
) -> None:
    data = uuid_map.apply_to(data)
    assert isinstance(context["form"], Form)
    form = context["form"]

    deserialized = FormVariableImportSerializer(
        many=True,
        data=data,
        context={
            **context,
            "forms": ({str(form.uuid): form}),
            "form_definitions": {
                str(fd.uuid): fd
                for fd in FormDefinition.objects.filter(formstep__form=form)
            },
        },
    )

    deserialized.is_valid(raise_exception=True)
    deserialized.save()


def _import_form_logic_resources(
    data: Sequence[ShallowJSONObject],
    uuid_map: UUIDMap,
    context: ImportContext,
) -> None:
    data = uuid_map.apply_to(data)
    assert isinstance(context["form"], Form)
    form = context["form"]

    updated_context = {
        **context,
        "forms": ({str(form.uuid): form}),
        "form_definitions": {
            str(fd.uuid): fd
            for fd in FormDefinition.objects.filter(formstep__form=form)
        },
        "form_variables": FormVariableWrapper(form),
        "form_steps": {
            form_step.uuid: form_step
            for form_step in form.formstep_set.all().order_by("order")
        },
    }

    for entry in data:
        old_uuid: str | None = entry.get("uuid")
        deserialized = FormLogicImportSerializer(data=entry, context=updated_context)

        deserialized.is_valid(raise_exception=True)
        instance = deserialized.save()
        assert instance is not None
        uuid_map.add(old_uuid, instance.uuid)


class FileComponentOptions(TypedDict, total=False):
    key: Required[str]
    document_type_description: str
    organization_rsin: str
    confidentiality_level: str
    title: str


# Original commit 2d1ef3cbaecd42350470864a1dbb9a134868732c
def move_file_registration_options(
    form: Form, form_definitions: Collection[FormDefinition]
) -> None:
    from typing import cast  # noqa: TID251

    relevant_backends = [
        backend
        for backend in form.registration_backends.all()
        if backend.backend
        in (
            OBJECTS_API_PLUGIN_IDENTIFIER,
            STUF_ZDS_PLUGIN_IDENTIFIER,
            ZGW_APIS_PLUGIN_IDENTIFIER,
        )
    ]
    if not relevant_backends:
        return

    # collect all file components, including the ones inside edit grids
    file_component_options: dict[str, FileComponentOptions] = {}
    for fd in form_definitions:
        for component in fd.configuration_wrapper:
            if component["type"] != "file":
                continue
            component = cast(FileComponent, component)

            if not (registration := component.get("registration")):
                continue

            opts: FileComponentOptions = {"key": component["key"]}

            # NOTE: we ignore the catalogue information - the backend-level catalogue
            # option is used and this is validate at the serializer level
            document_type_description = (registration.get("documentType") or {}).get(
                "description"
            )
            organization_rsin = registration.get("bronorganisatie")
            confidentiality_level = registration.get("docVertrouwelijkheidaanduiding")
            title = registration.get("titel")

            if document_type_description:
                opts["document_type_description"] = document_type_description
            if organization_rsin:
                opts["organization_rsin"] = organization_rsin
            if confidentiality_level:
                opts["confidentiality_level"] = confidentiality_level
            if title:
                opts["title"] = title

            if len(opts.keys()) != 1:
                file_component_options[component["key"]] = opts

    if not file_component_options:
        return

    files = list(file_component_options.values())

    def _file_for_stuf_zds(opts: FileComponentOptions):
        if title := opts.get("title"):
            return {"key": opts["key"], "title": title}
        return None

    files_for_stuf_zds = [o for opts in files if (o := _file_for_stuf_zds(opts))]

    for backend in relevant_backends:
        options = backend.options
        if "files" in options:
            continue

        plugin_id = backend.backend
        if plugin_id in (OBJECTS_API_PLUGIN_IDENTIFIER, ZGW_APIS_PLUGIN_IDENTIFIER):
            options["files"] = files
        elif plugin_id == STUF_ZDS_PLUGIN_IDENTIFIER:
            options["files"] = files_for_stuf_zds
        else:  # pragma: no cover
            raise ValueError(f"Unknown registration plugin '{plugin_id}'.")

        # Persist the changes made to the registration backend
        backend.save()
