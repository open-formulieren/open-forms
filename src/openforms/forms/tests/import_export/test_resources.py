from django.test import TestCase

from openforms.authentication.tests.factories import AttributeGroupFactory
from openforms.config.tests.factories import (
    MapTileLayerFactory,
    MapWMSTileLayerFactory,
)
from openforms.forms.tests.factories import FormFactory
from openforms.products.tests.factories import ProductFactory

from ...import_export.resources import (
    ProductResource,
    WMSTileLayerResource,
    WMTSTileLayerResource,
    YiviAttributeGroupResource,
)


class ProductResourceTests(TestCase):
    def test_export_for_form(self):
        product = ProductFactory.create()
        # An unused product that should not be included in the dataset
        ProductFactory.create()
        form = FormFactory.create(product=product)

        dataset = ProductResource().export_for_form(form).dict

        self.assertEqual(len(dataset), 1)

        # Only the product explicitly assigned to the form should be in the dataset
        self.assertEqual(dataset[0]["uuid"], str(product.uuid))
        self.assertEqual(dataset[0]["name"], product.name)
        self.assertEqual(
            dataset[0]["price"],
            str(product.price).replace(".", ","),
        )
        self.assertEqual(dataset[0]["information"], product.information)

    def test_export_for_form_without_product(self):
        # An unused product that should not be included in the dataset
        ProductFactory.create()
        form = FormFactory.create(product=None)

        dataset = ProductResource().export_for_form(form).dict

        self.assertEqual(len(dataset), 0)


class WMSTileLayerResourceTests(TestCase):
    def test_export_for_form(self):
        wms_tile_layer1 = MapWMSTileLayerFactory.create()
        wms_tile_layer2 = MapWMSTileLayerFactory.create()
        # An unused WMS tile layer that should not be included in the dataset
        MapWMSTileLayerFactory.create()
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "label": "Map",
                        "key": "map",
                        "type": "map",
                        "useConfigDefaultMapSettings": False,
                        "interactions": {
                            "marker": True,
                            "polygon": False,
                            "polyline": False,
                        },
                        "overlays": [
                            {
                                "url": "",
                                "type": "wms",
                                "uuid": str(wms_tile_layer1.uuid),
                                "label": "Overlay 1",
                                "layers": ["layer1"],
                            },
                            {
                                "url": "",
                                "type": "wms",
                                "uuid": str(wms_tile_layer2.uuid),
                                "label": "Overlay 2",
                                "layers": ["layer2"],
                            },
                        ],
                    },
                ],
            },
        )

        dataset = WMSTileLayerResource().export_for_form(form).dict

        self.assertEqual(len(dataset), 2)

        # Only the WMS tile layers that are used by the form should be in the dataset
        self.assertEqual(dataset[0]["uuid"], str(wms_tile_layer1.uuid))
        self.assertEqual(dataset[0]["name"], wms_tile_layer1.name)
        self.assertEqual(dataset[0]["url"], wms_tile_layer1.url)

        self.assertEqual(dataset[1]["uuid"], str(wms_tile_layer2.uuid))
        self.assertEqual(dataset[1]["name"], wms_tile_layer2.name)
        self.assertEqual(dataset[1]["url"], wms_tile_layer2.url)

    def test_export_for_form_with_broken_overlay(self):
        # An unused WMS tile layer that should not be included in the dataset
        MapWMSTileLayerFactory.create()

        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "label": "Map",
                        "key": "map",
                        "type": "map",
                        "useConfigDefaultMapSettings": False,
                        "interactions": {
                            "marker": True,
                            "polygon": False,
                            "polyline": False,
                        },
                        "overlays": [
                            # This is some weird configuration without the UUID, but
                            # technically valid.
                            {
                                "url": "",
                                "type": "wms",
                                "uuid": "",
                                "label": "Overlay 1",
                                "layers": ["layer1"],
                            },
                        ],
                    },
                ],
            },
        )

        dataset = WMSTileLayerResource().export_for_form(form).dict

        self.assertEqual(len(dataset), 0)

    def test_export_for_form_without_overlays(self):
        # An unused WMS tile layer that should not be included in the dataset
        MapWMSTileLayerFactory.create()

        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "label": "Map",
                        "key": "map",
                        "type": "map",
                        "useConfigDefaultMapSettings": False,
                        "interactions": {
                            "marker": True,
                            "polygon": False,
                            "polyline": False,
                        },
                    },
                ],
            },
        )

        dataset = WMSTileLayerResource().export_for_form(form).dict

        self.assertEqual(len(dataset), 0)

    def test_export_for_form_with_multiple_map_component(self):
        wms_tile_layer1 = MapWMSTileLayerFactory.create()
        wms_tile_layer2 = MapWMSTileLayerFactory.create()
        wms_tile_layer3 = MapWMSTileLayerFactory.create()
        # An unused WMS tile layer that should not be included in the dataset
        MapWMSTileLayerFactory.create()

        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "label": "Map",
                        "key": "map",
                        "type": "map",
                        "useConfigDefaultMapSettings": False,
                        "interactions": {
                            "marker": True,
                            "polygon": False,
                            "polyline": False,
                        },
                        "overlays": [
                            {
                                "url": "",
                                "type": "wms",
                                "uuid": str(wms_tile_layer1.uuid),
                                "label": "Overlay 1",
                                "layers": [],
                            },
                            {
                                "url": "",
                                "type": "wms",
                                "uuid": str(wms_tile_layer2.uuid),
                                "label": "Overlay 2",
                                "layers": [],
                            },
                        ],
                    },
                    {
                        "label": "Map 2",
                        "key": "map2",
                        "type": "map",
                        "useConfigDefaultMapSettings": False,
                        "interactions": {
                            "marker": True,
                            "polygon": False,
                            "polyline": False,
                        },
                        "overlays": [
                            {
                                "url": "",
                                "type": "wms",
                                "uuid": str(wms_tile_layer2.uuid),
                                "label": "Overlay 2",
                                "layers": [],
                            },
                            {
                                "url": "",
                                "type": "wms",
                                "uuid": str(wms_tile_layer3.uuid),
                                "label": "Overlay 3",
                                "layers": [],
                            },
                        ],
                    },
                ],
            },
        )

        dataset = WMSTileLayerResource().export_for_form(form).dict

        # The dataset should contain three entries, one for each unique tile layer
        self.assertEqual(len(dataset), 3)

        # Only the WMS tile layers that are used by the form should be in the dataset
        self.assertEqual(dataset[0]["uuid"], str(wms_tile_layer1.uuid))
        self.assertEqual(dataset[0]["name"], wms_tile_layer1.name)
        self.assertEqual(dataset[0]["url"], wms_tile_layer1.url)

        self.assertEqual(dataset[1]["uuid"], str(wms_tile_layer2.uuid))
        self.assertEqual(dataset[1]["name"], wms_tile_layer2.name)
        self.assertEqual(dataset[1]["url"], wms_tile_layer2.url)

        self.assertEqual(dataset[2]["uuid"], str(wms_tile_layer3.uuid))
        self.assertEqual(dataset[2]["name"], wms_tile_layer3.name)
        self.assertEqual(dataset[2]["url"], wms_tile_layer3.url)

    def test_export_for_form_without_map_component(self):
        # An unused WMS tile layer that should not be included in the dataset
        MapWMSTileLayerFactory.create()
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "label": "Textfield",
                        "key": "textfield",
                        "type": "textfield",
                    },
                ],
            },
        )

        # This should not cause any errors
        dataset = WMSTileLayerResource().export_for_form(form).dict

        self.assertEqual(len(dataset), 0)


