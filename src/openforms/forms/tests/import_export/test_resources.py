from django.test import TestCase

import tablib

from openforms.authentication.contrib.yivi_oidc.models import AttributeGroup
from openforms.authentication.tests.factories import AttributeGroupFactory
from openforms.config.models import MapTileLayer, MapWMSTileLayer
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
from openforms.products.models import Product
from openforms.products.tests.factories import ProductFactory


class ProductResourceExportTests(TestCase):
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


class ProductResourceImportTests(TestCase):
    def test_import_product_with_same_identifier(self):
        product = ProductFactory.create(
            uuid="20523058-a69b-4d8e-b58d-b6a9291e3b66",
            name="product",
            price=10,
            information="product information",
        )

        # Create a dataset with the same UUID, but with different product information
        dataset = tablib.Dataset(
            *[
                (
                    "20523058-a69b-4d8e-b58d-b6a9291e3b66",
                    "product 2",
                    "15,00",
                    "different product information",
                )
            ],
            headers=["uuid", "name", "price", "information"],
        )

        results = ProductResource().import_data(dataset)

        self.assertEqual(len(results.rows), 1)
        result = results.rows[0]

        # The result should represent the product with the same UUID
        self.assertEqual(result.is_skip(), True)
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
            *[
                (
                    "a29744bd-f30b-46ed-9677-30f55d767f14",
                    "product",
                    "10,00",
                    "product information",
                )
            ],
            headers=["uuid", "name", "price", "information"],
        )

        results = ProductResource().import_data(dataset)

        self.assertEqual(len(results.rows), 1)
        result = results.rows[0]

        # The result should represent the product with the same product information
        self.assertEqual(result.is_skip(), True)
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
            *[
                (
                    "a29744bd-f30b-46ed-9677-30f55d767f14",
                    "product 2",
                    "15,00",
                    "different product information",
                )
            ],
            headers=["uuid", "name", "price", "information"],
        )

        results = ProductResource().import_data(dataset)

        self.assertEqual(len(results.rows), 1)
        result = results.rows[0]

        # The result does not represent any existing product
        self.assertEqual(result.is_new(), True)
        self.assertNotEqual(result.instance, product)

        # A new product has been created
        self.assertEqual(Product.objects.count(), 2)


class WMSTileLayerResourceExportTests(TestCase):
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


class WMSTileLayerResourceImportTests(TestCase):
    def setUp(self):
        # Make sure we start with a clean slate
        MapWMSTileLayer.objects.all().delete()

    def test_import_wms_tile_layer_with_same_identifier(self):
        tile_layer = MapWMSTileLayerFactory.create(
            uuid="20523058-a69b-4d8e-b58d-b6a9291e3b66",
            name="tile layer",
            url="http://example.com",
        )

        # Create a dataset with the same UUID, but with different tile layer information
        dataset = tablib.Dataset(
            *[
                (
                    "20523058-a69b-4d8e-b58d-b6a9291e3b66",
                    "different layer",
                    "http://different.com",
                )
            ],
            headers=["uuid", "name", "url"],
        )

        results = WMSTileLayerResource().import_data(dataset)

        self.assertEqual(len(results.rows), 1)
        result = results.rows[0]

        # The result should represent the tile layer with the same UUID
        self.assertEqual(result.is_skip(), True)
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
            *[
                (
                    "670596d5-8ce3-4b97-b4a4-bd1c05516c4a",
                    "tile layer",
                    "http://example.com",
                )
            ],
            headers=["uuid", "name", "url"],
        )

        results = WMSTileLayerResource().import_data(dataset)

        self.assertEqual(len(results.rows), 1)
        result = results.rows[0]

        # The result should represent the tile layer with the same information
        self.assertEqual(result.is_skip(), True)
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
            *[
                (
                    "670596d5-8ce3-4b97-b4a4-bd1c05516c4a",
                    "different layer",
                    "http://different.com",
                )
            ],
            headers=["uuid", "name", "url"],
        )

        results = WMSTileLayerResource().import_data(dataset)

        self.assertEqual(len(results.rows), 1)
        result = results.rows[0]

        # The result does not represent any existing tile layer
        self.assertEqual(result.is_new(), True)
        self.assertNotEqual(result.instance, tile_layer)

        # A new tile layer has been created
        self.assertEqual(MapWMSTileLayer.objects.count(), 2)


