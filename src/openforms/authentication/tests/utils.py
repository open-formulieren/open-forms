import json
from pathlib import Path

from django.urls import reverse

from furl import furl
from jsonschema import ValidationError, Validator
from jsonschema.validators import validator_for

from openforms.forms.models import Form


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
            raise self.failureException(  # pyright: ignore[reportAttributeAccessIssue]
                "Context is not valid according to schema"
            ) from exc
