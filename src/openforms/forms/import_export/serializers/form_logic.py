from ...api.serializers import FormLogicSerializer
from ...constants import LogicActionTypes
from ...disable_next_import_conversion import (
    add_form_step_uuid_to_disable_next_actions,
)
from ...models import FormLogic
from ..typing import FormLogicData
from .base import BaseExportSerializer, BaseImportSerializer


class FormLogicExportSerializer(
    FormLogicSerializer, BaseExportSerializer[FormLogic, FormLogicData]
):
    safe_export_fields = (
        "uuid",
        "url",
        "form",
        "json_logic_trigger",
        "description",
        "order",
        "actions",
        "is_advanced",
        "form_steps",
    )

    def remove_sensitive_content(
        self, instance: FormLogic, representation: FormLogicData
    ) -> FormLogicData:
        representation = super().remove_sensitive_content(instance, representation)
        form = instance.form

        # TODO move this to a registration backend options specific implementation
        # Preventing the removal or naming of options to break this functionality
        sensitive_variables = (
            registration.options["to_emails_from_variable"]
            for registration in form.registration_backends.all()
            if registration.backend == "email"
            and "to_emails_from_variable" in registration.options
        )

        for action in representation["actions"]:
            if (
                action["action"]["type"] == "variable"
                and action["variable"] in sensitive_variables
            ):
                action["action"]["value"] = ""

        return representation


class FormLogicImportSerializer(
    FormLogicSerializer, BaseImportSerializer[FormLogic, FormLogicData]
):
    def prepare_for_import(self, data: FormLogicData) -> None:
        self.clear_old_service_fetch_config(data)

    @staticmethod
    def clear_old_service_fetch_config(rule: FormLogicData) -> None:
        """
        Clear the old service fetch configuration from the rule.

        Original commit bbf49674274a92dd5004bc98cf0cf18c8e8f11d6
        """
        for _action in rule.get("actions", []):
            if (action := _action.get("action")) is None:
                continue

            # See the comment in FormVariableImportSerializer.prepare_for_import(), where
            # we check if the variable has a `service_fetch_configuration` attribute.
            # We can't reliably relate the service fetch configured to an existing
            # configuration. So we don't add any existing service fetch config to the
            # variables.
            if action.get("type") == LogicActionTypes.fetch_from_service:
                action["value"] = ""

    def apply_backwards_compatibility(self, data: FormLogicData) -> None:
        # Original commit 879751310d0bdf6a21bdd143b54f2a3d3f095023
        add_form_step_uuid_to_disable_next_actions(
            data,  # pyright: ignore[reportArgumentType]
            self.context["form_variables"].variables,
            self.context["form_steps"],
        )
