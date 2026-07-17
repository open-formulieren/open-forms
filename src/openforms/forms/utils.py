import json
import zipfile
from collections.abc import Callable, Collection
from dataclasses import dataclass
from typing import Any, Literal, Required, TypedDict

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.utils import timezone
from django.utils.translation import override

import structlog
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from openforms.import_export.serializers import (
    BaseImportSerializer,
    FormDefinitionExportSerializer,
    FormDefinitionImportSerializer,
    FormExportSerializer,
    FormImportSerializer,
    FormLogicExportSerializer,
    FormLogicImportSerializer,
    FormStepExportSerializer,
    FormStepImportSerializer,
    FormVariableExportSerializer,
    FormVariableImportSerializer,
)
from openforms.import_export.typing import (
    FormExportOptions,
    FormImportOptions,
)
from openforms.import_export.utils import (
    get_additional_form_configuration_data,
    import_additional_form_configuration_data,
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
from openforms.variables.constants import FormVariableSources

from .api.datastructures import FormVariableWrapper
from .constants import EXPORT_META_KEY
from .models import Form, FormDefinition, FormLogic, FormStep

logger = structlog.stdlib.get_logger(__name__)


IMPORT_ORDER = (
    "product",
    "theme",
    "category",
    "wmsTileLayers",
    "wmtsTileLayers",
    "yiviAttributeGroups",
    "formDefinitions",
    "forms",
    "formSteps",
    "formVariables",
    "formLogic",
)


@dataclass(frozen=True)
class ImportSerializerConfig:
    serializer: type[BaseImportSerializer]
    serializer_kwargs: Callable[
        [dict[str, Any], Form | None, FormImportOptions, Request],
        [dict[str, Any]],
    ]
    type: Literal["form", "formDefinition", "formStep", "formVariable", "formLogic"]


def get_serializer_kwargs(
    data: dict[str, Any],
    form: Form | None,
    import_options: FormImportOptions,
    request: Request,
) -> dict[str, Any]:
    return {
        "data": data,
        "context": {
            "request": request,
            "form": form,
            "is_import": True,
            "import_options": import_options,
        },
    }


def get_form_variable_serializer_kwargs(
    data: dict[str, Any],
    form: Form | None,
    import_options: FormImportOptions,
    request: Request,
) -> dict[str, Any]:
    kwargs = get_serializer_kwargs(data, form, import_options, request)
    kwargs["context"] = {
        **kwargs["context"],
        "forms": ({str(form.uuid): form}),
        "form_definitions": {
            str(fd.uuid): fd
            for fd in FormDefinition.objects.filter(formstep__form=form)
        },
    }
    return kwargs


def get_form_logic_serializer_kwargs(
    data: dict[str, Any],
    form: Form | None,
    import_options: FormImportOptions,
    request: Request,
) -> dict[str, Any]:
    kwargs = get_serializer_kwargs(data, form, import_options, request)
    kwargs["context"] = {
        **kwargs["context"],
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
    return kwargs


"""
Serializer configuration for the import process. The key is the name of the resource
in the import file, and the value is the serializer class and serializer kwargs.
"""
IMPORT_SERIALIZER_CONFIGS: dict[str, ImportSerializerConfig] = {
    "forms": ImportSerializerConfig(
        serializer=FormImportSerializer,
        serializer_kwargs=get_serializer_kwargs,
        type="form",
    ),
    "formDefinitions": ImportSerializerConfig(
        serializer=FormDefinitionImportSerializer,
        serializer_kwargs=get_serializer_kwargs,
        type="formDefinition",
    ),
    "formSteps": ImportSerializerConfig(
        serializer=FormStepImportSerializer,
        serializer_kwargs=get_serializer_kwargs,
        type="formStep",
    ),
    "formVariables": ImportSerializerConfig(
        serializer=FormVariableImportSerializer,
        serializer_kwargs=get_form_variable_serializer_kwargs,
        type="formVariable",
    ),
    "formLogic": ImportSerializerConfig(
        serializer=FormLogicImportSerializer,
        serializer_kwargs=get_form_logic_serializer_kwargs,
        type="formLogic",
    ),
}


def _get_mock_request():
    factory = APIRequestFactory()
    first_allowed_host = (
        settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else "testserver"
    )
    server_name = first_allowed_host if first_allowed_host != "*" else "testserver"
    request = factory.get("/", SERVER_NAME=server_name)
    request.is_mock_request = True  # pyright: ignore[reportAttributeAccessIssue]
    return request


def to_json(obj: Any):
    return json.dumps(obj, cls=DjangoJSONEncoder)


def form_to_json(form_id: int, export_options: FormExportOptions = None) -> dict:
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


def export_form(
    form_id, archive_name=None, response=None, export_options: FormExportOptions = None
):
    resources = form_to_json(form_id, export_options)

    outfile = response or archive_name
    with zipfile.ZipFile(outfile, "w") as zip_file:
        for name, data in resources.items():
            zip_file.writestr(f"{name}.json", data)
    return outfile


@transaction.atomic
def import_form(
    import_file, existing_form_instance=None, import_options: FormImportOptions = None
) -> Form | None:
    import_data = {}
    with zipfile.ZipFile(import_file, "r") as zip_file:
        for resource in IMPORT_ORDER:
            if f"{resource}.json" in zip_file.namelist():
                import_data[resource] = zip_file.read(f"{resource}.json").decode()

    return import_form_data(import_data, existing_form_instance, import_options)


def check_form_definition(uuid: str, attrs: dict[str, Any], for_existing_form: bool):
    """
    Import a form definition with a given UUID.

    If the UUID is already present, check if the configuration is the same or not. If
    it's the same, the existing record is updated, otherwise a new form definition is
    created.
    """
    existing = FormDefinition.objects.filter(uuid=uuid).first()
    # no existing record -> let the import flow create one
    if existing is None:
        return None

    # if there is an existing form definition, but it's not being related to the same
    # form, then we need to create a copy
    # if new form, existing is used, existing is not reusable
    if not for_existing_form and existing.used_in.exists() and not existing.is_reusable:
        return None

    # Compare hashes to check if form fields configuration changed or not. If there are
    # changes, the import data should be created as a new record.
    existing_fd_hash = existing.get_hash()
    imported_fd_hash = FormDefinition(configuration=attrs["configuration"]).get_hash()
    if existing_fd_hash == imported_fd_hash:
        return existing
    return None


@transaction.atomic
@override(language=settings.LANGUAGE_CODE)
def import_form_data(
    import_data: dict,
    existing_form_instance: Form | None = None,
    import_options: FormImportOptions = None,
) -> Form | None:
    uuid_mapping = {}

    request = _get_mock_request()
    created_form = None
    form_definitions = []

    # Import additional data
    import_additional_form_configuration_data(
        resources=import_data, import_options=import_options, uuid_mapping=uuid_mapping
    )

    for resource in IMPORT_SERIALIZER_CONFIGS:
        if resource not in import_data:
            continue

        data = import_data[resource]
        for old, new in uuid_mapping.items():
            data = data.replace(old, new)

        serializer_config = IMPORT_SERIALIZER_CONFIGS[resource]
        for entry in json.loads(data):
            old_uuid = entry.get("uuid")

            deserialized = serializer_config.serializer(
                **serializer_config.serializer_kwargs(
                    entry, created_form, import_options, request
                )
            )

            try:
                deserialized.is_valid(raise_exception=True)

                instance = deserialized.save()
                if serializer_config.type == "form" and created_form is None:
                    created_form = instance
                if serializer_config.type == "formDefinition":
                    form_definitions.append(instance)

                if hasattr(deserialized.instance, "uuid") and "uuid" in entry:
                    uuid_mapping[old_uuid] = str(deserialized.instance.uuid)
            except ValidationError as e:
                raise e

        if serializer_config.type == "formDefinition":
            move_file_registration_options(created_form, form_definitions)

    return created_form


def remove_key_from_dict(dictionary, key):
    for dict_key in list(dictionary.keys()):
        if key == dict_key:
            del dictionary[key]
        elif isinstance(dictionary[dict_key], dict):
            remove_key_from_dict(dictionary[dict_key], key)
        elif isinstance(dictionary[dict_key], list):
            for value in dictionary[dict_key]:
                if isinstance(value, dict):
                    remove_key_from_dict(value, key)


class FileComponentOptions(TypedDict, total=False):
    key: Required[str]
    document_type_description: str
    organization_rsin: str
    confidentiality_level: str
    title: str


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
