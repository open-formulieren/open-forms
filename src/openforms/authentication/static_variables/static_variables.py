from typing import TYPE_CHECKING, Optional

from django.utils.translation import gettext_lazy as _

from openforms.authentication.constants import AuthAttribute
from openforms.forms.constants import FormVariableDataTypes
from openforms.variables.base import BaseStaticVariable
from openforms.variables.registry import static_variables_register

if TYPE_CHECKING:  # pragma: nocover
    from openforms.authentication.utils import FormAuth
    from openforms.submissions.models import Submission


@static_variables_register("auth_identifier")
class AuthIdentifier(BaseStaticVariable):
    name = _("Authentication identifier")
    data_type = FormVariableDataTypes.object

    def get_initial_value(
        self, submission: Optional["Submission"]
    ) -> Optional["FormAuth"]:
        if not submission or not hasattr(submission, "auth_info"):
            return None

        from openforms.authentication.utils import FormAuth

        auth_data = FormAuth(
            plugin=submission.auth_info.plugin,
            attribute=submission.auth_info.attribute,
            value=submission.auth_info.value,
            # TODO what is the structure of the data in the machtigen field?
            machtigen=submission.auth_info.machtigen,
        )

        return auth_data


def get_auth_value(submission: Optional["Submission"], attribute: str) -> str:
    if not submission or not hasattr(submission, "auth_info"):
        return ""

    if submission.auth_info.attribute == attribute:
        return submission.auth_info.value

    return ""


@static_variables_register("auth_bsn")
class AuthBSN(BaseStaticVariable):
    name = _("Authentication BSN")
    data_type = FormVariableDataTypes.string

    def get_initial_value(self, submission: Optional["Submission"]) -> str:
        return get_auth_value(submission, AuthAttribute.bsn)


@static_variables_register("auth_kvk")
class AuthKvK(BaseStaticVariable):
    name = _("Authentication KvK")
    data_type = FormVariableDataTypes.string

    def get_initial_value(self, submission: Optional["Submission"]) -> str:
        return get_auth_value(submission, AuthAttribute.kvk)


@static_variables_register("auth_pseudo")
class AuthPseudo(BaseStaticVariable):
    name = _("Authentication pseudo")
    data_type = FormVariableDataTypes.string

    def get_initial_value(self, submission: Optional["Submission"]) -> str:
        return get_auth_value(submission, AuthAttribute.pseudo)
