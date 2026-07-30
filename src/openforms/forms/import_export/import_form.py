import json
import zipfile
from collections.abc import Collection
from typing import Required, TypedDict

from django.conf import settings
from django.db import transaction
from django.utils.translation import override

from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from openforms.forms.api.datastructures import FormVariableWrapper
from openforms.forms.models import (
    Form,
    FormDefinition,
)
from openforms.registrations.contrib.objects_api.constants import (
    PLUGIN_IDENTIFIER as OBJECTS_API_PLUGIN_IDENTIFIER,
)
from openforms.registrations.contrib.stuf_zds.plugin import (
    PLUGIN_IDENTIFIER as STUF_ZDS_PLUGIN_IDENTIFIER,
)
from openforms.registrations.contrib.zgw_apis.plugin import (
    PLUGIN_IDENTIFIER as ZGW_APIS_PLUGIN_IDENTIFIER,
)

from .serializers import (
    FormDefinitionImportSerializer,
    FormImportSerializer,
    FormLogicImportSerializer,
    FormStepImportSerializer,
    FormVariableImportSerializer,
)
from .typing import FormImportOptions
from .utils import import_additional_form_configuration_data

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


def _get_mock_request():
    factory = APIRequestFactory()
    first_allowed_host = (
        settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else "testserver"
    )
    server_name = first_allowed_host if first_allowed_host != "*" else "testserver"
    request = factory.get("/", SERVER_NAME=server_name)
    request.is_mock_request = True  # pyright: ignore[reportAttributeAccessIssue]
    return request


@transaction.atomic
def import_form(
    import_file, import_options: FormImportOptions, existing_form_instance=None
) -> Form | None:
    import_data = {}
    with zipfile.ZipFile(import_file, "r") as zip_file:
        for resource in EXPECTED_RESOURCES:
            if f"{resource}.json" in zip_file.namelist():
                import_data[resource] = zip_file.read(f"{resource}.json").decode()

    return import_form_data(import_data, import_options, existing_form_instance)


@transaction.atomic
@override(language=settings.LANGUAGE_CODE)
def import_form_data(
    import_data: dict,
    import_options: FormImportOptions,
    existing_form_instance: Form | None = None,
) -> Form | None:
    uuid_mapping = {}

    request = _get_mock_request()
    created_form: Form | None = None

    # Import additional data
    import_additional_form_configuration_data(
        resources=import_data,
        import_options=import_options,
        uuid_mapping=uuid_mapping,
        restore_previous_form_version=existing_form_instance is not None,
    )

    if (forms_data := import_data.get("forms")) is not None:
        created_form = _import_form_resource(
            data=forms_data,
            uuid_mapping=uuid_mapping,
            request=request,
            import_options=import_options,
            existing_form_instance=existing_form_instance,
        )

    if (form_definitions_data := import_data.get("formDefinitions")) is not None:
        form_definitions = _import_form_definition_resources(
            data=form_definitions_data,
            uuid_mapping=uuid_mapping,
            form=created_form,
            request=request,
            import_options=import_options,
        )
        move_file_registration_options(created_form, form_definitions)

    if (form_steps_data := import_data.get("formSteps")) is not None:
        _import_form_step_resources(
            data=form_steps_data,
            uuid_mapping=uuid_mapping,
            form=created_form,
            request=request,
            import_options=import_options,
        )

    if (form_variables_data := import_data.get("formVariables")) is not None:
        _import_form_variable_resources(
            data=form_variables_data,
            uuid_mapping=uuid_mapping,
            form=created_form,
            request=request,
            import_options=import_options,
        )

    if (form_logic_data := import_data.get("formLogic")) is not None:
        _import_form_logic_resources(
            data=form_logic_data,
            uuid_mapping=uuid_mapping,
            form=created_form,
            request=request,
            import_options=import_options,
        )

    return created_form


