from unittest.mock import Mock, patch

from django.test import TestCase

from rest_framework.test import APIRequestFactory

from openforms.config.models import GlobalConfiguration
from openforms.config.tests.factories import (
    MapTileLayerFactory,
    MapWFSTileLayerFactory,
    MapWMSTileLayerFactory,
)
from openforms.formio.datastructures import FormioConfigurationWrapper
from openforms.formio.dynamic_config import (
    rewrite_formio_components,
    rewrite_formio_components_for_request,
)
from openforms.submissions.tests.factories import SubmissionFactory

rf = APIRequestFactory()


class DynamicConfigTests(TestCase):
    @patch("openforms.formio.components.vanilla.GlobalConfiguration.get_solo")
    def test_map_without_default_map_config(self, m_solo: Mock):
        m_solo.return_value = GlobalConfiguration(
            form_map_default_zoom_level=8,
            form_map_default_latitude=55.123,
            form_map_default_longitude=56.456,
        )

        configuration = {
            "components": [
                {
                    "type": "map",
                    "key": "map",
                    "defaultZoom": 3,
                    "initialCenter": {
                        "lat": 43.23,
                        "lng": 41.23,
                    },
                    "useConfigDefaultMapSettings": False,
                }
            ]
        }
        formio_configuration = FormioConfigurationWrapper(configuration)
        submission = SubmissionFactory.create()
        rewrite_formio_components(formio_configuration, submission)

        request = rf.get("/dummy")
        rewrite_formio_components_for_request(formio_configuration, request)

        expected = {
            "type": "map",
            "key": "map",
            "defaultZoom": 3,
            "initialCenter": {
                "lat": 43.23,
                "lng": 41.23,
            },
            "useConfigDefaultMapSettings": False,
        }
        self.assertEqual(configuration["components"][0], expected)

    @patch("openforms.formio.components.vanilla.GlobalConfiguration.get_solo")
    def test_map_with_default_map_config(self, m_solo: Mock):
        m_solo.return_value = GlobalConfiguration(
            form_map_default_zoom_level=8,
            form_map_default_latitude=55.123,
            form_map_default_longitude=56.456,
        )

        configuration = {
            "components": [
                {
                    "type": "map",
                    "key": "map",
                    "defaultZoom": 3,
                    "initialCenter": {
                        "lat": 43.23,
                        "lng": 41.23,
                    },
                    "useConfigDefaultMapSettings": True,
                }
            ]
        }
        formio_configuration = FormioConfigurationWrapper(configuration)
        submission = SubmissionFactory.create()
        rewrite_formio_components(formio_configuration, submission)

        request = rf.get("/dummy")
        rewrite_formio_components_for_request(formio_configuration, request)

        expected = {
            "type": "map",
            "key": "map",
            "defaultZoom": 8,
            "initialCenter": {
                "lat": 55.123,
                "lng": 56.456,
            },
            "useConfigDefaultMapSettings": True,
        }
        self.assertEqual(configuration["components"][0], expected)

    def test_map_without_tile_layer_identifier(self):
        configuration = {
            "components": [
                {
                    "type": "map",
                    "key": "map",
                    "defaultZoom": 3,
                    "initialCenter": {
                        "lat": 43.23,
                        "lng": 41.23,
                    },
                    "useConfigDefaultMapSettings": False,
                    "tileLayerIdentifier": None,
                }
            ]
        }
        formio_configuration = FormioConfigurationWrapper(configuration)
        submission = SubmissionFactory.create()
        rewrite_formio_components(formio_configuration, submission)

        request = rf.get("/dummy")
        rewrite_formio_components_for_request(formio_configuration, request)

        expected = {
            "type": "map",
            "key": "map",
            "defaultZoom": 3,
            "initialCenter": {
                "lat": 43.23,
                "lng": 41.23,
            },
            "useConfigDefaultMapSettings": False,
            "tileLayerIdentifier": None,
        }
        self.assertEqual(configuration["components"][0], expected)

    def test_map_with_invalid_tile_layer_identifier(self):
        configuration = {
            "components": [
                {
                    "type": "map",
                    "key": "map",
                    "defaultZoom": 3,
                    "initialCenter": {
                        "lat": 43.23,
                        "lng": 41.23,
                    },
                    "useConfigDefaultMapSettings": False,
                    "tileLayerIdentifier": "",
                }
            ]
        }
        formio_configuration = FormioConfigurationWrapper(configuration)
        submission = SubmissionFactory.create()
        rewrite_formio_components(formio_configuration, submission)

        request = rf.get("/dummy")
        rewrite_formio_components_for_request(formio_configuration, request)

        expected = {
            "type": "map",
            "key": "map",
            "defaultZoom": 3,
            "initialCenter": {
                "lat": 43.23,
                "lng": 41.23,
            },
            "useConfigDefaultMapSettings": False,
            "tileLayerIdentifier": "",
        }
        self.assertEqual(configuration["components"][0], expected)

    def test_map_with_valid_unknown_tile_layer_identifier(self):
        configuration = {
            "components": [
                {
                    "type": "map",
                    "key": "map",
                    "defaultZoom": 3,
                    "initialCenter": {
                        "lat": 43.23,
                        "lng": 41.23,
                    },
                    "useConfigDefaultMapSettings": False,
                    "tileLayerIdentifier": "identifier",
                }
            ]
        }
        formio_configuration = FormioConfigurationWrapper(configuration)
        submission = SubmissionFactory.create()
        rewrite_formio_components(formio_configuration, submission)

        request = rf.get("/dummy")
        rewrite_formio_components_for_request(formio_configuration, request)

        expected = {
            "type": "map",
            "key": "map",
            "defaultZoom": 3,
            "initialCenter": {
                "lat": 43.23,
                "lng": 41.23,
            },
            "useConfigDefaultMapSettings": False,
            "tileLayerIdentifier": "identifier",
        }
        self.assertEqual(configuration["components"][0], expected)

    def test_map_with_valid_known_tile_layer_identifier(self):
        map = MapTileLayerFactory.create(identifier="identifier")
        configuration = {
            "components": [
                {
                    "type": "map",
                    "key": "map",
                    "defaultZoom": 3,
                    "initialCenter": {
                        "lat": 43.23,
                        "lng": 41.23,
                    },
                    "useConfigDefaultMapSettings": False,
                    "tileLayerIdentifier": "identifier",
                }
            ]
        }
        formio_configuration = FormioConfigurationWrapper(configuration)
        submission = SubmissionFactory.create()
        rewrite_formio_components(formio_configuration, submission)

        request = rf.get("/dummy")
        rewrite_formio_components_for_request(formio_configuration, request)

        expected = {
            "type": "map",
            "key": "map",
            "defaultZoom": 3,
            "initialCenter": {
                "lat": 43.23,
                "lng": 41.23,
            },
            "useConfigDefaultMapSettings": False,
            "tileLayerIdentifier": "identifier",
            "tileLayerUrl": map.url,
        }
        self.assertEqual(configuration["components"][0], expected)

    @patch("openforms.formio.components.vanilla.GlobalConfiguration.get_solo")
    def test_map_with_valid_known_tile_layer_identifier_and_use_config_default_map_settings(
        self, m_solo: Mock
    ):
        m_solo.return_value = GlobalConfiguration(
            form_map_default_zoom_level=8,
            form_map_default_latitude=55.123,
            form_map_default_longitude=56.456,
        )
        map = MapTileLayerFactory.create(identifier="identifier")
        configuration = {
            "components": [
                {
                    "type": "map",
                    "key": "map",
                    "defaultZoom": 3,
                    "initialCenter": {
                        "lat": 43.23,
                        "lng": 41.23,
                    },
                    "useConfigDefaultMapSettings": True,
                    "tileLayerIdentifier": "identifier",
                }
            ]
        }
        formio_configuration = FormioConfigurationWrapper(configuration)
        submission = SubmissionFactory.create()
        rewrite_formio_components(formio_configuration, submission)

        request = rf.get("/dummy")
        rewrite_formio_components_for_request(formio_configuration, request)

        expected = {
            "type": "map",
            "key": "map",
            "defaultZoom": 8,
            "initialCenter": {
                "lat": 55.123,
                "lng": 56.456,
            },
            "useConfigDefaultMapSettings": True,
            "tileLayerIdentifier": "identifier",
            "tileLayerUrl": map.url,
        }
        self.assertEqual(configuration["components"][0], expected)

    def test_map_with_known_WMS_overlay(self):
        MapWMSTileLayerFactory.create(
            uuid="1266c027-9a18-4ecb-8a9e-6acddf7e74f3", url="https://example.wms.com"
        )
        configuration = {
            "components": [
                {
                    "type": "map",
                    "key": "map",
                    "defaultZoom": 3,
                    "initialCenter": {
                        "lat": 43.23,
                        "lng": 41.23,
                    },
                    "overlays": [
                        {
                            "type": "wms",
                            "uuid": "1266c027-9a18-4ecb-8a9e-6acddf7e74f3",
                            "name": "My first overlay",
                            "layers": ["layer1", "layer2"],
                        }
                    ],
                }
            ]
        }

        formio_configuration = FormioConfigurationWrapper(configuration)
        submission = SubmissionFactory.create()
        rewrite_formio_components(formio_configuration, submission)

        request = rf.get("/dummy")
        rewrite_formio_components_for_request(formio_configuration, request)

        # Expect that the overlay has the "url" attribute with the value of the WMS tile
        # layer url.
        expected = {
            "type": "map",
            "key": "map",
            "defaultZoom": 3,
            "initialCenter": {
                "lat": 43.23,
                "lng": 41.23,
            },
            "overlays": [
                {
                    "type": "wms",
                    "uuid": "1266c027-9a18-4ecb-8a9e-6acddf7e74f3",
                    "name": "My first overlay",
                    "layers": ["layer1", "layer2"],
                    "url": "https://example.wms.com",
                }
            ],
        }
        self.assertEqual(configuration["components"][0], expected)

    def test_map_with_unknown_WMS_overlay(self):
        configuration = {
            "components": [
                {
                    "type": "map",
                    "key": "map",
                    "defaultZoom": 3,
                    "initialCenter": {
                        "lat": 43.23,
                        "lng": 41.23,
                    },
                    "overlays": [
                        {
                            "type": "wms",
                            # Some unknown uuid
                            "uuid": "44c9ee90-96a3-4ac2-bb55-f2f42b547b15",
                            "name": "My first overlay",
                            "layers": ["layer1", "layer2"],
                        }
                    ],
                }
            ]
        }

        formio_configuration = FormioConfigurationWrapper(configuration)
        submission = SubmissionFactory.create()
        rewrite_formio_components(formio_configuration, submission)

        request = rf.get("/dummy")
        rewrite_formio_components_for_request(formio_configuration, request)

        # Expect that the invalid overlay is removed from the component.
        expected = {
            "type": "map",
            "key": "map",
            "defaultZoom": 3,
            "initialCenter": {
                "lat": 43.23,
                "lng": 41.23,
            },
            "overlays": [],
        }
        self.assertEqual(configuration["components"][0], expected)

    def test_map_with_known_WFS_overlay(self):
        MapWFSTileLayerFactory.create(
            uuid="1266c027-9a18-4ecb-8a9e-6acddf7e74f3", url="https://example.wfs.com"
        )
        configuration = {
            "components": [
                {
                    "type": "map",
                    "key": "map",
                    "defaultZoom": 3,
                    "initialCenter": {
                        "lat": 43.23,
                        "lng": 41.23,
                    },
                    "overlays": [
                        {
                            "type": "wfs",
                            "uuid": "1266c027-9a18-4ecb-8a9e-6acddf7e74f3",
                            "name": "My first overlay",
                            "layers": ["layer1", "layer2"],
                        }
                    ],
                }
            ]
        }

        formio_configuration = FormioConfigurationWrapper(configuration)
        submission = SubmissionFactory.create()
        rewrite_formio_components(formio_configuration, submission)

        request = rf.get("/dummy")
        rewrite_formio_components_for_request(formio_configuration, request)

        # Expect that the overlay has the "url" attribute with the value of the WFS tile
        # layer url.
        expected = {
            "type": "map",
            "key": "map",
            "defaultZoom": 3,
            "initialCenter": {
                "lat": 43.23,
                "lng": 41.23,
            },
            "overlays": [
                {
                    "type": "wfs",
                    "uuid": "1266c027-9a18-4ecb-8a9e-6acddf7e74f3",
                    "name": "My first overlay",
                    "layers": ["layer1", "layer2"],
                    "url": "https://example.wfs.com",
                }
            ],
        }
        self.assertEqual(configuration["components"][0], expected)

    def test_map_with_unknown_WFS_overlay(self):
        configuration = {
            "components": [
                {
                    "type": "map",
                    "key": "map",
                    "defaultZoom": 3,
                    "initialCenter": {
                        "lat": 43.23,
                        "lng": 41.23,
                    },
                    "overlays": [
                        {
                            "type": "wfs",
                            # Some unknown uuid
                            "uuid": "44c9ee90-96a3-4ac2-bb55-f2f42b547b15",
                            "name": "My first overlay",
                            "layers": ["layer1", "layer2"],
                        }
                    ],
                }
            ]
        }

        formio_configuration = FormioConfigurationWrapper(configuration)
        submission = SubmissionFactory.create()
        rewrite_formio_components(formio_configuration, submission)

        request = rf.get("/dummy")
        rewrite_formio_components_for_request(formio_configuration, request)

        # Expect that the invalid overlay is removed from the component.
        expected = {
            "type": "map",
            "key": "map",
            "defaultZoom": 3,
            "initialCenter": {
                "lat": 43.23,
                "lng": 41.23,
            },
            "overlays": [],
        }
        self.assertEqual(configuration["components"][0], expected)
