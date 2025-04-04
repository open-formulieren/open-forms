from copy import deepcopy
from typing import Literal, TypedDict

from django.db import models
from django.utils.translation import gettext_lazy as _

from drf_polymorphic.serializers import PolymorphicSerializer
from rest_framework import serializers


class GeoJsonGeometryTypes(models.TextChoices):
    point = "Point", _("Point")
    polygon = "Polygon", _("Polygon")
    line_string = "LineString", _("LineString")


class GeoJSONCoordinatesField(serializers.ListField):
    child = serializers.FloatField(required=True, allow_null=False)

    def __init__(self, *args, **kwargs):
        kwargs["min_length"] = 2
        kwargs["max_length"] = 2
        super().__init__(*args, **kwargs)


class GeoJSONPointGeometrySerializer(serializers.Serializer):
    coordinates = GeoJSONCoordinatesField()


class GeoJSONLineStringGeometrySerializer(serializers.Serializer):
    coordinates = serializers.ListField(child=GeoJSONCoordinatesField())


class GeoJSONPolygonGeometrySerializer(serializers.Serializer):
    coordinates = serializers.ListField(
        child=serializers.ListField(child=GeoJSONCoordinatesField())
    )


class GeoJsonGeometryPolymorphicSerializer(PolymorphicSerializer):
    type = serializers.ChoiceField(choices=GeoJsonGeometryTypes.choices, required=True)

    discriminator_field = "type"
    serializer_mapping = {
        GeoJsonGeometryTypes.point: GeoJSONPointGeometrySerializer,
        GeoJsonGeometryTypes.line_string: GeoJSONLineStringGeometrySerializer,
        GeoJsonGeometryTypes.polygon: GeoJSONPolygonGeometrySerializer,
    }


type Coordinates = tuple[float, float]


class PointGeometry(TypedDict):
    type: Literal["Point"]
    coordinates: Coordinates


class LineStringGeometry(TypedDict):
    type: Literal["LineString"]
    coordinates: list[Coordinates]


class PolygonGeometry(TypedDict):
    type: Literal["Polygon"]
    coordinates: list[list[Coordinates]]


# TODO-5027: probably this needs to go somewhere else... Perhaps
#  openforms.formio.components.json_schema?
COORDINATE_SCHEMA = {
    "type": "array",
    "prefixItems": [
        {"title": "Longitude", "type": "number"},
        {"title": "Latitude", "type": "number"},
    ],
    "items": False,
    "minItems": 2,
}

LINE_COORDINATE_SCHEMA = {
    "type": "array",
    "minItems": 2,
    "items": deepcopy(COORDINATE_SCHEMA),
}

POLYGON_COORDINATE_SCHEMA = {
    "type": "array",
    "minItems": 1,
    "maxItems": 1,
    "items": {
        "type": "array",
        "minItems": 4,
        "items": deepcopy(COORDINATE_SCHEMA),
    },
}

GEO_JSON_COORDINATE_SCHEMAS = {
    GeoJsonGeometryTypes.point: COORDINATE_SCHEMA,
    GeoJsonGeometryTypes.line_string: LINE_COORDINATE_SCHEMA,
    GeoJsonGeometryTypes.polygon: POLYGON_COORDINATE_SCHEMA,
}

GEO_JSON_TYPE_TO_INTERACTION = {
    GeoJsonGeometryTypes.point: "marker",
    GeoJsonGeometryTypes.polygon: "polygon",
    GeoJsonGeometryTypes.line_string: "polyline",
}
