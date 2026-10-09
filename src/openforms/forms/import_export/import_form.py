import json
import random
import string
import zipfile
from collections.abc import Collection
from pathlib import Path
from typing import Any, Required, TypedDict

from django.conf import settings
from django.db import transaction
from django.http.request import HttpRequest
from django.utils.translation import override

import structlog
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory

from openforms.formio.migration_converters import CONVERTERS, DEFINITION_CONVERTERS
from openforms.formio.typing import FileComponent
from openforms.formio.utils import iter_components
from openforms.registrations.contrib.objects_api.constants import (
    PLUGIN_IDENTIFIER as OBJECTS_API_PLUGIN_IDENTIFIER,
)
from openforms.registrations.contrib.stuf_zds.plugin import (
    PLUGIN_IDENTIFIER as STUF_ZDS_PLUGIN_IDENTIFIER,
)
from openforms.registrations.contrib.zgw_apis.plugin import (
    PLUGIN_IDENTIFIER as ZGW_APIS_PLUGIN_IDENTIFIER,
)
from openforms.typing import JSONObject

from ..api.datastructures import FormVariableWrapper
from ..constants import FormTypeChoices, LogicActionTypes
from ..models import (
    Form,
    FormDefinition,
    FormLogic,
    FormStep,
    FormVariable,
)
from .serializers import (
    FormDefinitionImportSerializer,
    FormImportSerializer,
    FormLogicImportSerializer,
    FormStepImportSerializer,
    FormVariableImportSerializer,
)
from .typing import (
    FormDataRepresentation,
    FormDefinitionDataRepresentation,
    FormLogicDataRepresentation,
    FormStepDataRepresentation,
    FormVariableDataRepresentation,
)

EXPECTED_RESOURCES = (
    "forms",
    "formDefinitions",
    "formSteps",
    "formVariables",
    "formLogic",
)

logger = structlog.stdlib.get_logger(__name__)


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

    return import_form_data(import_data, existing_form_instance)


@transaction.atomic
@override(language=settings.LANGUAGE_CODE)
def import_form_data(
    import_data: dict[str, str],
    existing_form_instance: Form | None = None,
) -> Form | None:
    uuid_mapping: dict[str, str] = {}

    request: HttpRequest = _get_mock_request()
    imported_form: Form | None = None

    # when restoring a previous version, delete the current form configuration,
    # it will be replaced with the import data.
    if existing_form_instance:
        form_steps = FormStep.objects.filter(form=existing_form_instance)
        # delete single-use form definitions, they're orphan nodes when deleting the steps
        fd_ids = list(
            FormDefinition.objects.filter(
                is_reusable=False, formstep__in=form_steps
            ).values_list("id", flat=True)
        )
        form_steps.delete()
        FormDefinition.objects.filter(id__in=fd_ids).delete()
        FormLogic.objects.filter(form=existing_form_instance).delete()
        FormVariable.objects.filter(form=existing_form_instance).delete()

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


def update_uuids(data: str, uuid_mapping: dict[str, str]) -> str:
    for old, new in uuid_mapping.items():
        data = data.replace(old, new)
    return data


def _import_form_resource(
    data: str,
    uuid_mapping: dict[str, str],
    context: dict[str, Any],
    existing_form_instance: Form | None,
) -> Form | None:
    imported_form: Form | None = None
    data = update_uuids(data, uuid_mapping)

    for entry in json.loads(data):
        entry: FormDataRepresentation = entry
        old_uuid: str | None = entry.get("uuid")

        # we can only extract a category UUID from the URL here, but that requires
        # an exact match and we currently don't provide import/export functionality
        # for categories. Relying on ID/Name is not much better than guesswork either,
        # so we always import forms with NO category at all to prevent import errors.
        # See #1774 for one such example of an error.
        entry["category"] = ""
        # theme overrides cannot be imported, since the theme records/FKs have to
        # exist in the target environment. Importing/exporting themes is also not
        # possible at this time, so we reset the theme and admins need to update
        # the imported form.
        entry["theme"] = ""

        # forms before v4.0 do not have the type field so in case we import an
        # old appointment form we have to make sure that the form has the right
        # type configured (by default is regular)
        if appointment_options := entry.get("appointment_options"):
            if appointment_options.get("is_appointment"):
                entry["type"] = FormTypeChoices.appointment

        if not existing_form_instance:
            entry["active"] = False

        # If there is a slug, make sure that it's unique
        if (form_slug := entry.get("slug")) and Form.objects.filter(
            slug=form_slug
        ).first() is not None:
            entry["slug"] = (
                f"{form_slug}-{''.join(random.choices(string.hexdigits, k=6))}"
            )

        deserialized = FormImportSerializer(
            data=entry, context=context, instance=existing_form_instance
        )

        try:
            deserialized.is_valid(raise_exception=True)
            imported_form = deserialized.save()

            if (
                old_uuid
                and deserialized.instance
                and hasattr(deserialized.instance, "uuid")
            ):
                uuid_mapping[old_uuid] = str(deserialized.instance.uuid)
        except ValidationError as e:
            raise e

    return imported_form


