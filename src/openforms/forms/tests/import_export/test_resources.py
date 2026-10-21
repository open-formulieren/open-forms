from django.test import TestCase

import tablib

from openforms.authentication.contrib.yivi_oidc.models import AttributeGroup
from openforms.authentication.tests.factories import AttributeGroupFactory
from openforms.config.models import MapTileLayer, MapWMSTileLayer
from openforms.config.tests.factories import (
    MapTileLayerFactory,
    MapWMSTileLayerFactory,
)
from openforms.products.models import Product
from openforms.products.tests.factories import ProductFactory

from ...import_export.resources import (
    ProductResource,
    WMSTileLayerResource,
    WMTSTileLayerResource,
    YiviAttributeGroupResource,
)
from ...tests.factories import FormFactory


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

        # No product is used in the form, so the dataset should be empty
        self.assertEqual(len(dataset), 0)

    def test_import_product_with_same_identifier(self):
        product = ProductFactory.create(
            uuid="20523058-a69b-4d8e-b58d-b6a9291e3b66",
            name="product",
            price=10,
            information="product information",
        )

        # Create a dataset with the same UUID, but with different product information
        dataset = tablib.Dataset(
            (
                "20523058-a69b-4d8e-b58d-b6a9291e3b66",
                "product 2",
                "15,00",
                "different product information",
            ),
            headers=["uuid", "name", "price", "information"],
        )

        results = ProductResource().import_data(dataset)

        self.assertEqual(len(results.rows), 1)
        result = results.rows[0]

        # The result should point to the product with the same UUID
        self.assertTrue(result.is_skip())
        self.assertEqual(result.instance, product)

        # No new products have been created
        self.assertEqual(Product.objects.count(), 1)

    def test_import_product_with_different_identifier_but_same_configuration(self):
        product = ProductFactory.create(
            uuid="20523058-a69b-4d8e-b58d-b6a9291e3b66",
            name="product",
            price=10,
            information="product information",
        )

        # Create a dataset with a different UUID, but with the same product information
        dataset = tablib.Dataset(
            (
                "a29744bd-f30b-46ed-9677-30f55d767f14",
                "product",
                "10,00",
                "product information",
            ),
            headers=["uuid", "name", "price", "information"],
        )

        results = ProductResource().import_data(dataset)

        self.assertEqual(len(results.rows), 1)
        result = results.rows[0]

        # The result should point to the product with the same configuration
        self.assertTrue(result.is_skip())
        self.assertEqual(result.instance, product)

        # No new products have been created
        self.assertEqual(Product.objects.count(), 1)

    def test_import_product_with_different_identifier_and_configuration(self):
        product = ProductFactory.create(
            uuid="20523058-a69b-4d8e-b58d-b6a9291e3b66",
            name="product",
            price=10,
            information="product information",
        )

        # Create a dataset with a different UUID and product information
        dataset = tablib.Dataset(
            (
                "a29744bd-f30b-46ed-9677-30f55d767f14",
                "product 2",
                "15,00",
                "different product information",
            ),
            headers=["uuid", "name", "price", "information"],
        )

        results = ProductResource().import_data(dataset)

        self.assertEqual(len(results.rows), 1)
        result = results.rows[0]

        # The result does not point to any existing product
        self.assertTrue(result.is_new())
        self.assertNotEqual(result.instance, product)

        # A new product has been created
        self.assertEqual(Product.objects.count(), 2)

    def test_import_product_with_missing_fields_in_configuration(self):
        dataset = tablib.Dataset(
            ("a29744bd-f30b-46ed-9677-30f55d767f14",),
            headers=["uuid"],
        )

        results = ProductResource().import_data(dataset)
        result = results.rows[0]

        # Expect the import to have failed due to the invalid data in the configuration
        self.assertTrue(result.is_error())
        assert len(result.errors) == 1
        self.assertEqual(
            result.errors[0].error.args[0],
            "Column 'name' not found in dataset. Available columns are: ['uuid']",
        )

    def test_import_product_with_unknown_field_in_configuration(self):
        # There shouldn't be any products yet
        self.assertFalse(Product.objects.exists())

        dataset = tablib.Dataset(
            (
                "a29744bd-f30b-46ed-9677-30f55d767f14",
                "product",
                "15,00",
                "product information",
                "unknown field value",
            ),
            headers=["uuid", "name", "price", "information", "unknown_field"],
        )

        results = ProductResource().import_data(dataset)
        result = results.rows[0]

        self.assertTrue(result.is_new())

        # A new product has been created
        self.assertEqual(Product.objects.count(), 1)


class WMSTileLayerResourceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # Make sure we start with a clean slate
        MapWMSTileLayer.objects.all().delete()

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

        # No WMS tile layer is used in the form, so the dataset should be empty
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

        # No WMS tile layer is used in the form, so the dataset should be empty
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

        # No WMTS tile layer is used in the form, so the dataset should be empty
        self.assertEqual(len(dataset), 0)

    def test_import_wms_tile_layer_with_same_identifier(self):
        tile_layer = MapWMSTileLayerFactory.create(
            uuid="20523058-a69b-4d8e-b58d-b6a9291e3b66",
            name="tile layer",
            url="http://example.com",
        )

        # Create a dataset with the same UUID, but with different tile layer information
        dataset = tablib.Dataset(
            (
                "20523058-a69b-4d8e-b58d-b6a9291e3b66",
                "different layer",
                "http://different.com",
            ),
            headers=["uuid", "name", "url"],
        )

        results = WMSTileLayerResource().import_data(dataset)

        self.assertEqual(len(results.rows), 1)
        result = results.rows[0]

        # The result should represent the tile layer with the same UUID
        self.assertTrue(result.is_skip())
        self.assertEqual(result.instance, tile_layer)

        # No new tile layers have been created
        self.assertEqual(MapWMSTileLayer.objects.count(), 1)

    def test_import_wms_tile_layer_with_different_identifier_but_same_configuration(
        self,
    ):
        tile_layer = MapWMSTileLayerFactory.create(
            uuid="20523058-a69b-4d8e-b58d-b6a9291e3b66",
            name="tile layer",
            url="http://example.com",
        )

        # Create a dataset with a different UUID, but with the same tile layer information
        dataset = tablib.Dataset(
            (
                "670596d5-8ce3-4b97-b4a4-bd1c05516c4a",
                "tile layer",
                "http://example.com",
            ),
            headers=["uuid", "name", "url"],
        )

        results = WMSTileLayerResource().import_data(dataset)

        self.assertEqual(len(results.rows), 1)
        result = results.rows[0]

        # The result should represent the tile layer with the same information
        self.assertTrue(result.is_skip())
        self.assertEqual(result.instance, tile_layer)

        # No new tile layers have been created
        self.assertEqual(MapWMSTileLayer.objects.count(), 1)

    def test_import_wms_tile_layer_with_different_identifier_and_configuration(self):
        tile_layer = MapWMSTileLayerFactory.create(
            uuid="20523058-a69b-4d8e-b58d-b6a9291e3b66",
            name="tile layer",
            url="http://example.com",
        )

        # Create a dataset with a different UUID and tile layer information
        dataset = tablib.Dataset(
            (
                "670596d5-8ce3-4b97-b4a4-bd1c05516c4a",
                "different layer",
                "http://different.com",
            ),
            headers=["uuid", "name", "url"],
        )

        results = WMSTileLayerResource().import_data(dataset)

        self.assertEqual(len(results.rows), 1)
        result = results.rows[0]

        # The result does not represent any existing tile layer
        self.assertTrue(result.is_new())
        self.assertNotEqual(result.instance, tile_layer)

        # A new tile layer has been created
        self.assertEqual(MapWMSTileLayer.objects.count(), 2)

    def test_import_wms_tile_layer_with_missing_fields_in_configuration(self):
        dataset = tablib.Dataset(
            ("670596d5-8ce3-4b97-b4a4-bd1c05516c4a",),
            headers=["uuid"],
        )

        results = WMSTileLayerResource().import_data(dataset)
        result = results.rows[0]

        # Expect the import to have failed due to the invalid data in the configuration
        self.assertTrue(result.is_error())
        assert len(result.errors) == 1
        self.assertEqual(
            result.errors[0].error.args[0],
            "Column 'name' not found in dataset. Available columns are: ['uuid']",
        )

    def test_import_wms_tile_layer_with_unknown_field_in_configuration(self):
        # There shouldn't be any wms tile layers yet
        self.assertFalse(MapWMSTileLayer.objects.exists())

        dataset = tablib.Dataset(
            (
                "670596d5-8ce3-4b97-b4a4-bd1c05516c4a",
                "layer",
                "http://layer.com",
                "unknown field value",
            ),
            headers=["uuid", "name", "url", "unknown_field"],
        )

        results = WMSTileLayerResource().import_data(dataset)
        result = results.rows[0]

        self.assertTrue(result.is_new())

        # A new tile layer has been created
        self.assertEqual(MapWMSTileLayer.objects.count(), 1)


class WMTSTileLayerResourceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # Make sure we start with a clean slate
        MapTileLayer.objects.all().delete()

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

        # No WMTS tile layer is used in the form, so the dataset should be empty
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

        # No WMTS tile layer is used in the form, so the dataset should be empty
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

        # No map component in the form, so the WMTS dataset should be empty
        self.assertEqual(len(dataset), 0)

    def test_import_wmts_tile_layer_with_same_identifier(self):
        background_layer = MapTileLayerFactory.create(
            identifier="background-layer",
            label="background layer",
            url="http://example.com",
        )

        # Create a dataset with the same identifier, but with different tile layer information
        dataset = tablib.Dataset(
            (
                "background-layer",
                "different background layer",
                "http://different.com",
            ),
            headers=["identifier", "label", "url"],
        )

        results = WMTSTileLayerResource().import_data(dataset)

        self.assertEqual(len(results.rows), 1)
        result = results.rows[0]

        # The result should represent the tile layer with the same identifier
        self.assertTrue(result.is_skip())
        self.assertEqual(result.instance, background_layer)

        # No new tile layers have been created
        self.assertEqual(MapTileLayer.objects.count(), 1)

    def test_import_wmts_tile_layer_with_different_identifier_but_same_configuration(
        self,
    ):
        background_layer = MapTileLayerFactory.create(
            identifier="background-layer",
            label="background layer",
            url="http://example.com",
        )

        # Create a dataset with a different identifier, but with the same tile layer information
        dataset = tablib.Dataset(
            (
                "different-background-layer",
                "background layer",
                "http://example.com",
            ),
            headers=["identifier", "label", "url"],
        )

        results = WMTSTileLayerResource().import_data(dataset)

        self.assertEqual(len(results.rows), 1)
        result = results.rows[0]

        # The result should represent the tile layer with the same information
        self.assertTrue(result.is_skip())
        self.assertEqual(result.instance, background_layer)

        # No new tile layers have been created
        self.assertEqual(MapTileLayer.objects.count(), 1)

    def test_import_wmts_tile_layer_with_different_identifier_and_configuration(self):
        background_layer = MapTileLayerFactory.create(
            identifier="background-layer",
            label="background layer",
            url="http://example.com",
        )

        # Create a dataset with a different identifier and tile layer information
        dataset = tablib.Dataset(
            (
                "different-background-layer",
                "different background layer",
                "http://different.com",
            ),
            headers=["identifier", "label", "url"],
        )

        results = WMTSTileLayerResource().import_data(dataset)

        self.assertEqual(len(results.rows), 1)
        result = results.rows[0]

        # The result does not represent any existing tile layer
        self.assertTrue(result.is_new())
        self.assertNotEqual(result.instance, background_layer)

        # A new tile layer has been created
        self.assertEqual(MapTileLayer.objects.count(), 2)

    def test_import_wmts_tile_layer_with_missing_fields_in_configuration(self):
        dataset = (
            tablib.Dataset(  # A dataset missing the expected 'label' and 'url' fields
                ("different-background-layer",),
                headers=["identifier"],
            )
        )

        results = WMTSTileLayerResource().import_data(dataset)
        result = results.rows[0]

        # Expect the import to have failed due to missing fields in the configuration
        self.assertTrue(result.is_error())
        assert len(result.errors) == 1
        self.assertEqual(
            result.errors[0].error.args[0],
            "Column 'label' not found in dataset. Available columns are: ['identifier']",
        )

    def test_import_wmts_tile_layer_with_unknown_field_in_configuration(self):
        # There shouldn't be any wmts tile layers yet
        self.assertFalse(MapTileLayer.objects.exists())

        dataset = tablib.Dataset(
            (
                "background-layer",
                "background layer",
                "http://different.com",
                "unknown field value",
            ),
            headers=["identifier", "label", "url", "unknown_field"],
        )

        results = WMTSTileLayerResource().import_data(dataset)
        result = results.rows[0]

        self.assertTrue(result.is_new())

        # A new tile layer has been created
        self.assertEqual(MapTileLayer.objects.count(), 1)


class YiviAttributeGroupResourceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # Make sure we start with a clean slate
        AttributeGroup.objects.all().delete()

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

        # No yivi attribute groups are used in the form, so the dataset should be empty
        self.assertEqual(len(dataset), 0)

    def test_export_for_form_without_yivi_auth_backend(self):
        # An unused attribute group that should not be included in the dataset
        AttributeGroupFactory.create()
        form = FormFactory.create(authentication_backend="demo")

        dataset = YiviAttributeGroupResource().export_for_form(form).dict

        # No Yivi authentication backend is used in the form, so the dataset should  be
        # empty
        self.assertEqual(len(dataset), 0)

    def test_import_yivi_attribute_group_with_same_identifier(self):
        attribute_group = AttributeGroupFactory.create(
            uuid="670596d5-8ce3-4b97-b4a4-bd1c05516c4a",
            name="base attributes",
            description="some basic yivi attributes",
            attributes=["firstname", "lastname"],
        )

        # Create a dataset with the same identifier, but with different attribute group information
        dataset = tablib.Dataset(
            (
                "670596d5-8ce3-4b97-b4a4-bd1c05516c4a",
                "additional attributes",
                "",
                "DOB",
            ),
            headers=["uuid", "name", "description", "attributes"],
        )

        results = YiviAttributeGroupResource().import_data(dataset)

        self.assertEqual(len(results.rows), 1)
        result = results.rows[0]

        # The result should represent the attribute group with the same identifier
        self.assertTrue(result.is_skip())
        self.assertEqual(result.instance, attribute_group)

        # No new attribute groups have been created
        self.assertEqual(AttributeGroup.objects.count(), 1)

    def test_import_yivi_attribute_group_with_different_identifier_but_same_configuration(
        self,
    ):
        attribute_group = AttributeGroupFactory.create(
            uuid="670596d5-8ce3-4b97-b4a4-bd1c05516c4a",
            name="base attributes",
            description="some basic yivi attributes",
            attributes=["firstname", "lastname"],
        )

        # Create a dataset with a different identifier, but with the same attribute group information
        dataset = tablib.Dataset(
            (
                "79623448-fa11-4d86-91c5-0e2a5cd617ac",
                "base attributes",
                "some basic yivi attributes",
                "firstname,lastname",
            ),
            headers=["uuid", "name", "description", "attributes"],
        )

        results = YiviAttributeGroupResource().import_data(dataset)

        self.assertEqual(len(results.rows), 1)
        result = results.rows[0]

        # The result should represent the attribute group with the same information
        self.assertTrue(result.is_skip())
        self.assertEqual(result.instance, attribute_group)

        # No new attribute groups have been created
        self.assertEqual(AttributeGroup.objects.count(), 1)

    def test_import_yivi_attribute_group_with_different_identifier_and_configuration(
        self,
    ):
        attribute_group = AttributeGroupFactory.create(
            uuid="670596d5-8ce3-4b97-b4a4-bd1c05516c4a",
            name="base attributes",
            description="some basic yivi attributes",
            attributes=["firstname", "lastname"],
        )

        # Create a dataset with a different identifier and attribute group information
        dataset = tablib.Dataset(
            (
                "79623448-fa11-4d86-91c5-0e2a5cd617ac",
                "additional attributes",
                "",
                "DOB",
            ),
            headers=["uuid", "name", "description", "attributes"],
        )

        results = YiviAttributeGroupResource().import_data(dataset)

        self.assertEqual(len(results.rows), 1)
        result = results.rows[0]

        # The result should not represent any existing attribute group
        self.assertTrue(result.is_new())
        self.assertNotEqual(result.instance, attribute_group)

        # A new attribute group has been created
        self.assertEqual(AttributeGroup.objects.count(), 2)

    def test_import_yivi_attribute_group_with_missing_fields_in_configuration(self):
        dataset = tablib.Dataset(
            ("79623448-fa11-4d86-91c5-0e2a5cd617ac",),
            headers=["uuid"],
        )

        results = YiviAttributeGroupResource().import_data(dataset)
        result = results.rows[0]

        # Expect the import to have failed due to the invalid data in the configuration
        self.assertTrue(result.is_error())
        assert len(result.errors) == 1
        self.assertEqual(
            result.errors[0].error.args[0],
            "Column 'name' not found in dataset. Available columns are: ['uuid']",
        )

    def test_import_yivi_attribute_group_with_unknown_field_in_configuration(self):
        # There shouldn't be any attribute groups yet
        self.assertFalse(AttributeGroup.objects.exists())

        dataset = tablib.Dataset(
            (
                "79623448-fa11-4d86-91c5-0e2a5cd617ac",
                "additional attributes",
                "",
                "DOB",
                "unknown field value",
            ),
            headers=["uuid", "name", "description", "attributes", "unknown_field"],
        )

        results = YiviAttributeGroupResource().import_data(dataset)
        result = results.rows[0]

        self.assertTrue(result.is_new())

        # A new attribute group has been created
        self.assertEqual(AttributeGroup.objects.count(), 1)