class WMTSTileLayerExportResourceTests(TestCase):
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


class WMSTTileLayerResourceImportTests(TestCase):
    def setUp(self):
        # Make sure we start with a clean slate
        MapTileLayer.objects.all().delete()

    def test_import_wmts_tile_layer_with_same_identifier(self):
        background_layer = MapTileLayerFactory.create(
            identifier="background-layer",
            label="background layer",
            url="http://example.com",
        )

        # Create a dataset with the same identifier, but with different tile layer information
        dataset = tablib.Dataset(
            *[
                (
                    "background-layer",
                    "different background layer",
                    "http://different.com",
                )
            ],
            headers=["identifier", "label", "url"],
        )

        results = WMTSTileLayerResource().import_data(dataset)

        self.assertEqual(len(results.rows), 1)
        result = results.rows[0]

        # The result should represent the tile layer with the same identifier
        self.assertEqual(result.is_skip(), True)
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
            *[
                (
                    "different-background-layer",
                    "background layer",
                    "http://example.com",
                )
            ],
            headers=["identifier", "label", "url"],
        )

        results = WMTSTileLayerResource().import_data(dataset)

        self.assertEqual(len(results.rows), 1)
        result = results.rows[0]

        # The result should represent the tile layer with the same information
        self.assertEqual(result.is_skip(), True)
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
            *[
                (
                    "different-background-layer",
                    "different background layer",
                    "http://different.com",
                )
            ],
            headers=["identifier", "label", "url"],
        )

        results = WMTSTileLayerResource().import_data(dataset)

        self.assertEqual(len(results.rows), 1)
        result = results.rows[0]

        # The result does not represent any existing tile layer
        self.assertEqual(result.is_new(), True)
        self.assertNotEqual(result.instance, background_layer)

        # A new tile layer has been created
        self.assertEqual(MapTileLayer.objects.count(), 2)


class YiviAttributeGroupResourceExportTests(TestCase):
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


class YiviAttributeGroupResourceImportTests(TestCase):
    def setUp(self):
        # Make sure we start with a clean slate
        AttributeGroup.objects.all().delete()

    def test_import_yivi_attribute_group_with_same_identifier(self):
        attribute_group = AttributeGroupFactory.create(
            uuid="670596d5-8ce3-4b97-b4a4-bd1c05516c4a",
            name="base attributes",
            description="some basic yivi attributes",
            attributes=["firstname", "lastname"],
        )

        # Create a dataset with the same identifier, but with different attribute group information
        dataset = tablib.Dataset(
            *[
                (
                    "670596d5-8ce3-4b97-b4a4-bd1c05516c4a",
                    "additional attributes",
                    "",
                    "DOB",
                )
            ],
            headers=["uuid", "name", "description", "attributes"],
        )

        results = YiviAttributeGroupResource().import_data(dataset)

        self.assertEqual(len(results.rows), 1)
        result = results.rows[0]

        # The result should represent the attribute group with the same identifier
        self.assertEqual(result.is_skip(), True)
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
            *[
                (
                    "79623448-fa11-4d86-91c5-0e2a5cd617ac",
                    "base attributes",
                    "some basic yivi attributes",
                    "firstname,lastname",
                )
            ],
            headers=["uuid", "name", "description", "attributes"],
        )

        results = YiviAttributeGroupResource().import_data(dataset)

        self.assertEqual(len(results.rows), 1)
        result = results.rows[0]

        # The result should represent the attribute group with the same information
        self.assertEqual(result.is_skip(), True)
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
            *[
                (
                    "79623448-fa11-4d86-91c5-0e2a5cd617ac",
                    "additional attributes",
                    "",
                    "DOB",
                )
            ],
            headers=["uuid", "name", "description", "attributes"],
        )

        results = YiviAttributeGroupResource().import_data(dataset)

        self.assertEqual(len(results.rows), 1)
        result = results.rows[0]

        # The result should not represent any existing attribute group
        self.assertEqual(result.is_new(), True)
        self.assertNotEqual(result.instance, attribute_group)

        # A new attribute group has been created
        self.assertEqual(AttributeGroup.objects.count(), 2)
