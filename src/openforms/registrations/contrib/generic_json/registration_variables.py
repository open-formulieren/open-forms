from django.utils.translation import gettext_lazy as _

from openforms.plugins.registry import BaseRegistry
from openforms.submissions.models import Submission
from openforms.typing import JSONObject
from openforms.variables.base import BaseStaticVariable
from openforms.variables.constants import FormVariableDataTypes
from openforms.variables.static_variables.static_variables import Now

from .constants import PLUGIN_IDENTIFIER


class Registry(BaseRegistry[BaseStaticVariable]):
    """
    A registry for the Generic JSON registration variables.
    """

    module = PLUGIN_IDENTIFIER


register = Registry()
"""The Generic JSON registration variables registry."""


@register("public_reference")
class PublicReference(BaseStaticVariable):
    name = _("Public reference")
    data_type = FormVariableDataTypes.string

    def get_initial_value(self, submission: Submission | None = None) -> str:
        if submission is None:
            return ""
        return submission.public_registration_reference

    def as_json_schema(self) -> JSONObject:
        return {"title": "Public reference", "type": "string"}


@register("form_version")
class FormVersion(BaseStaticVariable):
    name = _("Form version")
    data_type = FormVariableDataTypes.string

    def get_initial_value(self, submission: Submission | None = None) -> str:
        if submission is None:
            return ""

        form_version = submission.form.formversion_set.order_by("created").last()
        return form_version.description if form_version else ""

    def as_json_schema(self) -> JSONObject:
        return {"title": "Form version", "type": "string"}


@register("registration_timestamp")
class RegistrationTimestamp(Now):
    name = _("Registration timestamp")

    def as_json_schema(self) -> JSONObject:
        return {
            "title": "Registration timestamp",
            "type": "string",
            "format": "date-time",
        }
