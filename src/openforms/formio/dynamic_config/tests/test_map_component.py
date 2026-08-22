from unittest.mock import Mock, patch

from django.test import TestCase

from rest_framework.test import APIRequestFactory

from formio_types import Map
from openforms.config.models import GlobalConfiguration
from openforms.config.tests.factories import MapTileLayerFactory, MapWMSTileLayerFactory
from openforms.submissions.tests.factories import SubmissionFactory

from ...datastructures import FormioConfig
from ...dynamic_config import (
    rewrite_formio_components,
    rewrite_formio_components_for_request,
)
from ...typing import MapComponent

rf = APIRequestFactory()


class DynamicConfigTests(TestCase):
    maxDiff = None

    @patch("openforms.formio.components.vanilla.GlobalConfiguration.get_solo")
    def test_map_without_default_map_config(self, m_solo: Mock):
        m_solo.return_value = GlobalConfiguration(
            form_map_default_zoom_level=8,
            form_map_default_latitude=55.123,
            form_map_default_longitude=56.456,
        )
        component: MapComponent = {
            "type": "map",
            "key": "map",
            "label": "map",
            "defaultZoom": 3,
            "initialCenter": {
                "lat": 43.23,
                "lng": 41.23,
            },
            "useConfigDefaultMapSettings": False,
            "interactions": {"marker": True, "polyline": False, "polygon": False},
        }
        config = FormioConfig(name="<test>", components=[component])
        submission = SubmissionFactory.create()
        rewrite_formio_components(config, submission)

        request = rf.get("/dummy")
        rewrite_formio_components_for_request(config, request)

        updated_component = config["map"]
        assert isinstance(updated_component, Map)
        self.assertEqual(updated_component.default_zoom, 3)
        assert updated_component.initial_center is not None
        self.assertEqual(updated_component.initial_center.lat, 43.23)
        self.assertEqual(updated_component.initial_center.lng, 41.23)

    @patch("openforms.formio.components.vanilla.GlobalConfiguration.get_solo")
    def test_map_with_default_map_config(self, m_solo: Mock):
        m_solo.return_value = GlobalConfiguration(
            form_map_default_zoom_level=8,
            form_map_default_latitude=55.123,
            form_map_default_longitude=56.456,
        )
        component: MapComponent = {
            "type": "map",
            "key": "map",
            "label": "map",
            "defaultZoom": 3,
            "initialCenter": {
                "lat": 43.23,
                "lng": 41.23,
            },
            "useConfigDefaultMapSettings": True,
            "interactions": {"marker": True, "polyline": False, "polygon": False},
        }
        config = FormioConfig(name="<test>", components=[component])
        submission = SubmissionFactory.create()
        rewrite_formio_components(config, submission)

        request = rf.get("/dummy")
        rewrite_formio_components_for_request(config, request)

        updated_component = config["map"]
        assert isinstance(updated_component, Map)
        self.assertEqual(updated_component.default_zoom, 8)
        assert updated_component.initial_center is not None
        self.assertEqual(updated_component.initial_center.lat, 55.123)
        self.assertEqual(updated_component.initial_center.lng, 56.456)

    def test_map_without_tile_layer_identifier(self):
        component: MapComponent = {
            "type": "map",
            "key": "map",
            "label": "map",
            "defaultZoom": 3,
            "initialCenter": {
                "lat": 43.23,
                "lng": 41.23,
            },
            "useConfigDefaultMapSettings": False,
            "interactions": {"marker": True, "polyline": False, "polygon": False},
        }
        config = FormioConfig(name="<test>", components=[component])
        submission = SubmissionFactory.create()
        rewrite_formio_components(config, submission)

        request = rf.get("/dummy")
        rewrite_formio_components_for_request(config, request)

        updated_component = config["map"]
        assert isinstance(updated_component, Map)
        self.assertIsNone(updated_component.tile_layer_identifier)
        self.assertIsNone(updated_component.tile_layer_url)

    def test_map_with_invalid_tile_layer_identifier(self):
        component: MapComponent = {
            "type": "map",
            "key": "map",
            "label": "map",
            "defaultZoom": 3,
            "initialCenter": {
                "lat": 43.23,
                "lng": 41.23,
            },
            "useConfigDefaultMapSettings": False,
            "tileLayerIdentifier": "",
            "interactions": {"marker": True, "polyline": False, "polygon": False},
        }
        config = FormioConfig(name="<test>", components=[component])
        submission = SubmissionFactory.create()
        rewrite_formio_components(config, submission)

        request = rf.get("/dummy")
        rewrite_formio_components_for_request(config, request)

        updated_component = config["map"]
        assert isinstance(updated_component, Map)
        self.assertEqual(updated_component.tile_layer_identifier, "")
        self.assertIsNone(updated_component.tile_layer_url)

    def test_map_with_valid_unknown_tile_layer_identifier(self):
        component: MapComponent = {
            "type": "map",
            "key": "map",
            "label": "map",
            "defaultZoom": 3,
            "initialCenter": {
                "lat": 43.23,
                "lng": 41.23,
            },
            "useConfigDefaultMapSettings": False,
            "tileLayerIdentifier": "identifier",
            "interactions": {"marker": True, "polyline": False, "polygon": False},
        }
        config = FormioConfig(name="<test>", components=[component])
        submission = SubmissionFactory.create()
        rewrite_formio_components(config, submission)

        request = rf.get("/dummy")
        rewrite_formio_components_for_request(config, request)

        updated_component = config["map"]
        assert isinstance(updated_component, Map)
        self.assertEqual(updated_component.tile_layer_identifier, "identifier")
        self.assertIsNone(updated_component.tile_layer_url)

    def test_map_with_valid_known_tile_layer_identifier(self):
        layer = MapTileLayerFactory.create(identifier="identifier")
        component: MapComponent = {
            "type": "map",
            "key": "map",
            "label": "map",
            "defaultZoom": 3,
            "initialCenter": {
                "lat": 43.23,
                "lng": 41.23,
            },
            "useConfigDefaultMapSettings": False,
            "tileLayerIdentifier": "identifier",
            "interactions": {"marker": True, "polyline": False, "polygon": False},
        }
        config = FormioConfig(name="<test>", components=[component])
        submission = SubmissionFactory.create()
        rewrite_formio_components(config, submission)

        request = rf.get("/dummy")
        rewrite_formio_components_for_request(config, request)

        updated_component = config["map"]
        assert isinstance(updated_component, Map)
        self.assertEqual(updated_component.tile_layer_identifier, "identifier")
        self.assertEqual(updated_component.tile_layer_url, layer.url)

    @patch("openforms.formio.components.vanilla.GlobalConfiguration.get_solo")
    def test_map_with_valid_known_tile_layer_identifier_and_use_config_default_map_settings(
        self, m_solo: Mock
    ):
        m_solo.return_value = GlobalConfiguration(
            form_map_default_zoom_level=8,
            form_map_default_latitude=55.123,
            form_map_default_longitude=56.456,
        )
        layer = MapTileLayerFactory.create(identifier="identifier")
        component: MapComponent = {
            "type": "map",
            "key": "map",
            "label": "map",
            "defaultZoom": 3,
            "initialCenter": {
                "lat": 43.23,
                "lng": 41.23,
            },
            "useConfigDefaultMapSettings": True,
            "tileLayerIdentifier": "identifier",
            "interactions": {"marker": True, "polyline": False, "polygon": False},
        }
        config = FormioConfig(name="<test>", components=[component])
        submission = SubmissionFactory.create()
        rewrite_formio_components(config, submission)

        request = rf.get("/dummy")
        rewrite_formio_components_for_request(config, request)

        updated_component = config["map"]
        assert isinstance(updated_component, Map)
        self.assertEqual(updated_component.default_zoom, 8)
        assert updated_component.initial_center is not None
        self.assertEqual(updated_component.initial_center.lat, 55.123)
        self.assertEqual(updated_component.initial_center.lng, 56.456)
        self.assertEqual(updated_component.tile_layer_identifier, "identifier")
        self.assertEqual(updated_component.tile_layer_url, layer.url)

    def test_map_with_known_WMS_overlay(self):
        MapWMSTileLayerFactory.create(
            uuid="1266c027-9a18-4ecb-8a9e-6acddf7e74f3", url="https://example.wms.com"
        )
        component: MapComponent = {
            "type": "map",
            "key": "map",
            "label": "map",
            "defaultZoom": 3,
            "initialCenter": {
                "lat": 43.23,
                "lng": 41.23,
            },
            "useConfigDefaultMapSettings": False,
            "interactions": {"marker": True, "polyline": False, "polygon": False},
            "overlays": [
                {
                    "type": "wms",
                    "uuid": "1266c027-9a18-4ecb-8a9e-6acddf7e74f3",
                    "label": "My first overlay",
                    "layers": ["layer1", "layer2"],
                }
            ],
        }

        config = FormioConfig(name="<test>", components=[component])
        submission = SubmissionFactory.create()
        rewrite_formio_components(config, submission)

        request = rf.get("/dummy")
        rewrite_formio_components_for_request(config, request)

        # Expect that the overlay has the "url" attribute with the value of the WMS tile
        # layer url.
        updated_component = config["map"]
        assert isinstance(updated_component, Map)
        assert updated_component.overlays is not None
        overlay = updated_component.overlays[0]
        self.assertEqual(overlay.url, "https://example.wms.com")

    def test_map_with_unknown_WMS_overlay(self):
        component: MapComponent = {
            "type": "map",
            "key": "map",
            "label": "map",
            "defaultZoom": 3,
            "initialCenter": {
                "lat": 43.23,
                "lng": 41.23,
            },
            "useConfigDefaultMapSettings": False,
            "interactions": {"marker": True, "polyline": False, "polygon": False},
            "overlays": [
                {
                    "type": "wms",
                    # Some unknown uuid
                    "uuid": "44c9ee90-96a3-4ac2-bb55-f2f42b547b15",
                    "label": "My first overlay",
                    "layers": ["layer1", "layer2"],
                }
            ],
        }

        config = FormioConfig(name="<test>", components=[component])
        submission = SubmissionFactory.create()
        rewrite_formio_components(config, submission)

        request = rf.get("/dummy")
        rewrite_formio_components_for_request(config, request)

        # Expect that the invalid overlay is removed from the component.
        updated_component = config["map"]
        assert isinstance(updated_component, Map)
        assert updated_component.overlays is not None
        self.assertEqual(updated_component.overlays, [])
