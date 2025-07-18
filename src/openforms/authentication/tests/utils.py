import copy
import json
from pathlib import Path

from django.urls import reverse

from digid_eherkenning.choices import AssuranceLevels, DigiDAssuranceLevels
from furl import furl
from glom import assign
from jsonschema import ValidationError, Validator
from jsonschema.validators import validator_for
from mozilla_django_oidc_db.constants import OIDC_ADMIN_CONFIG_IDENTIFIER
from mozilla_django_oidc_db.models import OIDCClient, OIDCProvider

from openforms.authentication.contrib.digid_eherkenning_oidc.oidc_plugins.constants import (
    OIDC_DIGID_IDENTIFIER,
    OIDC_DIGID_MACHTIGEN_IDENTIFIER,
    OIDC_EH_BEWINDVOERING_IDENTIFIER,
    OIDC_EH_IDENTIFIER,
)
from openforms.authentication.contrib.org_oidc.oidc_plugins.constants import (
    OIDC_ORG_IDENTIFIER,
)
from openforms.forms.models import Form
from openforms.typing import JSONObject


class URLsHelper:
    """
    Small helper to get the right frontend URLs for authentication flows.
    """

    def __init__(self, form: Form, host: str = "http://testserver"):
        self.form = form
        self.host = host

    @property
    def form_path(self) -> str:
        return reverse("core:form-detail", kwargs={"slug": self.form.slug})

    @property
    def frontend_start(self) -> str:
        """
        Compute the frontend URL that will trigger a submissions start.
        """
        form_url = furl(f"{self.host}{self.form_path}").set({"_start": "1"})
        return str(form_url)

    @property
    def api_resource(self) -> str:
        api_path = reverse("api:form-detail", kwargs={"uuid_or_slug": self.form.uuid})
        return f"{self.host}{api_path}"

    def get_auth_start(self, plugin_id: str) -> str:
        """
        Compute the authentication start URL for the specified plugin ID.
        """
        login_url = reverse(
            "authentication:start",
            kwargs={"slug": self.form.slug, "plugin_id": plugin_id},
        )
        start_url = furl(login_url).set({"next": self.frontend_start})
        return str(start_url)


SCHEMA_FILE = Path(__file__).parent.resolve() / "auth_context_schema.json"


def _get_validator() -> Validator:
    with SCHEMA_FILE.open("r") as infile:
        schema = json.load(infile)
    return validator_for(schema)(schema)


validator = _get_validator()


class AuthContextAssertMixin:
    def assertValidContext(self, context):
        try:
            validator.validate(context)
        except ValidationError as exc:
            raise self.failureException(
                "Context is not valid according to schema"
            ) from exc


CLIENT_DEFAULT_OPTIONS = {
    OIDC_ADMIN_CONFIG_IDENTIFIER: {
        "user_settings": {
            "claim_mappings": {
                "username": ["sub"],
                "first_name": [],
                "last_name": [],
                "email": [],
            },
            "username_case_sensitive": True,
            "sensitive_claims": [],
        },
        "groups_settings": {
            "claim_mapping": ["groups"],
            "sync": True,
            "sync_pattern": "*",
            "make_users_staff": False,
            "superuser_group_names": [],
            "default_groups": [],
        },
    },
    OIDC_DIGID_IDENTIFIER: {
        "loa_settings": {
            "claim_path": ["authsp_level"],
            "default": DigiDAssuranceLevels.middle,
            "value_mapping": [],
        },
        "identity_settings": {
            "bsn_claim_path": ["bsn"],
        },
    },
    OIDC_EH_IDENTIFIER: {
        "loa_settings": {
            "claim_path": ["authsp_level"],
            "default": AssuranceLevels.low_plus,
            "value_mapping": [],
        },
        "identity_settings": {
            "identifier_type_claim_path": ["name_qualifier"],
            "legal_subject_claim_path": ["legalSubjectID"],
            "acting_subject_claim_path": ["actingSubjectID"],
        },
    },
    OIDC_DIGID_MACHTIGEN_IDENTIFIER: {
        "loa_settings": {
            "claim_path": ["authsp_level"],
            "default": DigiDAssuranceLevels.middle,
            "value_mapping": [],
        },
        "identity_settings": {
            "representee_bsn_claim_path": ["aanvrager.bsn"],
            "authorizee_bsn_claim_path": ["gemachtigde.bsn"],
            "mandate_service_id_claim_path": ["service_id"],
        },
    },
    OIDC_EH_BEWINDVOERING_IDENTIFIER: {
        "loa_settings": {
            "claim_path": ["authsp_level"],
            "default": AssuranceLevels.low_plus,
            "value_mapping": [],
        },
        "identity_settings": {
            "identifier_type_claim_path": ["name_qualifier"],
            "legal_subject_claim_path": ["aanvrager.kvk"],
            "acting_subject_claim_path": ["actingSubjectID"],
            "representee_claim_path": ["representeeBSN"],
            "mandate_service_id_claim_path": ["service_id"],
            "mandate_service_uuid_claim_path": ["service_uuid"],
        },
    },
    OIDC_ORG_IDENTIFIER: {
        "user_settings": {
            "claim_mappings": {
                "username": ["preferred_username"],
                "email": ["email"],
                "employee_id": ["employeeId"],
            },
            "username_case_sensitive": True,
            "sensitive_claims": [],
        },
        "groups_settings": {
            "claim_mapping": ["groups"],
            "sync": True,
            "sync_pattern": "*",
            "make_users_staff": False,
            "superuser_group_names": [],
            "default_groups": [],
        },
    },
}
CLIENT_DEFAULT_SCOPES = {
    OIDC_DIGID_IDENTIFIER: ["openid", "bsn"],
    OIDC_DIGID_MACHTIGEN_IDENTIFIER: ["openid", "bsn"],
    OIDC_EH_IDENTIFIER: ["openid", "kvk"],
    OIDC_EH_BEWINDVOERING_IDENTIFIER: ["openid", "bsn"],
    OIDC_ADMIN_CONFIG_IDENTIFIER: ["email", "profile", "openid"],
    OIDC_ORG_IDENTIFIER: ["openid", "email", "profile", "employeeId"],
}


def make_client(
    identifier: str, provider: OIDCProvider, overrides: JSONObject | None = None
) -> OIDCClient:
    defaults = {
        "enabled": True,
        "oidc_rp_client_id": "testid",
        "oidc_rp_client_secret": "7DB3KUAAizYCcmZufpHRVOcD0TOkNO3I",
        "oidc_rp_sign_algo": "RS256",
        "oidc_rp_scopes_list": copy.deepcopy(CLIENT_DEFAULT_SCOPES[identifier]),
        "oidc_provider": provider,
        "options": copy.deepcopy(CLIENT_DEFAULT_OPTIONS[identifier]),
    }
    if overrides:
        for override_path, override_value in overrides.items():
            assign(defaults, override_path, override_value)

    client, _ = OIDCClient.objects.update_or_create(
        identifier=identifier,
        defaults=defaults,
    )
    return client
