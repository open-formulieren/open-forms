from typing import NotRequired, TypedDict

from openforms.typing import JSONObject


class Record(TypedDict):
    typeVersion: int
    startAt: str
    data: JSONObject
    geometry: NotRequired[JSONObject]  # TODO: narrow to GeoJSON


class Object(TypedDict):
    type: NotRequired[str]  # Required for create, optional for update
    record: Record