def _import_form_definition_resources(
    data: str,
    uuid_mapping: dict[str, str],
    context: dict[str, Any],
) -> list[FormDefinition]:
    form_definitions: list[FormDefinition] = []
    data = update_uuids(data, uuid_mapping)

    for entry in json.loads(data):
        entry: FormDefinitionDataRepresentation = entry
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

            apply_component_conversions(deserialized.validated_data["configuration"])
            apply_definition_conversions(deserialized.validated_data["configuration"])

            form_definitions.append(deserialized.save())

            if (
                old_uuid
                and deserialized.instance
                and hasattr(deserialized.instance, "uuid")
            ):
                uuid_mapping[old_uuid] = str(deserialized.instance.uuid)
        except ValidationError as e:
            raise e

    return form_definitions


def apply_component_conversions(configuration: JSONObject) -> None:
    """
    Apply the known formio component conversions to the entire form definition.
    """
    log = logger.bind(action="forms.apply_component_conversions")
    for component in iter_components(configuration):
        if not (component_type := component.get("type")):  # pragma: no cover
            continue
        if not (converters := CONVERTERS.get(component_type)):
            continue
        for identifier, apply_converter in converters.items():
            log.debug(
                "apply_converter", component_type=component_type, identifier=identifier
            )
            apply_converter(component)


def apply_definition_conversions(configuration: JSONObject) -> None:
    for converter in DEFINITION_CONVERTERS:
        converter(configuration)


def _import_form_step_resources(
    data: str,
    uuid_mapping: dict[str, str],
    context: dict[str, Any],
) -> None:
    data = update_uuids(data, uuid_mapping)

    for entry in json.loads(data):
        entry: FormStepDataRepresentation = entry
        old_uuid: str | None = entry.get("uuid")
        form: Form = context["form"]

        deserialized = FormStepImportSerializer(data=entry, context=context)

        try:
            deserialized.is_valid(raise_exception=True)
            deserialized.save()

            # Once the form steps have been created, we create the component FormVariables
            # based on the form definition configurations.
            FormVariable.objects.create_for_form(form)

            if (
                old_uuid
                and deserialized.instance
                and hasattr(deserialized.instance, "uuid")
            ):
                uuid_mapping[old_uuid] = str(deserialized.instance.uuid)
        except ValidationError as e:
            raise e


def _import_form_variable_resources(
    data: str, uuid_mapping: dict[str, str], context: dict[str, Any]
) -> None:
    data = update_uuids(data, uuid_mapping)

    for entry in json.loads(data):
        entry: FormVariableDataRepresentation = entry
        form: Form = context["form"]

        if "service_fetch_configuration" in entry:
            # The transferring between systems case is very tricky
            # better not import these, we don't know where this came from.
            # services and ids may point to different things
            # in different OF instances.
            del entry["service_fetch_configuration"]

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
    data: str, uuid_mapping: dict[str, str], context: dict[str, Any]
) -> None:
    data = update_uuids(data, uuid_mapping)

    for entry in json.loads(data):
        entry: FormLogicDataRepresentation = entry
        old_uuid: str | None = entry.get("uuid")
        form: Form = context["form"]

        if "order" not in entry:
            entry["order"] = 0

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
            clear_old_service_fetch_config(deserialized.validated_data)

            deserialized.save()

            if (
                old_uuid
                and deserialized.instance
                and hasattr(deserialized.instance, "uuid")
            ):
                uuid_mapping[old_uuid] = str(deserialized.instance.uuid)
        except ValidationError as e:
            raise e


def clear_old_service_fetch_config(rule: dict[str, Any]) -> None:
    for action in rule.get("actions", []):
        if action["action"]["type"] != LogicActionTypes.fetch_from_service:
            continue

        if "value" not in action["action"] or action["action"]["value"] == "":
            continue

        # See comment above in `import_form_data` where we check if the variable has a
        # `service_fetch_configuration` attribute.
        # We can't reliably relate the service fetch configured to an existing configuration.
        # So we don't add any existing service fetch config to the variables
        action["action"]["value"] = ""


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