class WMTSTileLayerResourceTests(TestCase):
    def test_export_for_form(self):
        wmts_tile_layer = MapTileLayerFactory.create()
        # An unused WMTS tile layer that should not be included in the dataset
        MapTileLayerFactory.create()
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "label": "Map",
                        "key": "map",
                        "type": "map",
                        "useConfigDefaultMapSettings": False,
                        "interactions": {
                            "marker": True,
                            "polygon": False,
                            "polyline": False,
                        },
                        "tileLayerIdentifier": wmts_tile_layer.identifier,
                    },
                ],
            },
        )

        dataset = WMTSTileLayerResource().export_for_form(form).dict

        self.assertEqual(len(dataset), 1)

        self.assertEqual(dataset[0]["identifier"], wmts_tile_layer.identifier)
        self.assertEqual(dataset[0]["label"], wmts_tile_layer.label)
        self.assertEqual(dataset[0]["url"], wmts_tile_layer.url)

    def test_export_for_form_with_empty_tile_layer_identifier(self):
        # An unused WMTS tile layer that should not be included in the dataset
        MapTileLayerFactory.create()
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "label": "Map",
                        "key": "map",
                        "type": "map",
                        "useConfigDefaultMapSettings": False,
                        "interactions": {
                            "marker": True,
                            "polygon": False,
                            "polyline": False,
                        },
                        "tileLayerIdentifier": "",
                    },
                ],
            },
        )

        dataset = WMTSTileLayerResource().export_for_form(form).dict

        self.assertEqual(len(dataset), 0)

    def test_export_for_form_without_tile_layer_identifier(self):
        # An unused WMTS tile layer that should not be included in the dataset
        MapTileLayerFactory.create()
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "label": "Map",
                        "key": "map",
                        "type": "map",
                        "useConfigDefaultMapSettings": False,
                        "interactions": {
                            "marker": True,
                            "polygon": False,
                            "polyline": False,
                        },
                    },
                ],
            },
        )

        dataset = WMTSTileLayerResource().export_for_form(form).dict

        self.assertEqual(len(dataset), 0)

    def test_export_for_form_with_multiple_map_component(self):
        wmts_tile_layer = MapTileLayerFactory.create(identifier="wmts_layer_1")
        wmts_tile_layer2 = MapTileLayerFactory.create(identifier="wmts_layer_2")
        # An unused WMTS tile layer that should not be included in the dataset
        MapTileLayerFactory.create()

        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "label": "Map",
                        "key": "map",
                        "type": "map",
                        "useConfigDefaultMapSettings": False,
                        "interactions": {
                            "marker": True,
                            "polygon": False,
                            "polyline": False,
                        },
                        "tileLayerIdentifier": wmts_tile_layer.identifier,
                    },
                    {
                        "label": "Map 2",
                        "key": "map2",
                        "type": "map",
                        "useConfigDefaultMapSettings": False,
                        "interactions": {
                            "marker": True,
                            "polygon": False,
                            "polyline": False,
                        },
                        "tileLayerIdentifier": wmts_tile_layer2.identifier,
                    },
                ],
            },
        )

        dataset = WMTSTileLayerResource().export_for_form(form).dict
        dataset = sorted(dataset, key=lambda item: item["identifier"])

        self.assertEqual(len(dataset), 2)

        self.assertEqual(dataset[0]["identifier"], wmts_tile_layer.identifier)
        self.assertEqual(dataset[0]["label"], wmts_tile_layer.label)
        self.assertEqual(dataset[0]["url"], wmts_tile_layer.url)

        self.assertEqual(dataset[1]["identifier"], wmts_tile_layer2.identifier)
        self.assertEqual(dataset[1]["label"], wmts_tile_layer2.label)
        self.assertEqual(dataset[1]["url"], wmts_tile_layer2.url)

    def test_export_for_form_without_map_component(self):
        # An unused WMTS tile layer that should not be included in the dataset
        MapTileLayerFactory.create()
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "label": "Textfield",
                        "key": "textfield",
                        "type": "textfield",
                    },
                ],
            },
        )

        dataset = WMTSTileLayerResource().export_for_form(form).dict

        self.assertEqual(len(dataset), 0)


