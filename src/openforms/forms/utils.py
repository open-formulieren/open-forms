import json
import random
import string
import zipfile
from typing import Dict, List, Optional
from uuid import uuid4

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone

from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory

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
from .api.serializers.logic.action_serializers import LogicComponentActionSerializer
from .constants import EXPORT_META_KEY
from .models import Form, FormDefinition, FormLogic, FormStep, FormVariable

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
    request.is_mock_request = True
    return request


def form_to_json(form_id: int) -> dict:
    form = Form.objects.get(pk=form_id)

    # Ignore products in the export
    form.product = None

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
        context={"request": request},
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
        "forms": json.dumps(forms),
        "formSteps": json.dumps(form_steps),
        "formDefinitions": json.dumps(form_definitions),
        "formLogic": json.dumps(form_logic),
        "formVariables": json.dumps(form_variables),
        EXPORT_META_KEY: json.dumps(
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
def import_form(import_file, existing_form_instance=None):
    import_data = {}
    with zipfile.ZipFile(import_file, "r") as zip_file:
        for resource, model in IMPORT_ORDER.items():
            if f"{resource}.json" in zip_file.namelist():
                import_data[resource] = zip_file.read(f"{resource}.json").decode()

    return import_form_data(import_data, existing_form_instance)


@transaction.atomic
def import_form_data(
    import_data: dict, existing_form_instance: Form = None
) -> List[FormDefinition]:
    uuid_mapping = {}

    request = _get_mock_request()
    created_form_definitions = []

    created_form = None

    # when restoring a previous version, delete the current form configuration,
    # it will be replaced with the import data.
    if existing_form_instance:
        FormStep.objects.filter(form=existing_form_instance).delete()
        FormLogic.objects.filter(form=existing_form_instance).delete()
        FormVariable.objects.filter(form=existing_form_instance).delete()

    for resource, model in IMPORT_ORDER.items():
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
            if "uuid" in entry:
                old_uuid = entry["uuid"]
                entry["uuid"] = str(uuid4())

            if resource == "forms":
                # we can only extract a category UUID from the URL here, but that requires
                # an exact match and we currently don't provide import/export functionality
                # for categories. Relying on ID/Name is not much better than guesswork either,
                # so we always import forms with NO category at all to prevent import errors.
                # See #1774 for one such example of an error.
                entry["category"] = None

            if resource == "forms" and not existing_form_instance:
                entry["active"] = False

            serializer_kwargs = {
                "data": entry,
                "context": {"request": request, "form": created_form},
            }

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

            if resource == "formLogic":
                # by now, the form resource has been created (or it was an existing one)
                _form = existing_form_instance or created_form
                serializer_kwargs["context"].update(
                    {
                        "form_variables": FormVariableWrapper(_form),
                    }
                )

            deserialized = serializer(**serializer_kwargs)

            if resource == "formLogic" and "order" not in entry:
                entry["order"] = 0

            try:
                deserialized.is_valid(raise_exception=True)
                deserialized.save()
                if resource == "forms":
                    created_form = deserialized.instance
                if resource == "formSteps":
                    # Once the form steps have been created, we create the component FormVariables
                    # based on the form definition configurations.
                    FormVariable.objects.create_for_form(created_form)

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
                    entry[
                        "slug"
                    ] = f'{entry["slug"]}-{"".join(random.choices(string.hexdigits, k=6))}'

                    deserialized = serializer(
                        data=entry,
                        context={"request": request, "form": created_form},
                        instance=existing_form_instance,
                    )
                    deserialized.is_valid(raise_exception=True)
                    deserialized.save()
                    created_form = deserialized.instance
                    uuid_mapping[old_uuid] = str(deserialized.instance.uuid)

                elif (
                    resource == "formDefinitions"
                    and "slug" in e.detail
                    and e.detail["slug"][0].code == "unique"
                ):
                    existing_fd = FormDefinition.objects.get(slug=entry["slug"])
                    existing_fd_hash = existing_fd.get_hash()
                    imported_fd_hash = FormDefinition(
                        configuration=entry["configuration"]
                    ).get_hash()

                    if existing_fd_hash == imported_fd_hash:
                        # The form definition that is being imported is identical to
                        # the existing form definition # with the same slug, use
                        # existing instead # of creating new definition. This may be
                        # both single and multiple use (is_reusable=True) form
                        # definitions. Note that the mapping will include the same UUID
                        # here often, which is okay for find-and-replace.
                        uuid_mapping[old_uuid] = str(existing_fd.uuid)
                    else:
                        # The imported form definition configuration
                        # is different, create a new form definition
                        # TODO: this would still cause unique slug constraint errors, no?
                        entry.pop("url")
                        entry.pop("uuid")
                        new_fd = FormDefinition(**entry)
                        new_fd.save()
                        uuid_mapping[old_uuid] = str(new_fd.uuid)

                        created_form_definitions.append(new_fd.slug)
                else:
                    raise e
    return created_form_definitions


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


def parse_trigger(
    trigger_info: JSONObject,
    configuration_wrapper: Optional[Dict[str, JSONObject]] = None,
) -> Optional[JSONObject]:
    trigger_type = trigger_info["type"]
    trigger = trigger_info[trigger_type]

    if trigger_type not in ["json", "simple"]:
        return

    if trigger_type == "simple":
        trigger_component_key = trigger.get("when")
        compare_value = trigger.get("eq")

        if (
            configuration_wrapper
            and configuration_wrapper[trigger_component_key]["type"] == "selectboxes"
        ):
            return {"==": [{"var": f"{trigger_component_key}.{compare_value}"}, True]}

        return {"==": [{"var": trigger_component_key}, compare_value]}

    if trigger_type == "json":
        return trigger


def parse_actions(
    actions: List[JSONObject], component_key: str = None
) -> List[JSONObject]:
    """Parse Formio logic actions and convert them to backend actions.

    We only support the "property" action among the ones offered by Formio advanced logic.
    We also only support the properties hidden, disabled and required.

    The 'required' property is special, in Formio it's:

    .. code-block:: json

        {
            "property": {
               "value": "validate.required",
               "type": "boolean"
             },
             "state": true
        }

    While we use:

    .. code-block:: json

        {
            "property": {
               "value": "validate",
               "type": "json"
             },
             "state": {"required": True}
        }

    """
    parsed_actions = []
    for action in actions:
        if action["type"] != "property":
            continue

        if action["property"]["value"] not in [
            "hidden",
            "disabled",
            "validate.required",
        ]:
            continue

        if action["property"]["value"] == "validate.required":
            action.update(
                {
                    "property": {"value": "validate", "type": "json"},
                    "state": {"required": action["state"]},
                }
            )
        else:
            # Formio uses "boolean"
            action["property"]["type"] = "bool"

        parsed_actions.append({"action": action, "component": component_key})

    return parsed_actions


def advanced_formio_logic_to_backend_logic(
    form_definition: "FormDefinition", apps
) -> None:
    FormStep = apps.get_model("forms", "FormStep")
    Form = apps.get_model("forms", "Form")
    FormLogic = apps.get_model("forms", "FormLogic")

    form_steps = FormStep.objects.filter(form_definition__pk=form_definition.pk)
    forms = Form.objects.filter(pk__in=form_steps.values_list("form", flat=True))

    configuration_wrapper = {
        component["key"]: component
        for component in iter_components(form_definition.configuration, recursive=True)
    }

    logic_rules_to_create = []
    for key, component in configuration_wrapper.items():
        if "logic" not in component or not len(component["logic"]):
            continue

        component_key = component["key"]
        for component_logic_rule in component["logic"]:
            parsed_trigger = parse_trigger(
                component_logic_rule["trigger"], configuration_wrapper
            )
            if not parsed_trigger:
                continue

            parsed_actions = parse_actions(
                component_logic_rule["actions"], component_key
            )
            if not parsed_actions:
                continue

            for form in forms:
                order = (
                    getattr(
                        form.formlogic_set.all().order_by("order").last(), "order", 0
                    )
                    + 1
                )
                logic_rules_to_create.append(
                    FormLogic(
                        form=form,
                        json_logic_trigger=parsed_trigger,
                        actions=parsed_actions,
                        order=order,
                    )
                )

        component["logic"] = []

    if logic_rules_to_create:
        form_definition.save()
        FormLogic.objects.bulk_create(logic_rules_to_create)


def fix_broken_rules(rules: models.QuerySet) -> None:
    fixed_rules = []
    for rule in rules:
        serializer = LogicComponentActionSerializer(data=rule.actions, many=True)
        is_valid = serializer.is_valid()
        if not is_valid:
            fixed_actions = []
            for index, action in enumerate(rule.actions):
                if (
                    "action" not in serializer.errors[index]
                    or "property" not in action
                    or "state" not in action
                ):
                    fixed_actions.append(action)
                    continue

                if action["property"].get("type") == "boolean":
                    action["property"]["type"] = "bool"

                # The serializer does not accept an empty component value, this will be flagged as an unknown component
                # next time the user tries to save the form in the form Editor.
                fixed_actions.append({"action": action, "component": "UNKNOWN"})

            rule.actions = fixed_actions
            fixed_rules.append(rule)

    if fixed_rules:
        FormLogic.objects.bulk_update(fixed_rules, fields=["actions"])
