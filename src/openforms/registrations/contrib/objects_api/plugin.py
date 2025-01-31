from __future__ import annotations

import logging
from functools import partial
from typing import TYPE_CHECKING, Any, override

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from openforms.config.data import Action
from openforms.contrib.objects_api.checks import check_config
from openforms.contrib.objects_api.clients import (
    get_objects_client,
    get_objecttypes_client,
)
from openforms.contrib.objects_api.ownership_validation import validate_object_ownership
from openforms.registrations.utils import execute_unless_result_exists
from openforms.variables.service import get_static_variables

from ...base import BasePlugin
from ...registry import register
from .config import ObjectsAPIOptionsSerializer
from .models import ObjectsAPIConfig
from .registration_variables import register as variables_registry
from .submission_registration import HANDLER_MAPPING
from .typing import RegistrationOptions
from .utils import apply_defaults_to

if TYPE_CHECKING:
    from openforms.forms.models import FormVariable
    from openforms.submissions.models import Submission


PLUGIN_IDENTIFIER = "objects_api"

logger = logging.getLogger(__name__)


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

        with get_objects_client(api_group) as client:
            validate_object_ownership(submission, client, auth_attribute_path, self)

    @override
    def register_submission(
        self, submission: Submission, options: RegistrationOptions
    ) -> dict[str, Any]:
        """Register a submission using the Objects API backend.

        Depending on the options version (legacy or mapped variables), the payload
        will be created differently. The actual logic lives in the ``submission_registration`` submodule.
        """

        self.set_defaults(options)

        handler = HANDLER_MAPPING[options["version"]]

        handler.save_registration_data(submission, options)

        record_data = handler.get_record_data(
            submission=submission,
            options=options,
        )

        with get_objecttypes_client(options["objects_api_group"]) as objecttypes_client:
            objecttype = objecttypes_client.get_objecttype(options["objecttype"])
            objecttype_url = objecttype["url"]

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
            response = execute_unless_result_exists(
                update_or_create,
                submission,
                "intermediate.objects_api_object",
            )

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