def _import_form_resource(
    data: dict,
    uuid_mapping: dict[str, str],
    request: Request,
    import_options: FormImportOptions,
    existing_form_instance: Form | None,
) -> Form | None:
    imported_form = None

    for old, new in uuid_mapping.items():
        data = data.replace(old, new)

    for entry in json.loads(data):
        old_uuid = entry.get("uuid")

        deserialized = FormImportSerializer(
            data=entry,
            context={
                "request": request,
                "is_import": True,
                "import_options": import_options,
            },
            instance=existing_form_instance,
        )

        try:
            deserialized.is_valid(raise_exception=True)
            imported_form = deserialized.save()

            if hasattr(deserialized.instance, "uuid") and "uuid" in entry:
                uuid_mapping[old_uuid] = str(deserialized.instance.uuid)
        except ValidationError as e:
            raise e

    return imported_form


def _import_form_definition_resources(
    data: dict,
    uuid_mapping: dict[str, str],
    form: Form,
    request: Request,
    import_options: FormImportOptions,
) -> list[FormDefinition]:
    form_definitions: list[FormDefinition] = []

    for old, new in uuid_mapping.items():
        data = data.replace(old, new)

    for entry in json.loads(data):
        old_uuid = entry.get("uuid")

        instance: FormDefinition | None = None
        if import_options.reuse_form_definitions:
            # @TODO compare FD op component config zonder UUID's
            instance = FormDefinition.objects.filter(
                configuration=entry.get("configuration"),
                is_reusable=True,
            ).first()

        deserialized = FormDefinitionImportSerializer(
            data=entry,
            context={
                "request": request,
                "form": form,
                "is_import": True,
                "import_options": import_options,
            },
            instance=instance,
        )

        try:
            deserialized.is_valid(raise_exception=True)
            form_definitions.append(deserialized.save())

            if hasattr(deserialized.instance, "uuid") and "uuid" in entry:
                uuid_mapping[old_uuid] = str(deserialized.instance.uuid)
        except ValidationError as e:
            raise e

    return form_definitions


def _import_form_step_resources(
    data: dict,
    uuid_mapping: dict[str, str],
    form: Form,
    request: Request,
    import_options: FormImportOptions,
):
    for old, new in uuid_mapping.items():
        data = data.replace(old, new)

    for entry in json.loads(data):
        old_uuid = entry.get("uuid")

        deserialized = FormStepImportSerializer(
            data=entry,
            context={
                "request": request,
                "form": form,
                "is_import": True,
                "import_options": import_options,
            },
        )

        try:
            deserialized.is_valid(raise_exception=True)
            deserialized.save()

            if hasattr(deserialized.instance, "uuid") and "uuid" in entry:
                uuid_mapping[old_uuid] = str(deserialized.instance.uuid)
        except ValidationError as e:
            raise e


def _import_form_variable_resources(
    data: dict,
    uuid_mapping: dict[str, str],
    form: Form,
    request: Request,
    import_options: FormImportOptions,
):
    for old, new in uuid_mapping.items():
        data = data.replace(old, new)

    for entry in json.loads(data):
        old_uuid = entry.get("uuid")

        deserialized = FormVariableImportSerializer(
            data=entry,
            context={
                "request": request,
                "form": form,
                "is_import": True,
                "import_options": import_options,
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

            if hasattr(deserialized.instance, "uuid") and "uuid" in entry:
                uuid_mapping[old_uuid] = str(deserialized.instance.uuid)
        except ValidationError as e:
            raise e


def _import_form_logic_resources(
    data: dict,
    uuid_mapping: dict[str, str],
    form: Form,
    request: Request,
    import_options: FormImportOptions,
):
    for old, new in uuid_mapping.items():
        data = data.replace(old, new)

    for entry in json.loads(data):
        old_uuid = entry.get("uuid")

        deserialized = FormLogicImportSerializer(
            data=entry,
            context={
                "request": request,
                "form": form,
                "is_import": True,
                "import_options": import_options,
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

            if hasattr(deserialized.instance, "uuid") and "uuid" in entry:
                uuid_mapping[old_uuid] = str(deserialized.instance.uuid)
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
):
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
