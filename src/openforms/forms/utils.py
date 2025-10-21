import json
import random
import string
import zipfile
from typing import Any
from uuid import uuid4

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.utils import timezone
from django.utils.translation import override

import structlog
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory

from openforms.formio.migration_converters import CONVERTERS, DEFINITION_CONVERTERS
from openforms.formio.utils import iter_components
from openforms.typing import JSONObject
from openforms.variables.constants import FormVariableSources

from .api.datastructures import FormVariableWrapper
from .api.serializers import (
    FormDefinitionSerializer,
    FormExportSerializer,
    FormLogicSerializer,
    FormSerializer,
    FormStepSerializer,
    FormVariableSerializer,
)
from .constants import EXPORT_META_KEY, LogicActionTypes
from .models import Form, FormDefinition, FormLogic, FormStep, FormVariable

logger = structlog.stdlib.get_logger(__name__)


IMPORT_ORDER = {
    "formDefinitions": FormDefinition,
    "forms": Form,
    "formSteps": FormStep,
    "formVariables": FormVariable,
    "formLogic": FormLogic,
}

SERIALIZERS = {
    "formDefinitions": FormDefinitionSerializer,
    "forms": FormSerializer,
    "formSteps": FormStepSerializer,
    "formLogic": FormLogicSerializer,
    "formVariables": FormVariableSerializer,
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


def form_to_json(form_id: int) -> dict:
    form = Form.objects.get(pk=form_id)

    # Ignore products in the export
    form.product = None

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

    forms = [FormExportSerializer(instance=form, context={"request": request}).data]
    form_definitions = FormDefinitionSerializer(
        instance=form_definitions,
        many=True,
        context={"request": request, "is_export": True},
    ).data
    form_steps = FormStepSerializer(
        instance=form_steps, many=True, context={"request": request}
    ).data
    form_logic = FormLogicSerializer(
        instance=form_logic, many=True, context={"request": request}
    ).data
    form_variables = FormVariableSerializer(
        instance=form_variables, many=True, context={"request": request}
    ).data

    resources = {
        "forms": to_json(forms),
        "formSteps": to_json(form_steps),
        "formDefinitions": to_json(form_definitions),
        "formLogic": to_json(form_logic),
        "formVariables": to_json(form_variables),
        EXPORT_META_KEY: to_json(
            {
                "of_release": settings.RELEASE,
                "of_git_sha": settings.GIT_SHA,
                "created": timezone.now().isoformat(),
            }
        ),
    }

    return resources


def export_form(form_id, archive_name=None, response=None):
    resources = form_to_json(form_id)

    outfile = response or archive_name
    with zipfile.ZipFile(outfile, "w") as zip_file:
        for name, data in resources.items():
            zip_file.writestr(f"{name}.json", data)
    return outfile


@transaction.atomic
def import_form(import_file, existing_form_instance=None) -> Form:
    import_data = {}
    with zipfile.ZipFile(import_file, "r") as zip_file:
        for resource in IMPORT_ORDER.keys():
            if f"{resource}.json" in zip_file.namelist():
                import_data[resource] = zip_file.read(f"{resource}.json").decode()

    return import_form_data(import_data, existing_form_instance)


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
) -> Form | None:
    uuid_mapping = {}

    request = _get_mock_request()

    created_form = None

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

    for resource in IMPORT_ORDER.keys():
        if resource not in import_data:
            continue

        data = import_data[resource]
        for old, new in uuid_mapping.items():
            data = data.replace(old, new)

        try:
            serializer = SERIALIZERS[resource]
        except KeyError:
            raise ValidationError(f"Unknown resource {resource}")

        for entry in json.loads(data):
            if old_uuid := entry.get("uuid"):
                entry["uuid"] = str(uuid4())

            if resource == "forms":
                # we can only extract a category UUID from the URL here, but that requires
                # an exact match and we currently don't provide import/export functionality
                # for categories. Relying on ID/Name is not much better than guesswork either,
                # so we always import forms with NO category at all to prevent import errors.
                # See #1774 for one such example of an error.
                entry["category"] = None
                # theme overrides cannot be imported, since the theme records/FKs have to
                # exist in the target environment. Importing/exporting themes is also not
                # possible at this time, so we reset the theme and admins need to update
                # the imported form.
                entry["theme"] = None

            if resource == "forms" and not existing_form_instance:
                entry["active"] = False

            serializer_kwargs = {
                "data": entry,
                "context": {
                    "request": request,
                    "form": created_form,
                    "is_import": True,
                },
            }

            if resource == "formDefinitions":
                existing_form_definition_instance = check_form_definition(
                    old_uuid,
                    entry,
                    for_existing_form=existing_form_instance is not None,
                )
                if existing_form_definition_instance:
                    # The form definition that is being imported is identical to
                    # the existing form definition with the same UUID, use
                    # existing instead of creating new definition. This may be
                    # both single and multiple use (is_reusable=True) form
                    # definitions, depending on whether it's for an existing form or not.
                    # Note that the mapping will include the same UUID  here often,
                    # which is okay for find-and-replace.
                    serializer_kwargs["instance"] = existing_form_definition_instance
                    entry["uuid"] = old_uuid
                    uuid_mapping[old_uuid] = old_uuid

            if resource == "forms" and existing_form_instance:
                serializer_kwargs["instance"] = existing_form_instance

            if resource in ("formVariables", "formLogic"):
                # by now, the form resource has been created (or it was an existing one)
                _form = existing_form_instance or created_form
                serializer_kwargs["context"].update(
                    {
                        "forms": {str(_form.uuid): _form},
                        "form_definitions": {
                            str(fd.uuid): fd
                            for fd in FormDefinition.objects.filter(
                                formstep__form=_form
                            )
                        },
                    }
                )
                if "service_fetch_configuration" in entry:
                    # The transferring between systems case is very tricky
                    # better not import these, we don't know where this came from.
                    # services and ids may point to different things
                    # in different OF instances.
                    del entry["service_fetch_configuration"]

            if resource == "formLogic":
                # by now, the form resource has been created (or it was an existing one)
                _form = existing_form_instance or created_form
                serializer_kwargs["context"].update(
                    {
                        "form_variables": FormVariableWrapper(_form),
                        "form_steps": {
                            form_step.uuid: form_step
                            for form_step in _form.formstep_set.all()
                        },
                    }
                )

            deserialized = serializer(**serializer_kwargs)

            if resource == "formLogic" and "order" not in entry:
                entry["order"] = 0

            try:
                is_create = (
                    deserialized.instance is None or not deserialized.instance.pk
                )
                deserialized.is_valid(raise_exception=True)

                if resource == "formDefinitions":
                    apply_component_conversions(
                        deserialized.validated_data["configuration"]
                    )

                    apply_definition_conversions(
                        deserialized.validated_data["configuration"]
                    )

                if resource == "formLogic":
                    clear_old_service_fetch_config(deserialized.validated_data)

                instance = deserialized.save()
                if resource == "forms":
                    created_form = deserialized.instance
                if resource == "formSteps":
                    # Once the form steps have been created, we create the component FormVariables
                    # based on the form definition configurations.
                    FormVariable.objects.create_for_form(created_form)
                if resource == "formDefinitions" and is_create:
                    uuid_mapping[old_uuid] = str(instance.uuid)

                # The FormSerializer/FormStepSerializer/FormLogicSerializer have the uuid as a read only field.
                # So the mapping between the old uuid and the new needs to be done after the instance is saved.
                if hasattr(deserialized.instance, "uuid") and "uuid" in entry:
                    uuid_mapping[old_uuid] = str(deserialized.instance.uuid)
            except ValidationError as e:
                if (
                    resource == "forms"
                    and "slug" in e.detail
                    and e.detail["slug"][0].code == "unique"
                ):
                    entry["slug"] = (
                        f"{entry['slug']}-{''.join(random.choices(string.hexdigits, k=6))}"
                    )

                    deserialized = serializer(
                        data=entry,
                        context={
                            "request": request,
                            "form": created_form,
                            "is_import": True,
                        },
                        instance=existing_form_instance,
                    )
                    deserialized.is_valid(raise_exception=True)
                    deserialized.save()
                    created_form = deserialized.instance
                    uuid_mapping[old_uuid] = str(deserialized.instance.uuid)

                else:
                    raise e

    return created_form


def apply_component_conversions(configuration):
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


def clear_old_service_fetch_config(rule: dict) -> None:
    for action in rule["actions"]:
        if action["action"]["type"] != LogicActionTypes.fetch_from_service:
            continue

        if "value" not in action["action"] or action["action"]["value"] == "":
            continue

        # See comment above in `import_form_data` where we check if the variable has a
        # `service_fetch_configuration` attribute.
        # We can't reliably relate the service fetch configured to an existing configuration.
        # So we don't add any existing service fetch config to the variables
        action["action"]["value"] = ""
