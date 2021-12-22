import logging
from typing import Any, Dict, List, NoReturn, Optional, Tuple

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import requests
from django_camunda.api import get_process_definitions
from django_camunda.models import CamundaConfig
from django_camunda.tasks import start_process
from django_camunda.types import ProcessVariables
from django_camunda.utils import serialize_variable
from rest_framework import serializers

from openforms.submissions.models import Submission
from openforms.utils.mixins import JsonSchemaSerializerMixin

from ...base import BasePlugin
from ...exceptions import NoSubmissionReference, RegistrationFailed
from ...registry import register
from .checks import check_config

logger = logging.getLogger(__name__)


# temporary to debug the demo process instances from Camunda
VARS = {
    "amount": 10,
    "invoiceCategory": "Misc",
}


class CamundaOptionsSerializer(JsonSchemaSerializerMixin, serializers.Serializer):
    process_definition = serializers.CharField(
        required=True,
        help_text=_("The process definition for which to start a process instance."),
    )
    process_definition_version = serializers.IntegerField(
        required=False,
        help_text=_(
            "Which version of the process definition to start. The latest version is "
            "used if not specified."
        ),
        allow_null=True,
    )
    # TODO: derived_variables, variables_to_include (from component keys) - might have
    # to be done in react alltogether


def serialize_variables(variables: Optional[Dict[str, Any]]) -> ProcessVariables:
    if variables is None:
        return {}
    return {key: serialize_variable(value) for key, value in variables.items()}


@register("camunda")
class CamundaRegistration(BasePlugin):
    verbose_name = _("Camunda")
    configuration_options = CamundaOptionsSerializer

    def register_submission(
        self, submission: Submission, options: dict
    ) -> Dict[str, str]:
        process_definition = options["process_definition"]
        version = options["process_definition_version"]

        process_options = {
            "process_key": process_definition,
            "variables": serialize_variables(VARS),
        }

        # if we have a specific version, we need to get the actual process id
        if version is not None:
            process_definitions = get_process_definitions()
            needle = next(
                (
                    definition
                    for definition in process_definitions
                    if definition.key == process_definition
                    and definition.version == version
                ),
                None,
            )
            if needle is None:
                raise RegistrationFailed(
                    "Could not start instance for process definition with key "
                    f"'{process_definition}' and version '{version}'."
                )
            process_options["process_id"] = needle.id
            del process_options["process_key"]

        # celery task, but we call it synchronously since this codepath already runs
        # outside of a request-response cycle (celery or management command)
        try:
            meta_information = start_process(**process_options)
        except requests.RequestException as exc:
            if (response := exc.response) is not None:
                camunda_response = response.json()

                if response.status_code >= 500:
                    logger.exception(
                        "Camunda error on process start: %r", camunda_response
                    )
                    raise RegistrationFailed(
                        f"Failed starting the process instance: {camunda_response}"
                    ) from exc

                elif response.status_code >= 400:
                    logger.error(
                        "Invalid request made to Camunda to start a process instance: %r",
                        camunda_response,
                    )
                    raise RegistrationFailed(
                        f"Failed starting the process instance: {camunda_response}"
                    ) from exc
            raise

        return {
            "instance": {
                "id": meta_information["instance_id"],
                "url": meta_information["instance_url"],
            }
        }

    def get_reference_from_result(self, result: Dict[str, str]) -> NoReturn:
        """
        Extract the public submission reference from the result data.

        We never return, as the Camunda API response does not contain anything useful
        and readable for the end-user and we cannot make assumptions about the process
        model. The instance ID is a UUID, which is not suitable for end users.
        """
        raise NoSubmissionReference("Deferred to Open Forms itself")

    def update_payment_status(self, submission: "Submission", options: dict):
        # TODO: we could ask for a BPMN message to be specified so we can signal the
        # process instance? This needs to be documented properly for the modellers
        # though.
        raise NotImplementedError()

    def check_config(self):
        check_config()

    def get_config_actions(self) -> List[Tuple[str, str]]:
        return [
            (
                _("Configuration"),
                reverse(
                    "admin:django_camunda_camundaconfig_change",
                    args=(CamundaConfig.singleton_instance_id,),
                ),
            ),
        ]