class YiviAttributeGroupResourceTests(TestCase):
    def test_export_for_form(self):
        yivi_attribute_group = AttributeGroupFactory.create(
            attributes=["first_name", "last_name"]
        )
        yivi_attribute_group2 = AttributeGroupFactory.create(
            attributes=["some_other_attribute"]
        )
        # An unused attribute group that should not be included in the dataset
        AttributeGroupFactory.create()
        form = FormFactory.create(
            authentication_backend="yivi_oidc",
            authentication_backend__options={
                "additional_attributes_groups": [
                    yivi_attribute_group.uuid,
                    yivi_attribute_group2.uuid,
                ],
            },
        )

        dataset = YiviAttributeGroupResource().export_for_form(form).dict

        self.assertEqual(len(dataset), 2)

        # The two used attribute groups should be included in the dataset
        self.assertEqual(dataset[0]["uuid"], str(yivi_attribute_group.uuid))
        self.assertEqual(dataset[0]["name"], yivi_attribute_group.name)
        self.assertEqual(dataset[0]["description"], yivi_attribute_group.description)
        self.assertEqual(
            dataset[0]["attributes"], ",".join(yivi_attribute_group.attributes)
        )

        self.assertEqual(dataset[1]["uuid"], str(yivi_attribute_group2.uuid))
        self.assertEqual(dataset[1]["name"], yivi_attribute_group2.name)
        self.assertEqual(dataset[1]["description"], yivi_attribute_group2.description)
        self.assertEqual(
            dataset[1]["attributes"], ",".join(yivi_attribute_group2.attributes)
        )

    def test_export_for_form_without_resource(self):
        # An unused attribute group that should not be included in the dataset
        AttributeGroupFactory.create()
        form = FormFactory.create(authentication_backend="yivi_oidc")

        dataset = YiviAttributeGroupResource().export_for_form(form).dict

        self.assertEqual(len(dataset), 0)

    def test_export_for_form_without_yivi_auth_backend(self):
        # An unused attribute group that should not be included in the dataset
        AttributeGroupFactory.create()
        form = FormFactory.create(authentication_backend="demo")

        dataset = YiviAttributeGroupResource().export_for_form(form).dict

        # As there is no Yivi authentication backend, the dataset should be empty
        self.assertEqual(len(dataset), 0)
