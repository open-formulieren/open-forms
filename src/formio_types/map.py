from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Annotated, Literal, NewType

import msgspec

from ._base import (
    BaseOpenFormsExtensions,
    Component,
    Conditional,
    Errors,
    FormioStruct,
    Registration,
    TranslatedErrors,
)

Lon = NewType("Lon", float)
Lat = NewType("Lat", float)

type Coordinates = tuple[Lon, Lat]


class Point(msgspec.Struct, kw_only=True, tag="Point"):
    coordinates: Coordinates


class LineString(msgspec.Struct, kw_only=True, tag="LineString"):
    coordinates: list[Coordinates]


class Polygon(msgspec.Struct, kw_only=True, tag="Polygon"):
    coordinates: list[list[Coordinates]]


type GeoJsonGeometry = Point | LineString | Polygon


class Overlay(FormioStruct):
    label: str
    layers: Sequence[str]
    type: Literal["wms", "wfs"]
    url: str
    uuid: uuid.UUID


type MapValidatorKeys = Literal["required"]
type MapExtensions = BaseOpenFormsExtensions[Literal["label", "description", "tooltip"]]


class MapInteractions(FormioStruct, frozen=True):
    marker: bool = False
    polygon: bool = False
    polyline: bool = False


class MapValidate(FormioStruct):
    required: bool = False


class Map(Component, tag="map"):
    clear_on_hide: bool = True
    conditional: Conditional | None = None
    default_value: GeoJsonGeometry | None = None
    default_zoom: Annotated[int, msgspec.Meta(ge=1, le=13)] | None = None
    description: str = ""
    errors: Errors[MapValidatorKeys] | None = None
    hidden: bool = False
    interactions: MapInteractions = MapInteractions(marker=True)
    is_sensitive_data: bool = False
    label: str
    open_forms: MapExtensions | None = None
    overlays: Sequence[Overlay] | None = None
    registration: Registration | None = None
    show_in_email: bool = False
    show_in_pdf: bool = True
    show_in_summary: bool = True
    tile_layer_identifier: str | None = None
    tooltip: str = ""
    translated_errors: TranslatedErrors[MapValidatorKeys] | None = None
    validate: MapValidate | None = None
    validate_on: Literal["blur", "change"] = "blur"
