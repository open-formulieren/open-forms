from typing import Dict, List, NoReturn, Tuple

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from django_camunda.client import get_client
from django_camunda.models import CamundaConfig
from rest_framework import serializers

from openforms.submissions.models import Submission
from openforms.utils.mixins import JsonSchemaSerializerMixin

from ...base import BasePlugin
from ...exceptions import NoSubmissionReference, RegistrationFailed
from ...registry import register
from .checks import check_config


class CamundaOptionsSerializer(JsonSchemaSerializerMixin, serializers.Serializer):
    # TODO: get choices from django-camunda
    process_definition = serializers.CharField(
        required=True,
        help_text=_("The process definition for which to start a process instance."),
    )
    # TODO: get choices from django-camunda
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


@register("camunda")
class CamundaRegistration(BasePlugin):
    verbose_name = _("Camunda")
    configuration_options = CamundaOptionsSerializer

    def register_submission(
        self, submission: Submission, options: dict
    ) -> Dict[str, str]:
        camunda = get_client()
        # TODO: either use shared task or implement call ourself with the bare client
        raise NotImplementedError()

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
