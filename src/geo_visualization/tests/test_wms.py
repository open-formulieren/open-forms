import os
from io import BytesIO
from unittest import TestCase
from unittest.mock import patch

from django.core.cache import cache

from maykin_common.vcr import VCRMixin
from PIL import Image
from shapely.geometry import Point

from .. import Overlay
from ..overlays_draw import draw_overlays_on_map
from ..wms import VersionError


@patch.dict(os.environ, {"_MAP_GENERATION_MAX_WORKERS": "1"})
class WMSDrawTests(VCRMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cache.clear()
        cls.addClassCleanup(cache.clear)

    def test_map_with_wms(self):
        image = Image.new("RGBA", (10, 10))
        center = Point((113872, 486763))
        overlays: list[Overlay] = [
            {
                "url": "https://service.pdok.nl/lv/bag/wms/v2_0?request=getCapabilities&service=WMS",
                "type": "wms",
                "layers": ["pand"],
            },
        ]

        draw_overlays_on_map(
            image=image,
            overlays=overlays,
            center_rd=center,
            zoom=13,
        )

        stream = BytesIO()
        image.save(stream, "png")
        expected = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\n\x00\x00\x00\n\x08\x06"
            b"\x00\x00\x00\x8d2\xcf\xbd\x00\x00\x00]IDATx\x9ccd@\x02<<<\x9annn'KKKyYYY"
            b"\x91\xa5\x18\x98\x909_\xbe|\xb9\xbek\xd7.\x8b\x9e\x9e\x9e\xcf\xbf\x7f\xff"
            b"\xc6\xad\x10\xaa\xf8\xda\xce\x9d;\xb1*\xc6\nxxx\xb4\x82\x83\x83?\x1d?~"
            b"\xfc\xff\x993g\xfe\x13\xad\x98X\x93?\x13v\x03T1Q\ni\x03\x00\xc6@+\xac\xd3"
            b"\x18l[\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        self.assertEqual(stream.getvalue(), expected)

    def test_with_non_existing_layer(self):
        image = Image.new("RGBA", (10, 10))
        center = Point((113872, 486763))
        overlays: list[Overlay] = [
            {
                "url": "https://service.pdok.nl/lv/bag/wms/v2_0?request=getCapabilities&service=WMS",
                "type": "wms",
                "layers": ["fake_layer"],
            },
        ]

        draw_overlays_on_map(
            image=image,
            overlays=overlays,
            center_rd=center,
            zoom=12,
        )

        stream = BytesIO()
        image.save(stream, "png")
        # Should just be the empty image
        expected = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\n\x00\x00\x00\n\x08\x06"
            b"\x00\x00\x00\x8d2\xcf\xbd\x00\x00\x00\x0eIDATx\x9cc`\x18\x05\x83\x13\x00"
            b"\x00\x01\x9a\x00\x01\x1d\x82V\xa8\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        self.assertEqual(stream.getvalue(), expected)

    def test_invalid_url(self):
        image = Image.new("RGBA", (256, 256))
        center = Point((113872, 486763))
        overlays: list[Overlay] = [
            {
                "url": "https://google.nl",
                "type": "wms",
                "layers": ["fake_layer"],
            },
        ]

        with self.assertRaises(VersionError):
            draw_overlays_on_map(
                image=image,
                overlays=overlays,
                center_rd=center,
                zoom=12,
            )
