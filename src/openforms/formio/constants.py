from django.db import models

COMPONENT_DATATYPES = {
    "date": "date",
    "time": "time",
    "file": "array",
    "currency": "float",
    "number": "float",
    "checkbox": "boolean",
    "selectboxes": "object",
    "npFamilyMembers": "object",
    "map": "array",
    "editgrid": "array",
    "datetime": "datetime",
}


class GeoJsonGeometryTypes(models.TextChoices):
    point = "Point", "Point"
    polygon = "Polygon", "Polygon"
    line_string = "LineString", "LineString"
