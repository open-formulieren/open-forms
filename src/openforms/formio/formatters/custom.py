# TODO implement: iban, bsn, postcode, licenseplate, npFamilyMembers, cosign
import base64
from datetime import date, datetime
from io import BytesIO
from typing import NotRequired, TypedDict

from django.template.defaultfilters import date as fmt_date, time as fmt_time
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from openforms.api.geojson import LineStringGeometry, PointGeometry, PolygonGeometry
from openforms.config.models import MapTileLayer
from openforms.utils.map.wmts_draw import (
    draw_geojson_rd,
    find_best_zoom,
    geojson_to_rd,
    get_bounds_rd,
    get_center,
)
from openforms.utils.map.wmts_map_generator import WMTSMapGenerator

from ..typing import AddressNLComponent, Component, MapComponent
from .base import FormatterBase


class DateFormatter(FormatterBase):
    def format(self, component: Component, value: date | None) -> str:
        return fmt_date(value)


class DateTimeFormatter(FormatterBase):
    def format(self, component: Component, value: datetime | None) -> str:
        return f"{fmt_date(value)} {fmt_time(value, 'H:i')}"


type MapValue = PointGeometry | LineStringGeometry | PolygonGeometry


class MapFormatter(FormatterBase):
    def format(self, component: MapComponent, value: MapValue) -> str:
        if self.as_html:
            tile_layer = MapTileLayer.objects.get(
                identifier=component["tileLayerIdentifier"]
            )

            geojson_rd = geojson_to_rd(value)
            bounds = get_bounds_rd(geojson_rd)
            x_rd, y_rd = get_center(geojson_rd)

            image_size_px = (718, 500)

            zoom = find_best_zoom(bounds, image_size_px=image_size_px)

            map_img = WMTSMapGenerator.make_map_rd(
                url_template=tile_layer.url,
                x_rd=x_rd,
                y_rd=y_rd,
                zoom=zoom,
                img_size=image_size_px,
            )

            draw_geojson_rd(
                map_img,
                geojson_rd,
                zoom=zoom,
                img_size=image_size_px,
                center_x_rd=x_rd,
                center_y_rd=y_rd,
            )

            png_array = BytesIO()
            map_img.save(png_array, format="png")
            encoded = base64.b64encode(png_array.getvalue()).decode()
            img_data_uri = f"data:image/png;base64,{encoded}"

            return format_html("<img src='{}'>", img_data_uri)

        # use a comma here since its a single data element
        if coordinates := value.get("coordinates"):
            return ", ".join(str(x) for x in coordinates)
        else:
            return ""


class AddressValue(TypedDict):
    """
    Redefined, as the BRK structure is converted to snake_case.

    The Formio data is not transformed, and it stays camelCased. So while it's the same
    data, the shape is different.
    """

    postcode: str
    houseNumber: str
    houseLetter: NotRequired[str]
    houseNumberAddition: NotRequired[str]
    city: NotRequired[str]
    streetName: NotRequired[str]
    secretStreetCity: NotRequired[str]


class AddressNLFormatter(FormatterBase):
    empty_values = ({},)

    def format(self, component: AddressNLComponent, value: AddressValue) -> str:
        value = value.copy()
        value.setdefault("houseLetter", "")
        value.setdefault("houseNumberAddition", "")
        value.setdefault("city", "")
        value.setdefault("streetName", "")

        short_template = "{postcode} {houseNumber}{houseLetter} {houseNumberAddition}"
        full_template = (
            "{streetName} {houseNumber}{houseLetter} {houseNumberAddition}"
            "{sep}{postcode} {city}"
        )

        # setdefault doesn't narrow it for the type checker :(
        assert "city" in value
        assert "streetName" in value
        template = (
            full_template if (value["city"] or value["streetName"]) else short_template
        )

        if self.as_html:
            sep = mark_safe("<br>")
            return format_html(template, sep=sep, **value)

        return template.format(sep="\n", **value).strip()


class CosignFormatter(FormatterBase):
    def format(self, component: Component, value: str) -> str:
        return str(value)
