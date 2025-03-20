# TODO implement: iban, bsn, postcode, licenseplate, npFamilyMembers, cosign
from datetime import date
from typing import NotRequired, TypedDict

from django.template.defaultfilters import date as fmt_date, time as fmt_time
from django.utils.dateparse import parse_date, parse_datetime
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from openforms.api.geojson import LineStringGeometry, PointGeometry, PolygonGeometry

from ..typing import AddressNLComponent, Component, MapComponent
from .base import FormatterBase
# from ...utils.map import generate_cartopy_map
import base64
import datetime
from io import BytesIO
from ...utils.wmts_map_generator import WMTSMapGenerator


class DateFormatter(FormatterBase):
    def format(self, component: Component, value: str | date | None) -> str:
        if isinstance(value, str):
            value = parse_date(value)
        return fmt_date(value)


class DateTimeFormatter(FormatterBase):
    def format(self, component: Component, value: str) -> str:
        parsed_value = parse_datetime(value)
        return f"{fmt_date(parsed_value)} {fmt_time(parsed_value, 'H:i')}"


type MapValue = PointGeometry | LineStringGeometry | PolygonGeometry


class MapFormatter(FormatterBase):
    def format(self, component: MapComponent, value: MapValue) -> str:
        if self.as_html:
            start_time = datetime.datetime.now()
            map_img = WMTSMapGenerator.make_map(
                url_template="https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0/standaard/EPSG:28992/{z}/{x}/{y}.png", # noqa
                # lat=52.0870974,
                lat=52.3628026,
                lon=4.9075201,
                zoom=17,
                img_size=[648, 250]
            )
            # cartopy_map = generate_cartopy_map(
            #     value, component.get("tileLayerIdentifier")
            # )

            png_array = BytesIO()
            print(map_img)
            map_img.save(png_array, format='png')
            encoded = base64.b64encode(png_array.getvalue()).decode("utf-8")
            img_data_uri = 'data:image/png;base64,{}'.format(encoded)
            end_time = datetime.datetime.now()
            print(end_time - start_time)

            return format_html("<img src='{}'>", img_data_uri)

        # use a comma here since its a single data element
        if coordinates := value.get("coordinates"):
            return ", ".join((str(x) for x in coordinates))
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
