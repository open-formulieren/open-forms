from typing import TypedDict
from uuid import UUID

from openforms.contrib.objects_api.models import ObjectsAPIGroupConfig


class VariableMapping(TypedDict):
    variable_key: str
    target_path: list[str]


class ObjectsAPIOptions(TypedDict):
    objects_api_group: ObjectsAPIGroupConfig
    object_type_uuid: UUID
    objecttype_version: int
    variables_mapping: list[VariableMapping]