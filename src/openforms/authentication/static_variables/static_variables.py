from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from django.utils.translation import gettext_lazy as _

from openforms.variables.base import BaseStaticVariable
from openforms.variables.constants import FormVariableDataTypes
from openforms.variables.registry import register_static_variable

from ..constants import AuthAttribute
from ..typing import FormAuth

if TYPE_CHECKING:
    from openforms.submissions.models import Submission


@register_static_variable("submission_id")
class SubmissionID(BaseStaticVariable):
    name = _("Internal ID")
    data_type = FormVariableDataTypes.string

    def get_initial_value(self, submission: Submission | None = None) -> str:
        return str(submission.uuid) if submission else ""

    def as_json_schema(self):
        return {
            "title": "Submission identifier",
            "description": "UUID of the submission",
            "type": "string",
            "format": "uuid",
        }


@register_static_variable("language_code")
class LanguageCode(BaseStaticVariable):
    name = _("Language code")
    data_type = FormVariableDataTypes.string

    def get_initial_value(self, submission: Submission | None = None) -> str:
        return submission.language_code if submission else ""

    def as_json_schema(self):
        return {
            "title": "Language code",
            "description": "Abbreviation of the used langauge.",
            "type": "string",
            "enum": [language[0] for language in settings.LANGUAGES],
        }


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
            additional_claims=submission.auth_info.additional_claims,
        )

        return auth_data

    def as_json_schema(self):
        # NOTE: this has been made 'vague' on purpose, see the comment on AuthContext.
        # Will be ``null`` when no authentication was used.
        return {
            "title": "Authentication summary",
            "type": ["object", "null"],
            "additionalProperties": True,
        }


@register_static_variable("auth_type")
class AuthType(BaseStaticVariable):
    name = _("Authentication type")
    data_type = FormVariableDataTypes.string

    def get_initial_value(self, submission: Submission | None = None) -> str:
        if not submission or not submission.is_authenticated:
            return ""
        return submission.auth_info.attribute

    def as_json_schema(self):
        return {
            "title": "Authentication type",
            "type": "string",
            "enum": [*AuthAttribute.values, ""],
        }


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

    def as_json_schema(self):
        return {
            "title": "BSN",
            "description": (
                "Uniquely identifies the authenticated person. This value follows the "
                "rules for Dutch social security numbers."
            ),
            "type": "string",
            "pattern": r"^\d{9}$|^$",  # Note: will be an empty string if no authentication was used
            "format": "nl-bsn",
        }


@register_static_variable("auth_kvk")
class AuthKvK(BaseStaticVariable):
    name = _("Authentication KvK")
    data_type = FormVariableDataTypes.string

    def get_initial_value(self, submission: Submission | None = None) -> str:
        return get_auth_value(submission, AuthAttribute.kvk)

    def as_json_schema(self):
        return {
            "title": "KVK",
            "description": (
                "Chamber of commerce number (KVK-nummer) that uniquely identifies the "
                "company."
            ),
            "type": "string",
            "pattern": r"^\d{8}$|^$",  # Note: will be an empty string if no authentication was used
            "format": "urn:etoegang:1.9:EntityConcernedID:KvKnr",
        }


@register_static_variable("auth_pseudo")
class AuthPseudo(BaseStaticVariable):
    name = _("Authentication pseudo")
    data_type = FormVariableDataTypes.string

    def get_initial_value(self, submission: Submission | None = None) -> str:
        return get_auth_value(submission, AuthAttribute.pseudo)

    def as_json_schema(self):
        return {"title": "Pseudo", "type": "string"}


@register_static_variable("auth_additional_claims")
class AuthAdditionalClaims(BaseStaticVariable):
    name = _("Authentication additional claims")
    data_type = FormVariableDataTypes.object

    def get_initial_value(self, submission: Submission | None = None):
        if submission is None or not submission.is_authenticated:
            return None
        return submission.auth_info.additional_claims

    def as_json_schema(self):
        return {
            "title": "Authentication additional claims",
            "description": "Additional claims returned by the authentication backend.",
            "type": ["object", "null"],
        }


