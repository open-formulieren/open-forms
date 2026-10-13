from __future__ import annotations

import uuid
from collections.abc import Callable, Sequence
from typing import Annotated, Literal, NewType

import msgspec

from ..base_component import (
    BaseOpenFormsExtensions,
    Component,
    Conditional,
    Errors,
    FAQItem,
    FormioStruct,
    Registration,
    TranslatedErrors,
)
from ..templating import TestWithTrace

Lon = NewType("Lon", float)
Lat = NewType("Lat", float)


class InitialCenter(FormioStruct):
    lng: Lon | msgspec.UnsetType = msgspec.UNSET
    lat: Lat | msgspec.UnsetType = msgspec.UNSET


class Overlay(FormioStruct):
    label: str
    layers: Sequence[str]
    type: Literal["wms", "wfs"]
    url: str = ""  # dynamically set by the backend code
    uuid: uuid.UUID


type MapValidatorKeys = Literal["required"]

type MapTranslatableProperties = Literal["label", "description", "tooltip"]

MapExtensions = BaseOpenFormsExtensions[MapTranslatableProperties]


class MapInteractions(FormioStruct, frozen=True):
    marker: bool = True
    polygon: bool = False
    polyline: bool = False


class MapValidate(FormioStruct):
    required: bool = False
    plugins: Sequence[str] = []


class Map(Component, tag="map"):
    clear_on_hide: bool = True
    conditional: Conditional | msgspec.UnsetType = msgspec.UNSET
    default_zoom: Annotated[int, msgspec.Meta(ge=1, le=13)] | None = None
    description: str = ""
    errors: Errors[MapValidatorKeys] | msgspec.UnsetType = msgspec.UNSET
    faq_items: Sequence[FAQItem] = []
    hidden: bool = False
    initial_center: InitialCenter | msgspec.UnsetType = msgspec.UNSET
    interactions: MapInteractions = MapInteractions(marker=True)
    is_sensitive_data: bool = False
    label: str
    open_forms: MapExtensions | msgspec.UnsetType = msgspec.UNSET
    overlays: Sequence[Overlay] | msgspec.UnsetType = msgspec.UNSET
    registration: Registration | msgspec.UnsetType = msgspec.UNSET
    show_in_email: bool = False
    show_in_pdf: bool = msgspec.field(name="showInPDF", default=True)
    show_in_summary: bool = True
    tile_layer_identifier: str | msgspec.UnsetType = msgspec.UNSET
    tile_layer_url: str | msgspec.UnsetType = msgspec.UNSET
    use_config_default_map_settings: bool = False
    tooltip: str = ""
    translated_errors: TranslatedErrors[MapValidatorKeys] | msgspec.UnsetType = (
        msgspec.UNSET
    )
    validate: MapValidate = msgspec.field(default_factory=MapValidate)

    def render_templates(self, do_render: Callable[[str], str]) -> None:
        self.label = do_render(self.label)
        self.description = do_render(self.description)
        self.tooltip = do_render(self.tooltip)

    def _test_templates(self, test_with_trace: TestWithTrace) -> None:
        test_with_trace(self.label, attribute="label")
        test_with_trace(self.description, attribute="description")
        test_with_trace(self.tooltip, attribute="tooltip")
