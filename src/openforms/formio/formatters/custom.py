# TODO implement: iban, bsn, postcode, licenseplate, npFamilyMembers, cosign
from collections.abc import Mapping
from datetime import date, datetime
from typing import ClassVar, NotRequired, TypedDict

from django.template.defaultfilters import date as fmt_date, time as fmt_time
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from formio_types import (
    BSN,
    AddressNL,
    CosignV2,
    CustomerProfile,
    Date,
    DateTime,
    Map,
    Postcode,
)
from geo_visualization import generate_map_image_with_geojson
from openforms.api.geojson import LineStringGeometry, PointGeometry, PolygonGeometry
from openforms.config.models import MapTileLayer
from openforms.typing import StrOrPromise

from ..typing.custom import DigitalAddress, SupportedChannels
from .base import FormatterBase

MAP_IMAGE_SIZE = (400, 300)  # width and height in number of pixels
# With the above image size, this zoom level gives sufficient map context around a point
# to draw
MAX_ZOOM_LEVEL = 12


class PostcodeFormatter(FormatterBase[Postcode]):
    def format(self, component: Postcode, value: str) -> str:
        return str(value)


class BSNFormatter(FormatterBase[BSN]):
    def format(self, component: BSN, value: str) -> str:
        return str(value)


class DateFormatter(FormatterBase[Date]):
    def format(self, component: Date, value: date | None) -> str:
        return fmt_date(value)


class DateTimeFormatter(FormatterBase[DateTime]):
    def format(self, component: DateTime, value: datetime | None) -> str:
        return f"{fmt_date(value)} {fmt_time(value, 'H:i')}"


type MapValue = PointGeometry | LineStringGeometry | PolygonGeometry


class MapFormatter(FormatterBase[Map]):
    def format(self, component: Map, value: MapValue) -> str:
        # Will be an empty string if `value` was empty
        coordinates = ", ".join(str(x) for x in value.get("coordinates", []))
        overlays = component.overlays

        if not self.as_html or not coordinates:
            return coordinates

        # Note that "brt" is a default fixture from default_map_tile_layers.json
        tile_layer = MapTileLayer.objects.get(
            identifier=component.tile_layer_identifier or "brt",
        )
        image = generate_map_image_with_geojson(
            value,
            tile_layer.url,
            MAP_IMAGE_SIZE,
            overlays=[
                {
                    "type": overlay.type,
                    "url": overlay.url,
                    "layers": overlay.layers,
                }
                for overlay in overlays
            ]
            if overlays
            else None,
            max_zoom=MAX_ZOOM_LEVEL,
        )

        # Fallback to the coordinates if it couldn't be loaded
        if image is None:
            return coordinates

        return format_html(
            '<img src="data:image/png;base64,{image}" alt="{text}" style="max-width: 100%;"/>',
            image=image,
            text=coordinates,
        )


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


class AddressNLFormatter(FormatterBase[AddressNL]):
    empty_values = ({},)

    def format(self, component: AddressNL, value: AddressValue) -> str:
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


class CosignFormatter(FormatterBase[CosignV2]):
    def format(self, component: CosignV2, value: str) -> str:
        return str(value)


class CustomerProfileFormatter(FormatterBase[CustomerProfile]):
    ADDRESS_TYPE_LABELS: ClassVar[Mapping[SupportedChannels, StrOrPromise]] = {
        "email": _("email address"),
        "phoneNumber": _("phone number"),
    }

    def format(self, component: CustomerProfile, value: list[DigitalAddress]) -> str:
        # Gather all filled-in addresses and possibly add "as preferred" suffix
        addresses: list[str] = [
            _("{address} (will become preferred {address_type})").format(
                address=address["address"],
                address_type=self.ADDRESS_TYPE_LABELS[address["type"]],
            )
            if address.get("preferenceUpdate") == "isNewPreferred"
            else address["address"]
            for address in value
            if address["address"] != ""
        ]
        if len(addresses) == 0:
            return ""

        if not self.as_html:
            return self.multiple_separator.join(addresses)

        return format_html(
            "<ul>{values}</ul>",
            values=format_html_join(
                "",
                "<li>{}</li>",
                ((address,) for address in addresses),
            ),
        )
