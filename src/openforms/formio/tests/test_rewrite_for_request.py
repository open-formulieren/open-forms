from unittest.mock import Mock, patch

from django.test import TestCase

from rest_framework.test import APIRequestFactory

from openforms.config.models import GlobalConfiguration
from openforms.config.tests.factories import MapTileLayerFactory
from openforms.formio.components.custom import Map
from openforms.formio.registry import ComponentRegistry

rf = APIRequestFactory()


class RewriteForRequestTests(TestCase):
    @patch("openforms.formio.components.vanilla.GlobalConfiguration.get_solo")
    def test_map_without_use_config_default_map_settings(self, m_solo: Mock):
        m_solo.return_value = GlobalConfiguration(
            form_map_default_zoom_level="8",
            form_map_default_latitude="55.123",
            form_map_default_longitude="56.456",
        )

        component = {
            "type": "map",
            "defaultZoom": "3",
            "initialCenter": {
                "lat": "43.23",
                "lng": "41.23",
            },
            "useConfigDefaultMapSettings": False,
        }

        register = ComponentRegistry()
        register("map")(Map)
        request = rf.get("/dummy")
        register.update_config_for_request(component, request)

        expected = {
            "type": "map",
            "defaultZoom": "3",
            "initialCenter": {
                "lat": "43.23",
                "lng": "41.23",
            },
            "useConfigDefaultMapSettings": False,
        }
        self.assertEqual(component, expected)

    @patch("openforms.formio.components.vanilla.GlobalConfiguration.get_solo")
    def test_map_with_use_config_default_map_settings(self, m_solo: Mock):
        m_solo.return_value = GlobalConfiguration(
            form_map_default_zoom_level="8",
            form_map_default_latitude="55.123",
            form_map_default_longitude="56.456",
        )

        component = {
            "type": "map",
            "defaultZoom": "3",
            "initialCenter": {
                "lat": "43.23",
                "lng": "41.23",
            },
            "useConfigDefaultMapSettings": True,
        }

        register = ComponentRegistry()
        register("map")(Map)
        request = rf.get("/dummy")
        register.update_config_for_request(component, request)

        expected = {
            "type": "map",
            "defaultZoom": "8",
            "initialCenter": {
                "lat": "55.123",
                "lng": "56.456",
            },
            "useConfigDefaultMapSettings": True,
        }
        self.assertEqual(component, expected)

    def test_map_without_tile_layer_identifier(self):
        component = {
            "type": "map",
            "defaultZoom": "3",
            "initialCenter": {
                "lat": "43.23",
                "lng": "41.23",
            },
            "useConfigDefaultMapSettings": False,
            "tileLayerIdentifier": None,
        }

        register = ComponentRegistry()
        register("map")(Map)
        request = rf.get("/dummy")
        register.update_config_for_request(component, request)

        expected = {
            "type": "map",
            "defaultZoom": "3",
            "initialCenter": {
                "lat": "43.23",
                "lng": "41.23",
            },
            "useConfigDefaultMapSettings": False,
            "tileLayerIdentifier": None,
        }
        self.assertEqual(component, expected)

    def test_map_with_invalid_tile_layer_identifier(self):
        component = {
            "type": "map",
            "defaultZoom": "3",
            "initialCenter": {
                "lat": "43.23",
                "lng": "41.23",
            },
            "useConfigDefaultMapSettings": False,
            "tileLayerIdentifier": "",
        }

        register = ComponentRegistry()
        register("map")(Map)
        request = rf.get("/dummy")
        register.update_config_for_request(component, request)

        expected = {
            "type": "map",
            "defaultZoom": "3",
            "initialCenter": {
                "lat": "43.23",
                "lng": "41.23",
            },
            "useConfigDefaultMapSettings": False,
            "tileLayerIdentifier": "",
        }
        self.assertEqual(component, expected)

    def test_map_with_valid_unknown_tile_layer_identifier(self):
        component = {
            "type": "map",
            "defaultZoom": "3",
            "initialCenter": {
                "lat": "43.23",
                "lng": "41.23",
            },
            "useConfigDefaultMapSettings": False,
            "tileLayerIdentifier": "identifier",
        }

        register = ComponentRegistry()
        register("map")(Map)
        request = rf.get("/dummy")
        register.update_config_for_request(component, request)

        expected = {
            "type": "map",
            "defaultZoom": "3",
            "initialCenter": {
                "lat": "43.23",
                "lng": "41.23",
            },
            "useConfigDefaultMapSettings": False,
            "tileLayerIdentifier": "identifier",
        }
        self.assertEqual(component, expected)

    def test_map_with_valid_known_tile_layer_identifier(self):
        map = MapTileLayerFactory.create(identifier="identifier")
        component = {
            "type": "map",
            "defaultZoom": "3",
            "initialCenter": {
                "lat": "43.23",
                "lng": "41.23",
            },
            "useConfigDefaultMapSettings": False,
            "tileLayerIdentifier": "identifier",
        }

        register = ComponentRegistry()
        register("map")(Map)
        request = rf.get("/dummy")
        register.update_config_for_request(component, request)

        expected = {
            "type": "map",
            "defaultZoom": "3",
            "initialCenter": {
                "lat": "43.23",
                "lng": "41.23",
            },
            "useConfigDefaultMapSettings": False,
            "tileLayerIdentifier": "identifier",
            "tileLayerUrl": map.url,
        }
        self.assertEqual(component, expected)

    @patch("openforms.formio.components.vanilla.GlobalConfiguration.get_solo")
    def test_map_with_valid_known_tile_layer_identifier_and_use_config_default_map_settings(
        self, m_solo: Mock
    ):
        m_solo.return_value = GlobalConfiguration(
            form_map_default_zoom_level="8",
            form_map_default_latitude="55.123",
            form_map_default_longitude="56.456",
        )
        map = MapTileLayerFactory.create(identifier="identifier")
        component = {
            "type": "map",
            "defaultZoom": "3",
            "initialCenter": {
                "lat": "43.23",
                "lng": "41.23",
            },
            "useConfigDefaultMapSettings": True,
            "tileLayerIdentifier": "identifier",
        }

        register = ComponentRegistry()
        register("map")(Map)
        request = rf.get("/dummy")
        register.update_config_for_request(component, request)

        expected = {
            "type": "map",
            "defaultZoom": "8",
            "initialCenter": {
                "lat": "55.123",
                "lng": "56.456",
            },
            "useConfigDefaultMapSettings": True,
            "tileLayerIdentifier": "identifier",
            "tileLayerUrl": map.url,
        }
        self.assertEqual(component, expected)
