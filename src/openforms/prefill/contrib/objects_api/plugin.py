import logging
from typing import Any, Iterable

from click import option
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from glom import GlomError, glom

from openforms.authentication.service import AuthAttribute
from openforms.registrations.contrib.objects_api.client import (
    get_objects_client,
    get_objecttypes_client,
)
from openforms.registrations.contrib.objects_api.models import ObjectsAPIGroupConfig
from openforms.submissions.models import Submission
from openforms.typing import JSONEncodable
from ...base import BasePlugin
from ...constants import IdentifierRoles
from ...registry import register
from .constants import ObjectsAPIAttributes

logger = logging.getLogger(__name__)

PLUGIN_IDENTIFIER = "objects_api"


@register(PLUGIN_IDENTIFIER)
class ObjectsAPIPrefill(BasePlugin):
    verbose_name = _("Objects API")
    requires_auth = AuthAttribute.bsn

    @classmethod
    def parse_schema_properties(
        cls, schema, parent_key: str = ""
    ) -> list[tuple[str, str]]:
        properties = []

        if schema["type"] == "object":
            for prop, prop_schema in schema.get("properties", {}).items():
                full_key = f"{parent_key}.{prop}" if parent_key else prop
                prop_type = prop_schema.get("type", "unknown")
                properties.append((full_key, prop_type))
                if prop_type == "object" or (
                    prop_type == "array" and "items" in prop_schema
                ):
                    properties.extend(
                        cls.parse_schema_properties(prop_schema, full_key)
                    )
        elif schema["type"] == "array":
            items_schema = schema.get("items", {})
            if isinstance(items_schema, dict):
                properties.extend(
                    cls.parse_schema_properties(items_schema, f"{parent_key}[]")
                )
            elif isinstance(items_schema, list):
                for i, item_schema in enumerate(items_schema):
                    properties.extend(
                        cls.parse_schema_properties(item_schema, f"{parent_key}[{i}]")
                    )
        else:
            properties.append((parent_key, schema["type"]))

        return properties

    @staticmethod
    def get_available_attributes() -> Iterable[tuple[str, str]]:
        # attrs = ObjectsAPIAttributes.choices
        # attrs += dynamic_properties
        pass

    @classmethod
    def get_prefill_values(
        cls,
        submission: Submission,
        attributes: list[str],
        identifier_role: IdentifierRoles = IdentifierRoles.main,
    ) -> dict[str, JSONEncodable]:
        # for testing purposes, this will be defined in the modal by the user
        # frontend is not ready yet
        options = submission.registration_backend.options
        config = ObjectsAPIGroupConfig.objects.get(pk=options["objects_api_group"])

        if object_uuid := submission.initial_data_reference:
            with get_objecttypes_client(config) as objecttypes_client:
                objecttype = objecttypes_client.get_objecttype_version(
                    options["objecttype"], options["objecttype_version"]
                )

                if objecttype["status"] != "published":
                    logger.warning(
                        "object type '%s' is not published yet", objecttype["url"]
                    )
                    return {}

                if json_schema := objecttype.get("jsonSchema"):
                    properties = cls.parse_schema_properties(json_schema)

        return {}

    @classmethod
    def get_co_sign_values(
        cls, submission: Submission, identifier: str
    ) -> tuple[dict[str, Any], str]:
        pass

    def check_config(self):
        pass