@register_static_variable("auth_context")
class AuthContext(BaseStaticVariable):
    name = _("Authentication context data")
    data_type = FormVariableDataTypes.object

    def get_initial_value(self, submission: Submission | None = None):
        if submission is None:
            return None
        if not submission.is_authenticated:
            return None
        auth_context = submission.auth_info.to_auth_context_data()
        if auth_context.get("source") == "yivi":
            # The `additionalInformation` for yivi authentication contains yivi
            # attributes, which won't be accessible for jsonlogic and django templating.
            # So we have to clean them.
            auth_context["authorizee"]["legalSubject"]["additionalInformation"] = (
                auth_context["authorizee"]["legalSubject"]["additionalInformation"]
            )

        return auth_context

    def as_json_schema(self):
        # NOTE: `auth_context` includes all relevant options for the authentication
        # plugin, which means its values are plugin dependent. Therefore, to discourage
        # users from using this, no specific object information will be provided here.
        # Instead, variables like `auth_bsn` and `auth_kvk` should be used for
        # extracting information about authentication (they are strictly defined with a
        # schema). Will be ``null`` when no authentication was used.
        return {
            "title": "Authentication options",
            "description": "Options for the selected authentication plugin",
            "type": ["object", "null"],
        }


@register_static_variable("auth_context_source")
class AuthContextSource(BaseStaticVariable):
    name = _("Authentication context data: source")
    data_type = FormVariableDataTypes.string

    def get_initial_value(self, submission: Submission | None = None) -> str:
        if submission is None or not submission.is_authenticated:
            return ""
        auth_context = submission.auth_info.to_auth_context_data()
        return auth_context["source"]

    def as_json_schema(self):
        return {
            "title": "Authentication source",
            "description": "Name of the authentication source",
            "type": "string",
        }


@register_static_variable("auth_context_loa")
class AuthContextLOA(BaseStaticVariable):
    name = _("Authentication context data: level of assurance")
    data_type = FormVariableDataTypes.string

    def get_initial_value(self, submission: Submission | None = None) -> str:
        if submission is None or not submission.is_authenticated:
            return ""
        auth_context = submission.auth_info.to_auth_context_data()
        return auth_context["levelOfAssurance"]

    def as_json_schema(self):
        return {
            "title": "Authentication level of assurance",
            "description": (
                "afsprakenstelsel.etoegang.nl defines the available levels of "
                "assurance *and* prescribes what the minimum level must be. Note that "
                "a minimum of loa2plus is required these days."
            ),
            "type": "string",
        }


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

    def as_json_schema(self):
        return {
            "title": "Representee authentication type",
            "description": "Authentication type of the representee",
            "type": "string",
        }


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

    def as_json_schema(self):
        return {
            "title": "Representee authentication identifier",
            "description": "Authentication identifier of the representee.",
            "type": "string",
        }


@register_static_variable("auth_context_legal_subject_identifier_type")
class AuthContextLegalSubjectIdentifierType(BaseStaticVariable):
    name = _("Authentication context data: authorizee, legal subject identifier type")
    data_type = FormVariableDataTypes.string

    def get_initial_value(self, submission: Submission | None = None) -> str:
        if submission is None or not submission.is_authenticated:
            return ""
        auth_context = submission.auth_info.to_auth_context_data()
        return auth_context["authorizee"]["legalSubject"]["identifierType"]

    def as_json_schema(self):
        return {
            "title": "Legal subject authentication type",
            "description": (
                "Authentication type of the legal subject (mandated to act on behalf "
                "of the representee)"
            ),
            "type": "string",
        }


@register_static_variable("auth_context_legal_subject_identifier")
class AuthContextLegalSubjectIdentifier(BaseStaticVariable):
    name = _("Authentication context data: authorizee, legal subject identifier")
    data_type = FormVariableDataTypes.string

    def get_initial_value(self, submission: Submission | None = None) -> str:
        if submission is None or not submission.is_authenticated:
            return ""
        auth_context = submission.auth_info.to_auth_context_data()
        return auth_context["authorizee"]["legalSubject"]["identifier"]

    def as_json_schema(self):
        return {
            "title": "Legal subject authentication identifier",
            "description": (
                "Authentication identifier of the legal subject (mandated to act on "
                "behalf of the representee)"
            ),
            "type": "string",
        }


@register_static_variable("auth_context_branch_number")
class AuthContextBranchNumber(BaseStaticVariable):
    name = _("Authentication context data: branch number")
    data_type = FormVariableDataTypes.string

    def get_initial_value(self, submission: Submission | None = None) -> str:
        if submission is None or not submission.is_authenticated:
            return ""
        auth_context = submission.auth_info.to_auth_context_data()
        if auth_context["source"] != "eherkenning":
            return ""
        legal_subject = auth_context["authorizee"]["legalSubject"]
        return legal_subject.get("branchNumber", "")

    def as_json_schema(self):
        return {
            "title": "Authentication branch number",
            "description": (
                "The branch number imposes a restriction on the acting subject - it is "
                "limited to act only on this particular branch of the legal subject."
            ),
            "type": "string",
        }


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

    def as_json_schema(self):
        return {"title": "Acting subject authentication type", "type": "string"}


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

    def as_json_schema(self):
        return {"title": "Acting subject authentication identifier", "type": "string"}
