from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _

from openforms.variables.base import BaseStaticVariable
from openforms.variables.constants import FormVariableDataTypes
from openforms.variables.registry import register_static_variable

from ..constants import AuthAttribute
from ..typing import FormAuth

if TYPE_CHECKING:
    from openforms.submissions.models import Submission


@register_static_variable("auth")
class Auth(BaseStaticVariable):
    name = _("Authentication")
    data_type = FormVariableDataTypes.object

    def get_initial_value(
        self, submission: Submission | None = None
    ) -> FormAuth | None:
        if not submission or not submission.is_authenticated:
            return None

        auth_data = FormAuth(
            plugin=submission.auth_info.plugin,
            attribute=submission.auth_info.attribute,
            value=submission.auth_info.value,
            # XXX: use to_auth_context_data_method() here? Or make it a separate var?
            # TODO what is the structure of the data in the machtigen field?
            machtigen=submission.auth_info.machtigen,
        )

        return auth_data


@register_static_variable("auth_type")
class AuthType(BaseStaticVariable):
    name = _("Authentication type")
    data_type = FormVariableDataTypes.string

    def get_initial_value(self, submission: Submission | None = None) -> str:
        if not submission or not submission.is_authenticated:
            return ""
        return submission.auth_info.attribute


def get_auth_value(submission: Submission | None, attribute: AuthAttribute) -> str:
    if not submission or not submission.is_authenticated:
        return ""

    if submission.auth_info.attribute == attribute:
        return submission.auth_info.value

    return ""


@register_static_variable("auth_bsn")
class AuthBSN(BaseStaticVariable):
    name = _("Authentication BSN")
    data_type = FormVariableDataTypes.string

    def get_initial_value(self, submission: Submission | None = None) -> str:
        return get_auth_value(submission, AuthAttribute.bsn)


@register_static_variable("auth_kvk")
class AuthKvK(BaseStaticVariable):
    name = _("Authentication KvK")
    data_type = FormVariableDataTypes.string

    def get_initial_value(self, submission: Submission | None = None) -> str:
        return get_auth_value(submission, AuthAttribute.kvk)


@register_static_variable("auth_pseudo")
class AuthPseudo(BaseStaticVariable):
    name = _("Authentication pseudo")
    data_type = FormVariableDataTypes.string

    def get_initial_value(self, submission: Submission | None = None) -> str:
        return get_auth_value(submission, AuthAttribute.pseudo)


@register_static_variable("auth_context")
class AuthContext(BaseStaticVariable):
    name = _("Authentication context data")
    data_type = FormVariableDataTypes.object

    def get_initial_value(self, submission: Submission | None = None):
        if submission is None:
            return None
        if not submission.is_authenticated:
            return None
        return submission.auth_info.to_auth_context_data()


@register_static_variable("auth_context_source")
class AuthContextSource(BaseStaticVariable):
    name = _("Authentication context data: source")
    data_type = FormVariableDataTypes.string

    def get_initial_value(self, submission: Submission | None = None) -> str:
        if submission is None or not submission.is_authenticated:
            return ""
        auth_context = submission.auth_info.to_auth_context_data()
        return auth_context["source"]


@register_static_variable("auth_context_loa")
class AuthContextLOA(BaseStaticVariable):
    name = _("Authentication context data: level of assurance")
    data_type = FormVariableDataTypes.string

    def get_initial_value(self, submission: Submission | None = None) -> str:
        if submission is None or not submission.is_authenticated:
            return ""
        auth_context = submission.auth_info.to_auth_context_data()
        return auth_context["levelOfAssurance"]


@register_static_variable("auth_context_representee_identifier_type")
class AuthContextRepresenteeType(BaseStaticVariable):
    name = _("Authentication context data: representee identifier type")
    data_type = FormVariableDataTypes.string

    def get_initial_value(self, submission: Submission | None = None) -> str:
        if submission is None or not submission.is_authenticated:
            return ""
        auth_context = submission.auth_info.to_auth_context_data()
        if "representee" not in auth_context:
            return ""
        return auth_context["representee"]["identifierType"]


@register_static_variable("auth_context_representee_identifier")
class AuthContextRepresenteeIdentifier(BaseStaticVariable):
    name = _("Authentication context data: representee identifier")
    data_type = FormVariableDataTypes.string

    def get_initial_value(self, submission: Submission | None = None) -> str:
        if submission is None or not submission.is_authenticated:
            return ""
        auth_context = submission.auth_info.to_auth_context_data()
        if "representee" not in auth_context:
            return ""
        return auth_context["representee"]["identifier"]


@register_static_variable("auth_context_legal_subject_identifier_type")
class AuthContextLegalSubjectIdentifierType(BaseStaticVariable):
    name = _("Authentication context data: authorizee, legal subject identifier type")
    data_type = FormVariableDataTypes.string

    def get_initial_value(self, submission: Submission | None = None) -> str:
        if submission is None or not submission.is_authenticated:
            return ""
        auth_context = submission.auth_info.to_auth_context_data()
        return auth_context["authorizee"]["legalSubject"]["identifierType"]


@register_static_variable("auth_context_legal_subject_identifier")
class AuthContextLegalSubjectIdentifier(BaseStaticVariable):
    name = _("Authentication context data: authorizee, legal subject identifier")
    data_type = FormVariableDataTypes.string

    def get_initial_value(self, submission: Submission | None = None) -> str:
        if submission is None or not submission.is_authenticated:
            return ""
        auth_context = submission.auth_info.to_auth_context_data()
        return auth_context["authorizee"]["legalSubject"]["identifier"]


@register_static_variable("auth_context_acting_subject_identifier_type")
class AuthContextActingSubjectIdentifierType(BaseStaticVariable):
    name = _("Authentication context data: authorizee, acting subject identifier type")
    data_type = FormVariableDataTypes.string

    def get_initial_value(self, submission: Submission | None = None) -> str:
        if submission is None or not submission.is_authenticated:
            return ""
        auth_context = submission.auth_info.to_auth_context_data()
        if "actingSubject" not in auth_context["authorizee"]:
            return ""
        return auth_context["authorizee"]["actingSubject"]["identifierType"]


@register_static_variable("auth_context_acting_subject_identifier")
class AuthContextActingSubjectIdentifier(BaseStaticVariable):
    name = _("Authentication context data: authorizee, acting subject identifier")
    data_type = FormVariableDataTypes.string

    def get_initial_value(self, submission: Submission | None = None) -> str:
        if submission is None or not submission.is_authenticated:
            return ""
        auth_context = submission.auth_info.to_auth_context_data()
        if "actingSubject" not in auth_context["authorizee"]:
            return ""
        return auth_context["authorizee"]["actingSubject"]["identifier"]
