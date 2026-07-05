from django.test import TestCase

from openforms.authentication.tests.factories import AttributeGroupFactory
from openforms.config.tests.factories import (
    MapTileLayerFactory,
    MapWMSTileLayerFactory,
)
from openforms.forms.import_export.resources import (
    ProductResource,
    WMSTileLayerResource,
    WMTSTileLayerResource,
    YiviAttributeGroupResource,
)
from openforms.forms.tests.factories import FormFactory
from openforms.products.tests.factories import ProductFactory


class ProductResourceTests(TestCase):
    def test_export_for_form(self):
        product = ProductFactory.create()
        form = FormFactory.create(product=product)

        dataset = ProductResource().export_for_form(form).dict

        self.assertEqual(len(dataset), 1)
        self.assertEqual(dataset[0]["uuid"], str(product.uuid))
        self.assertEqual(dataset[0]["name"], product.name)
        self.assertEqual(
            dataset[0]["price"],
            str(product.price).replace(".", ","),
        )
        self.assertEqual(dataset[0]["information"], product.information)

    def test_export_for_form_without_product(self):
        form = FormFactory.create(product=None)

        dataset = ProductResource().export_for_form(form).dict

        self.assertEqual(len(dataset), 0)


class WMSTileLayerResourceTests(TestCase):
    def test_export_for_form(self):
        wms_tile_layer1 = MapWMSTileLayerFactory.create()
        wms_tile_layer2 = MapWMSTileLayerFactory.create()
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

        self.assertEqual(dataset[0]["uuid"], str(wms_tile_layer1.uuid))
        self.assertEqual(dataset[0]["name"], wms_tile_layer1.name)
        self.assertEqual(dataset[0]["url"], wms_tile_layer1.url)

        self.assertEqual(dataset[1]["uuid"], str(wms_tile_layer2.uuid))
        self.assertEqual(dataset[1]["name"], wms_tile_layer2.name)
        self.assertEqual(dataset[1]["url"], wms_tile_layer2.url)

    def test_export_for_form_with_broken_overlay(self):
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


class WMTSTileLayerResourceTests(TestCase):
    def test_export_for_form(self):
        wmts_tile_layer = MapTileLayerFactory.create()
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


class YiviAttributeGroupResourceTests(TestCase):
    def test_export_for_form(self):
        yivi_attribute_group = AttributeGroupFactory.create(
            attributes=["first_name", "last_name"]
        )
        form = FormFactory.create(
            authentication_backend="yivi_oidc",
            authentication_backend__options={
                "additional_attributes_groups": [yivi_attribute_group.uuid],
            },
        )

        dataset = YiviAttributeGroupResource().export_for_form(form).dict

        self.assertEqual(len(dataset), 1)

        self.assertEqual(dataset[0]["uuid"], str(yivi_attribute_group.uuid))
        self.assertEqual(dataset[0]["name"], yivi_attribute_group.name)
        self.assertEqual(dataset[0]["description"], yivi_attribute_group.description)
        self.assertEqual(
            dataset[0]["attributes"], ",".join(yivi_attribute_group.attributes)
        )

    def test_export_for_form_without_resource(self):
        form = FormFactory.create(authentication_backend="yivi_oidc")

        dataset = YiviAttributeGroupResource().export_for_form(form).dict

        self.assertEqual(len(dataset), 0)

    def test_export_for_form_without_yivi_auth_backend(self):
        form = FormFactory.create(authentication_backend="demo")

        dataset = YiviAttributeGroupResource().export_for_form(form).dict

        self.assertEqual(len(dataset), 0)
