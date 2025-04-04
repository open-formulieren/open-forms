from openforms.api.geojson import GeoJsonGeometryTypes
from openforms.typing import JSONObject

GEO_JSON_COORDINATE_SCHEMA = {
    "type": "array",
    "prefixItems": [
        {"title": "Longitude", "type": "number"},
        {"title": "Latitude", "type": "number"},
    ],
    "items": False,
    "minItems": 2,
}

GEO_JSON_LINE_COORDINATE_SCHEMA = {
    "type": "array",
    "minItems": 2,
    "items": GEO_JSON_COORDINATE_SCHEMA,
}

GEO_JSON_POLYGON_COORDINATE_SCHEMA = {
    "type": "array",
    "minItems": 1,
    "maxItems": 1,
    "items": {
        "type": "array",
        "minItems": 4,
        "items": GEO_JSON_COORDINATE_SCHEMA,
    },
}

GEO_JSON_COORDINATE_SCHEMAS = {
    GeoJsonGeometryTypes.point: GEO_JSON_COORDINATE_SCHEMA,
    GeoJsonGeometryTypes.line_string: GEO_JSON_LINE_COORDINATE_SCHEMA,
    GeoJsonGeometryTypes.polygon: GEO_JSON_POLYGON_COORDINATE_SCHEMA,
}


def to_multiple(schema: JSONObject) -> JSONObject:
    """Convert a JSON schema of a component to a schema of multiple components.

    :param schema: JSON schema of a component.
    :returns: JSON schema of multiple components.
    """
    title = schema.pop("title")
    return {
        "title": title,
        "type": "array",
        "items": schema,
    }
