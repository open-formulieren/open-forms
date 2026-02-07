from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Any, override

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import structlog

from openforms.config.data import Action
from openforms.contrib.objects_api.checks import check_config
from openforms.contrib.objects_api.clients import (
    get_objects_client,
    get_objecttypes_client,
)
from openforms.contrib.objects_api.ownership_validation import validate_object_ownership
from openforms.formio.typing import Component, EditGridComponent
from openforms.registrations.utils import execute_unless_result_exists
from openforms.typing import JSONObject
from openforms.variables.service import get_static_variables

from ...base import BasePlugin
from ...registry import register
from .config import ObjectsAPIOptionsSerializer
from .constants import PLUGIN_IDENTIFIER
from .models import ObjectsAPIConfig
from .registration_variables import register as variables_registry
from .submission_registration import HANDLER_MAPPING
from .typing import RegistrationOptions
from .utils import apply_defaults_to

if TYPE_CHECKING:
    from openforms.forms.models import FormVariable
    from openforms.submissions.models import Submission


logger = structlog.stdlib.get_logger(__name__)


@register(PLUGIN_IDENTIFIER)
class ObjectsAPIRegistration(BasePlugin[RegistrationOptions]):
    verbose_name = _("Objects API registration")
    configuration_options = ObjectsAPIOptionsSerializer

    @staticmethod
    def set_defaults(options: RegistrationOptions) -> None:
        config_group = options["objects_api_group"]
        apply_defaults_to(config_group, options)

        if options["version"] == 1:
            global_config = ObjectsAPIConfig.get_solo()
            if not options.get("content_json", "").strip():
                options["content_json"] = global_config.content_json
            if not options.get("payment_status_update_json", "").strip():
                options["payment_status_update_json"] = (
                    global_config.payment_status_update_json
                )
            options.setdefault(
                "productaanvraag_type", global_config.productaanvraag_type
            )

    @override
    def verify_initial_data_ownership(
        self, submission: Submission, options: RegistrationOptions
    ) -> None:
        # Object's ownership validation makes sense if we want to update an object
        if not options["update_existing_object"]:
            return

        assert submission.initial_data_reference
        api_group = options["objects_api_group"]
        assert api_group, "Can't do anything useful without an API group"

        auth_attribute_path = options["auth_attribute_path"]
        assert auth_attribute_path, "Auth attribute path may not be empty"

        with (
            get_objects_client(api_group) as client,
            structlog.contextvars.bound_contextvars(plugin=self),
        ):
            validate_object_ownership(submission, client, auth_attribute_path)

    @override
    def register_submission(
        self, submission: Submission, options: RegistrationOptions
    ) -> dict[str, Any]:
        """Register a submission using the Objects API backend.

        Depending on the options version (legacy or mapped variables), the payload
        will be created differently. The actual logic lives in the ``submission_registration`` submodule.
        """

        self.set_defaults(options)
        log = logger.bind(
            handler_version=options["version"],
            public_reference=submission.public_registration_reference,
        )

        handler = HANDLER_MAPPING[options["version"]]

        handler.save_registration_data(submission, options)
        log.debug("registration_data_saved")

        record_data = handler.get_record_data(
            submission=submission,
            options=options,
        )

        with get_objecttypes_client(options["objects_api_group"]) as objecttypes_client:
            objecttype = objecttypes_client.get_objecttype(options["objecttype"])
            objecttype_url = objecttype["url"]
            log.info("objecttype_resolved", objecttype_url=objecttype_url)

        with get_objects_client(options["objects_api_group"]) as objects_client:
            # update or create the object
            is_update = (
                options["update_existing_object"] and submission.initial_data_reference
            )
            update_or_create = (
                partial(
                    objects_client.update_object,
                    object_uuid=submission.initial_data_reference,
                    record_data=record_data,
                )
                if is_update
                else partial(
                    objects_client.create_object,
                    objecttype_url=objecttype_url,
                    record_data=record_data,
                )
            )
            log.info(
                "updating_object" if is_update else "creating_object",
                object_id=submission.initial_data_reference if is_update else None,
            )
            response = execute_unless_result_exists(
                update_or_create,
                submission,
                "intermediate.objects_api_object",
            )
            log.info("submission_registered", object_uuid=response["uuid"])

        return response

    @override
    def check_config(self):
        check_config()

    @override
    def get_config_actions(self) -> list[Action]:
        return [
            (
                _("Manage API groups"),
                reverse("admin:objects_api_objectsapigroupconfig_changelist"),
            ),
            (
                _("Defaults configuration"),
                reverse(
                    "admin:registrations_objects_api_objectsapiconfig_change",
                    args=(ObjectsAPIConfig.singleton_instance_id,),
                ),
            ),
        ]

    @override
    def get_custom_templatetags_libraries(self) -> list[str]:
        prefix = "openforms.registrations.contrib.objects_api.templatetags.registrations.contrib"
        return [
            f"{prefix}.objects_api.json_tags",
        ]

    @override
    def update_payment_status(
        self, submission: Submission, options: RegistrationOptions
    ) -> dict[str, Any] | None:
        self.set_defaults(options)

        handler = HANDLER_MAPPING[options["version"]]
        updated_record_data = handler.get_update_payment_status_data(
            submission, options
        )

        if updated_record_data is None:
            return

        with get_objecttypes_client(options["objects_api_group"]) as objecttypes_client:
            objecttype = objecttypes_client.get_objecttype(options["objecttype"])
            objecttype_url = objecttype["url"]

        assert submission.registration_result is not None
        object_url = submission.registration_result["url"]
        with get_objects_client(options["objects_api_group"]) as objects_client:
            response = objects_client.patch(
                url=object_url,
                json={
                    "type": objecttype_url,
                    "record": updated_record_data,
                },
                headers={"Content-Crs": "EPSG:4326"},
            )
            response.raise_for_status()
            return response.json()

    @override
    def get_variables(self) -> list[FormVariable]:
        return get_static_variables(variables_registry=variables_registry)

    @staticmethod
    def allows_json_schema_generation(options: RegistrationOptions) -> bool:
        return options["version"] == 2

    def process_variable_schema(
        self, component: Component, schema: JSONObject, options: RegistrationOptions
    ):
        """Process a variable schema for the Objects API format.

        The following components need extra attention:
        - File components: we send a url or list of urls, instead of the output from the
          serializer.
        - Selectboxes components: the selected options could be transformed to a list.
        - Edit grid components: layout component with other components as children,
          which (potentially) need to be processed.

        :param component: Component
        :param schema: JSON schema.
        :param options: Backend options, needed for the transform-to-list option of
          selectboxes components.
        """
        assert options["version"] == 2
        transform_to_list = options["transform_to_list"]

        match component:
            case {"type": "addressNL"}:
                # In the Objects API there exists an option to map the individual fields
                # of the addressNL component. Unlike the transform-to-list option for
                # selectboxes components, this is not a checkbox, but rather a mapping from
                # a variable to a JSON schema property. This creates the problem that this
                # option cannot be set without the 'contract' already being present in the
                # Objecttypes API, and essentially means we are trying to fetch contract
                # options (whether to map the complete object or individual subfields) from
                # the contract we are currently generating. Therefore, we just default to
                # the schema of a complete addressNL object.
                pass

            case {"type": "file", "multiple": True}:
                # If multiple is true, the value will be an empty list if no attachments are
                # uploaded, or a list of urls when one or more attachments are uploaded.
                schema["items"] = {"type": "string", "format": "uri"}

            case {"type": "file"}:  # multiple is False or missing
                # If multiple is false, the value will be an empty string if no attachment
                # is uploaded, or a single url if one attachment is uploaded.
                schema["type"] = "string"
                schema["oneOf"] = [{"format": "uri"}, {"pattern": "^$"}]
                schema.pop("items")

            case {"type": "selectboxes"} if component["key"] in transform_to_list:
                assert isinstance(schema["properties"], dict)

                # If the component is transformed to a list, we need to adjust the schema
                # accordingly
                schema["type"] = "array"
                schema["items"] = {"type": "string", "enum": list(schema["properties"])}

                for prop in ("properties", "required", "additionalProperties"):
                    schema.pop(prop)

            case {"type": "editgrid"}:
                from typing import cast  # noqa: TID251

                assert isinstance(schema["items"], dict)
                _properties = schema["items"]["properties"]
                assert isinstance(_properties, dict)

                component = cast(EditGridComponent, component)
                for child_component in component["components"]:
                    child_key = child_component["key"]
                    child_schema = _properties[child_key]
                    assert isinstance(child_schema, dict)
                    self.process_variable_schema(
                        child_component,
                        child_schema,
                        options,
                    )
            case _:
                pass
