from maykin_common.pdf import UrlFetcher
from weasyprint import HTML

from openforms.api.geojson import PointGeometry
from openforms.config.models import MapTileLayer
from openforms.formio.formatters.custom import MapFormatter, MapValue
from openforms.formio.typing import MapComponent
from openforms.utils.pdf import render_to_pdf, get_base_url, convert_html_to_pdf
from django.test import TestCase


class ASDF(TestCase):
    def test_generate_pdf(self):
        MapTileLayer.objects.create(
            label="BRT",
            url="https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0/standaard/EPSG:28992/{z}/{x}/{y}.png",
        )

        component: MapComponent = {
            "type": "map",
            "key": "map",
            "tileLayerIdentifier": "brt",
        }
        value: PointGeometry = {
            "type": "Point",
            "coordinates": (4.893164274470299, 52.36673378967122),
        }
        formatter = MapFormatter(as_html=True)

        map_html = formatter.format(component, value)

        # Example base64 PNG (tiny red dot)
        html_content = f"""
        <!DOCTYPE html>
        <html>
          <body>
            {map_html}
          </body>
        </html>
        """

        # Generate PDF
        pdf = convert_html_to_pdf(html_content)
        with open("output.pdf", "wb") as f:
            f.write(pdf)
