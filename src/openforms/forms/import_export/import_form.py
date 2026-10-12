import json
import zipfile
from collections.abc import Collection, MutableMapping
from pathlib import Path
from typing import Any, Protocol, Required, TypedDict
from uuid import UUID

from django.conf import settings
from django.db import transaction
from django.http.request import HttpRequest
from django.utils.translation import override

from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory

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
from .serializers import (
    FormDefinitionImportSerializer,
    FormImportSerializer,
    FormLogicImportSerializer,
    FormStepImportSerializer,
    FormVariableImportSerializer,
)
from .typing import (
    FormData,
    FormDefinitionData,
    FormLogicData,
    FormStepData,
    FormVariableData,
)

EXPECTED_RESOURCES = (
    "forms",
    "formDefinitions",
    "formSteps",
    "formVariables",
    "formLogic",
)


class HasUUID(Protocol):
    uuid: UUID


class UUIDMap:
    def __init__(self):
        self.mapping: MutableMapping[
            str, str
        ] = {}  # Keys are old UUIDs, values are new UUIDs.

    def apply_to_data(self, data: str) -> str:
        """
        Replace all old UUID's for their new counterpart in the data, and return the
        updated data.
        """
        for old, new in self.mapping.items():
            data = data.replace(old, new)
        return data

    def add(self, old_uuid: str | None, new_instance: HasUUID | None) -> None:
        """
        Add the old and new UUID's of an instance to the mapping.
        """
        if old_uuid and new_instance:
            self.mapping[old_uuid] = str(new_instance.uuid)


def _get_mock_request() -> HttpRequest:
    factory = APIRequestFactory()
    first_allowed_host = (
        settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else "testserver"
    )
    server_name = first_allowed_host if first_allowed_host != "*" else "testserver"
    request = factory.get("/", SERVER_NAME=server_name)
    request.is_mock_request = True  # pyright: ignore[reportAttributeAccessIssue]
    return request


@transaction.atomic
def import_form(import_file: Path, existing_form_instance=None) -> Form | None:
    import_data: dict[str, str] = {}
    with zipfile.ZipFile(import_file, "r") as zip_file:
        for resource in EXPECTED_RESOURCES:
            if f"{resource}.json" in zip_file.namelist():
                import_data[resource] = zip_file.read(f"{resource}.json").decode()

    return import_form_data(import_data, existing_form_instance, deactivate_form=True)


@transaction.atomic
@override(language=settings.LANGUAGE_CODE)
def import_form_data(
    import_data: dict[str, str],
    existing_form_instance: Form | None = None,
    deactivate_form: bool = False,
) -> Form | None:
    uuid_mapping = UUIDMap()

    request: HttpRequest = _get_mock_request()
    imported_form: Form | None = None

    context = {
        "request": request,
        "is_import": True,
    }

    if forms_data := import_data.get("forms"):
        imported_form = _import_form_resource(
            data=forms_data,
            uuid_mapping=uuid_mapping,
            context=context,
            existing_form_instance=existing_form_instance,
            deactivate_form=deactivate_form,
        )

    assert imported_form is not None, "No form data has been imported"
    context = {
        **context,
        "form": imported_form,
    }

    if form_definitions_data := import_data.get("formDefinitions"):
        form_definitions = _import_form_definition_resources(
            data=form_definitions_data, uuid_mapping=uuid_mapping, context=context
        )
        move_file_registration_options(imported_form, form_definitions)

    if form_steps_data := import_data.get("formSteps"):
        _import_form_step_resources(
            data=form_steps_data, uuid_mapping=uuid_mapping, context=context
        )

    if form_variables_data := import_data.get("formVariables"):
        _import_form_variable_resources(
            data=form_variables_data, uuid_mapping=uuid_mapping, context=context
        )

    if form_logic_data := import_data.get("formLogic"):
        _import_form_logic_resources(
            data=form_logic_data, uuid_mapping=uuid_mapping, context=context
        )

    return imported_form


def _import_form_resource(
    data: str,
    uuid_mapping: UUIDMap,
    context: dict[str, Any],
    existing_form_instance: Form | None,
    deactivate_form: bool,
) -> Form | None:
    data = uuid_mapping.apply_to_data(data)

    forms = json.loads(data)
    assert len(forms) == 1, "expected exactly one form in the import data"

    form: FormData = forms[0]
    old_uuid: str | None = form.get("uuid")

    deserialized = FormImportSerializer(
        data=form,
        context={**context, "deactivate_form": deactivate_form},
        instance=existing_form_instance,
    )

    try:
        deserialized.is_valid(raise_exception=True)
        imported_form: Form = deserialized.save()

        uuid_mapping.add(old_uuid, deserialized.instance)
    except ValidationError as e:
        raise e

    return imported_form


def _import_form_definition_resources(
    data: str,
    uuid_mapping: UUIDMap,
    context: dict[str, Any],
) -> list[FormDefinition]:
    form_definitions: list[FormDefinition] = []
    data = uuid_mapping.apply_to_data(data)

    for entry in json.loads(data):
        entry: FormDefinitionData = entry
        old_uuid: str | None = entry.get("uuid")

        instance: FormDefinition | None = FormDefinition.objects.filter(
            configuration=entry.get("configuration"),
            is_reusable=True,
        ).first()

        deserialized = FormDefinitionImportSerializer(
            data=entry, context=context, instance=instance
        )

        try:
            deserialized.is_valid(raise_exception=True)
            form_definitions.append(deserialized.save())

            uuid_mapping.add(old_uuid, deserialized.instance)
        except ValidationError as e:
            raise e

    return form_definitions


def _import_form_step_resources(
    data: str,
    uuid_mapping: UUIDMap,
    context: dict[str, Any],
) -> None:
    data = uuid_mapping.apply_to_data(data)

    for entry in json.loads(data):
        entry: FormStepData = entry
        old_uuid: str | None = entry.get("uuid")

        deserialized = FormStepImportSerializer(data=entry, context=context)

        try:
            deserialized.is_valid(raise_exception=True)
            deserialized.save()

            uuid_mapping.add(old_uuid, deserialized.instance)
        except ValidationError as e:
            raise e


def _import_form_variable_resources(
    data: str, uuid_mapping: UUIDMap, context: dict[str, Any]
) -> None:
    data = uuid_mapping.apply_to_data(data)

    for entry in json.loads(data):
        entry: FormVariableData = entry
        form: Form = context["form"]

        deserialized = FormVariableImportSerializer(
            data=entry,
            context={
                **context,
                "forms": ({str(form.uuid): form}),
                "form_definitions": {
                    str(fd.uuid): fd
                    for fd in FormDefinition.objects.filter(formstep__form=form)
                },
            },
        )

        try:
            deserialized.is_valid(raise_exception=True)
            deserialized.save()
        except ValidationError as e:
            raise e


def _import_form_logic_resources(
    data: str, uuid_mapping: UUIDMap, context: dict[str, Any]
) -> None:
    data = uuid_mapping.apply_to_data(data)

    for entry in json.loads(data):
        entry: FormLogicData = entry
        old_uuid: str | None = entry.get("uuid")
        form: Form = context["form"]

        deserialized = FormLogicImportSerializer(
            data=entry,
            context={
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
            },
        )

        try:
            deserialized.is_valid(raise_exception=True)
            deserialized.save()

            uuid_mapping.add(old_uuid, deserialized.instance)
        except ValidationError as e:
            raise e


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
