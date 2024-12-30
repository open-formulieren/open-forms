from typing import TypedDict
from uuid import UUID

from openforms.contrib.objects_api.models import ObjectsAPIGroupConfig


class VariableMapping(TypedDict):
    variable_key: str
    target_path: list[str]


class ObjectsAPIOptions(TypedDict):
    objects_api_group: ObjectsAPIGroupConfig
    objecttype_uuid: UUID
    objecttype_version: int
    skip_ownership_check: bool
    auth_attribute_path: list[str]
    variables_mapping: list[VariableMapping]
