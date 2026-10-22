import copy
import datetime
import json

from django.test import TestCase
from django.utils import translation
from django.utils.translation import gettext as _

import time_machine
from unittest_parametrize import ParametrizedTestCase, parametrize

from openforms.authentication.constants import AuthAttribute
from openforms.authentication.contrib.yivi_oidc.models import AttributeGroup
from openforms.authentication.tests.factories import AttributeGroupFactory
from openforms.config.models import MapTileLayer, MapWMSTileLayer, Theme
from openforms.config.tests.factories import (
    MapTileLayerFactory,
    MapWMSTileLayerFactory,
    ThemeFactory,
)
from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory
from openforms.formio.typing import MapComponent, TextFieldComponent
from openforms.payments.contrib.worldline.tests.factories import (
    WorldlineMerchantFactory,
)
from openforms.prefill.constants import IdentifierRoles
from openforms.products.models import Product
from openforms.products.tests.factories import ProductFactory
from openforms.variables.constants import (
    FormVariableDataTypes,
    FormVariableSources,
)

from ..models import Category, FormDefinition, FormStep, FormVersion
from .factories import (
    CategoryFactory,
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
    FormVariableFactory,
    FormVersionFactory,
)
from .utils import EXPORT_BLOB


class RestoreVersionTest(ParametrizedTestCase, TestCase):
    def test_restoring_version(self):
        form_definition = FormDefinitionFactory.create(
            name="Test Definition 2",
            internal_name="Test Internal 2",
            configuration={
                "components": [
                    {"test": "2", "key": "test", "label": "test", "type": "textfield"}
                ]
            },
            is_reusable=True,
        )
        form = FormFactory.create(name="Test Form 2")
        FormStepFactory.create(form=form, form_definition=form_definition)

        version = FormVersion.objects.create(
            form=form,
            created=datetime.datetime(2021, 7, 21, 12, 00, 00),
            export_blob=EXPORT_BLOB,
        )

        self.assertEqual(1, FormVersion.objects.count())
        self.assertEqual(1, FormDefinition.objects.count())

        form.restore_old_version(version.uuid)
        form.refresh_from_db()

        self.assertEqual(
            2, FormVersion.objects.count()
        )  # the restore creates a new version itself
        self.assertEqual("Test Form 1", form.name)
        self.assertEqual("Test Form Internal 1", form.internal_name)
        self.assertEqual(2, FormDefinition.objects.count())
        last_version = FormVersion.objects.order_by("-created").first()
        assert last_version is not None
        self.assertEqual(
            last_version.description,
            _("Restored form version {version} (from {created}).").format(
                version=1, created=version.created.isoformat()
            ),
        )

        form_steps = FormStep.objects.filter(form=form)

        self.assertEqual(1, form_steps.count())

        restored_form_definition = form_steps.get().form_definition

        with translation.override("en"):
            self.assertEqual("Test Definition 1", restored_form_definition.name)
            self.assertEqual("Test Definitie 1", restored_form_definition.name_nl)
        self.assertEqual(
            "Test Definition Internal 1", restored_form_definition.internal_name
        )
        self.assertEqual("test-definition-1", restored_form_definition.slug)
        self.assertEqual(
            {
                "components": [
                    {"test": "1", "key": "test", "type": "textfield", "label": "test"}
                ]
            },
            restored_form_definition.configuration,
        )

    @time_machine.travel("2022-02-21T17:00:00Z", tick=False)
    def test_restore_version_description_correct(self):
        """
        Assert that the counting of the form version number works correctly.
        """
        form1, form2 = FormFactory.create_batch(2, generate_minimal_setup=True)
        form_version1 = FormVersion.objects.create_for(form=form1)
        form_version2 = FormVersion.objects.create_for(form=form2)

        for form_version in [form_version1, form_version2]:
            with self.subTest(form_version=form_version):
                self.assertEqual(
                    form_version.description, _("Version {number}").format(number=1)
                )

        with time_machine.travel("2022-02-21T18:00:00Z", tick=False):
            form_version3 = FormVersion.objects.create_for(form=form1)
            form_version4 = FormVersion.objects.create_for(form=form2)

            # check that restoring is correct
            for form, form_version in [
                (form1, form_version3),
                (form2, form_version4),
            ]:
                with self.subTest(form=form, form_version=form_version):
                    form.restore_old_version(form_version_uuid=form_version.uuid)
                    last_version = (
                        FormVersion.objects.filter(form=form)
                        .order_by("-created", "-pk")
                        .first()
                    )
                    self.assertEqual(
                        last_version.description,
                        _("Restored form version {version} (from {created}).").format(
                            version=2, created="2022-02-21T18:00:00+00:00"
                        ),
                    )

    def test_form_definition_same_uuid_different_configuration(self):
        """Test that restoring a form definition with a slug that matches the slug of another form definition
        (but has a different configuration) creates a new form definition with a modified slug.
        """
        form_definition = FormDefinitionFactory.create(
            uuid="f0dad93b-333b-49af-868b-a6bcb94fa1b8",
            slug="test-definition-1",
            configuration={"test": "2"},
            is_reusable=True,
        )
        form = FormFactory.create(name="Test Form 2")
        FormStepFactory.create(form=form, form_definition=form_definition)

        version = FormVersion.objects.create(
            form=form,
            created=datetime.datetime(2021, 7, 21, 12, 00, 00),
            export_blob=EXPORT_BLOB,
        )

        form.restore_old_version(version.uuid)
        form.refresh_from_db()

        self.assertEqual(
            2, FormVersion.objects.count()
        )  # the restore creates a new version itself
        self.assertEqual(2, FormDefinition.objects.count())

        form_steps = FormStep.objects.filter(form=form)

        self.assertEqual(1, form_steps.count())

        restored_form_definition = form_steps.get().form_definition

        self.assertEqual("test-definition-1", restored_form_definition.slug)
        self.assertNotEqual(
            str(restored_form_definition.uuid), "f0dad93b-333b-49af-868b-a6bcb94fa1b8"
        )

    def test_handling_uuid(self):
        """
        Assert that existing UUIDs get replaced with new ones while restoring.

        Test what happens if the version being imported has the same definition UUID as
        another existing form definition.
        """
        form_definition = FormDefinitionFactory.create(
            uuid="f0dad93b-333b-49af-868b-a6bcb94fa1b8",
            slug="test-definition-1",
            configuration={"test": "2"},
            is_reusable=True,
        )
        form = FormFactory.create(name="Test Form 2")
        FormStepFactory.create(form=form, form_definition=form_definition)

        version = FormVersion.objects.create(
            form=form,
            created=datetime.datetime(2021, 7, 21, 12, 00, 00),
            export_blob=EXPORT_BLOB,
        )

        form.restore_old_version(version.uuid)
        form.refresh_from_db()

        new_fd = FormStep.objects.get(form=form).form_definition

        self.assertEqual(
            form_definition,
            FormDefinition.objects.get(uuid="f0dad93b-333b-49af-868b-a6bcb94fa1b8"),
        )
        self.assertNotEqual("f0dad93b-333b-49af-868b-a6bcb94fa1b8", str(new_fd.uuid))

    def test_restore_twice_a_version(self):
        form_definition = FormDefinitionFactory.create(
            uuid="f0dad93b-333b-49af-868b-a6bcb94fa1b8",
            slug="test-definition-2",
            configuration={"test": "2"},
        )
        form = FormFactory.create(name="Test Form 2")
        FormStepFactory.create(form=form, form_definition=form_definition)

        version = FormVersion.objects.create(
            form=form,
            created=datetime.datetime(2021, 7, 21, 12, 00, 00),
            export_blob=EXPORT_BLOB,
        )

        for _i in range(2):
            form.restore_old_version(version.uuid)
            form.refresh_from_db()

        self.assertEqual(FormDefinition.objects.count(), 1)

    def test_form_definition_same_uuid_same_configuration(self):
        """
        Test restoring a form definition with the same slug and same configuration.

        Restoring a form definition with a slug that matches the slug of another form
        definition and has the same configuration links to the existing form definition.
        """
        form_definition = FormDefinitionFactory.create(
            uuid="f0dad93b-333b-49af-868b-a6bcb94fa1b8",  # must match EXPORT_BLOB FD uuid
            slug="test-definition-1",
            configuration={
                "components": [
                    {
                        "test": "1",
                        "key": "test",
                        "label": "test",
                        "type": "textfield",
                    }
                ]
            },
            is_reusable=True,
        )
        form = FormFactory.create(name="Test Form 2")
        FormStepFactory.create(form=form, form_definition=form_definition)
        assert FormDefinition.objects.count() == 1

        version = FormVersion.objects.create(
            form=form,
            created=datetime.datetime(2021, 7, 21, 12, 00, 00),
            export_blob=EXPORT_BLOB,
        )

        form.restore_old_version(version.uuid)
        form.refresh_from_db()

        # the restore creates a new version itself
        self.assertEqual(FormVersion.objects.count(), 2)
        self.assertEqual(FormDefinition.objects.count(), 1)

        form_steps = FormStep.objects.filter(form=form)
        self.assertEqual(form_steps.count(), 1)
        restored_form_definition = form_steps.get().form_definition
        self.assertEqual(form_definition, restored_form_definition)

    def test_restore_form_with_reusable_form_definition(self):
        """
        Test that restoring forms with re-usable form definitions restores those as well.

        Regression test for issue #1348.
        """
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__is_reusable=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "reusable1",
                        "label": "reusable1",
                    }
                ]
            },
        )
        FormStepFactory.create(
            form=form,
            form_definition__is_reusable=False,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "notReusable",
                        "label": "notReusable",
                    }
                ]
            },
        )
        version = FormVersionFactory.create(form=form)
        # now delete the form step, we'll restore it in a bit
        form.formstep_set.all()[0].delete()
        with self.subTest("verify test setup"):
            self.assertNotEqual(version.export_blob, {})
            self.assertEqual(form.formstep_set.count(), 1)
            self.assertFalse(
                form.formstep_set.filter(form_definition__is_reusable=True).exists()
            )

        # do the actual restore
        form.restore_old_version(version.uuid)

        # get all fresh DB records
        form.refresh_from_db()

        self.assertEqual(form.formstep_set.count(), 2)
        form_steps = form.formstep_set.all()

        self.assertTrue(form_steps[0].form_definition.is_reusable)
        self.assertEqual(
            form_steps[0].form_definition.configuration,
            {
                "components": [
                    {
                        "type": "textfield",
                        "key": "reusable1",
                        "label": "reusable1",
                    }
                ]
            },
        )
        self.assertFalse(form_steps[1].form_definition.is_reusable)

    @parametrize("initial_active_state", [True, False])
    def test_form_restore_active_state_is_correctly_kept(self, initial_active_state):
        with self.subTest(data=initial_active_state):
            form = FormFactory.create(
                generate_minimal_setup=True, active=initial_active_state
            )

            version = FormVersionFactory.create(form=form)
            assert version.export_blob

            # Change active state after version was made
            form.active = not initial_active_state
            form.save()

            # Restore the previous version
            form.restore_old_version(version.uuid)

            # refresh DB records
            form.refresh_from_db()

            # Assert active state equals the initial active state
            self.assertEqual(form.active, initial_active_state)

    def test_full_form_save_and_restore(self):
        """
        Tests that all form configuration that receives dedicated attention from the
        import/export is correctly saved and restored.

        Ensuring all configuration is kept, especially the product, theme and category.
        """
        # Every OF instance has a couple default WMTS- and WMS-tile layer.
        # To simplify this test, we start at zero.
        MapTileLayer.objects.all().delete()
        MapWMSTileLayer.objects.all().delete()

        product = ProductFactory.create()
        theme = ThemeFactory.create(design_token_values={"key": "token"})
        category = CategoryFactory.create()

        wmts_tile_layer = MapTileLayerFactory.create()
        wms_tile_layer = MapWMSTileLayerFactory.create()

        yivi_attribute_group = AttributeGroupFactory.create(
            attributes=["first_name", "last_name"]
        )

        merchant = WorldlineMerchantFactory.create()
        objects_api_group = ObjectsAPIGroupConfigFactory.create(
            identifier="test-objects-api-group"
        )
        form = FormFactory.create(
            generate_minimal_setup=True,
            product=product,
            theme=theme,
            category=category,
            authentication_backend="yivi_oidc",
            authentication_backend__options={
                "authentication_options": [AuthAttribute.bsn],
                "additional_attributes_groups": [yivi_attribute_group.uuid],
            },
            internal_remarks="Some internal remark that should be kept",
            payment_backend="worldline",
            payment_backend_options={"merchant": merchant.pspid},
            registration_backend="email",
            registration_backend_options={"to_emails": ["abc@xyz.com"]},
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "textfield",
                        "type": "textfield",
                        "label": "Textfield",
                        "prefill": {
                            "plugin": "demo",
                            "attribute": "random_number",
                            "identifier_role": IdentifierRoles.authorizee,
                        },
                    },
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
                        "overlays": [
                            {
                                "url": "",
                                "type": "wms",
                                "uuid": str(wms_tile_layer.uuid),
                                "label": "Basisregistratie Adressen en Gebouwen (BAG)",
                                "layers": ["pand", "verblijfsobject"],
                            },
                        ],
                    },
                ],
            },
        )
        FormVariableFactory.create(
            form=form,
            key="variable_with_demo_prefill",
            user_defined=True,
            prefill_plugin="demo",
            prefill_attribute="random_string",
            prefill_identifier_role=IdentifierRoles.authorizee,
        )
        FormVariableFactory.create(
            form=form,
            key="variable_with_objects_api_prefill",
            user_defined=True,
            prefill_plugin="objects_api",
            prefill_options={
                "objects_api_group": objects_api_group.identifier,
                "objecttype_uuid": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                "objecttype_version": 3,
                "variables_mapping": [
                    {"variable_key": "lastName", "target_path": ["name", "last.name"]},
                    {"variable_key": "age", "target_path": ["age"]},
                ],
                "auth_attribute_path": ["bsn"],
            },
        )

        # Validate the initial setup
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(Theme.objects.count(), 1)
        self.assertEqual(Category.objects.count(), 1)
        self.assertEqual(MapTileLayer.objects.count(), 1)
        self.assertEqual(MapWMSTileLayer.objects.count(), 1)
        self.assertEqual(AttributeGroup.objects.count(), 1)

        version = FormVersionFactory.create(form=form)
        assert version.export_blob

        # Restore it
        form.restore_old_version(version.uuid)

        # get all fresh DB records
        form.refresh_from_db()

        # Validate that no new additional data was created
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(Theme.objects.count(), 1)
        self.assertEqual(Category.objects.count(), 1)
        self.assertEqual(MapTileLayer.objects.count(), 1)
        self.assertEqual(MapWMSTileLayer.objects.count(), 1)
        self.assertEqual(AttributeGroup.objects.count(), 1)

        # Validate that the product, theme and category are all still the same.
        self.assertEqual(form.product.uuid, product.uuid)
        self.assertEqual(form.theme.uuid, theme.uuid)
        self.assertEqual(form.category.uuid, category.uuid)

        # Validate payment backend stayed the same.
        self.assertEqual(form.payment_backend, "worldline")
        self.assertEqual(form.payment_backend_options["merchant"], merchant.pspid)

        # Validate auth backend
        self.assertEqual(form.auth_backends.count(), 1)
        auth_backend = form.auth_backends.first()
        assert auth_backend is not None

        self.assertEqual(auth_backend.backend, "yivi_oidc")
        self.assertEqual(
            auth_backend.options["authentication_options"], [AuthAttribute.bsn]
        )
        self.assertEqual(
            auth_backend.options["additional_attributes_groups"],
            [str(yivi_attribute_group.uuid)],
        )

        # Validate registration backend and sensitive data was kept
        self.assertEqual(
            form.internal_remarks, "Some internal remark that should be kept"
        )
        self.assertEqual(form.registration_backends.count(), 1)
        registration_backend = form.registration_backends.first()
        assert registration_backend is not None

        self.assertEqual(registration_backend.backend, "email")
        self.assertEqual(registration_backend.options["to_emails"], ["abc@xyz.com"])

        # Validate that prefill configuration is kept on form variables
        user_defined_variables = form.formvariable_set.filter(
            source=FormVariableSources.user_defined
        ).order_by("pk")
        self.assertEqual(user_defined_variables.count(), 2)

        variable1 = user_defined_variables[0]
        assert variable1.key == "variable_with_demo_prefill"
        self.assertEqual(variable1.prefill_plugin, "demo")
        self.assertEqual(variable1.prefill_attribute, "random_string")
        self.assertEqual(variable1.prefill_identifier_role, IdentifierRoles.authorizee)

        variable2 = user_defined_variables[1]
        assert variable2.key == "variable_with_objects_api_prefill"
        self.assertEqual(variable2.prefill_plugin, "objects_api")
        self.assertEqual(
            variable2.prefill_options,
            {
                "objects_api_group": objects_api_group.identifier,
                "objecttype_uuid": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                "objecttype_version": 3,
                "variables_mapping": [
                    {"variable_key": "lastName", "target_path": ["name", "last.name"]},
                    {"variable_key": "age", "target_path": ["age"]},
                ],
                "auth_attribute_path": ["bsn"],
            },
        )

        form_step = form.formstep_set.first()
        assert form_step is not None
        form_definition = form_step.form_definition
        assert len(form_definition.configuration["components"]) == 2

        # Validate that prefill configuration is kept on components
        textfield_component: TextFieldComponent = form_definition.configuration[
            "components"
        ][0]
        assert textfield_component["type"] == "textfield"
        self.assertEqual(
            textfield_component.get("prefill"),
            {
                "plugin": "demo",
                "attribute": "random_number",
                "identifier_role": IdentifierRoles.authorizee,
            },
        )

        # Validate map component tile layer configuration is kept
        map_component: MapComponent = form_definition.configuration["components"][1]
        assert map_component["type"] == "map"
        self.assertEqual(
            map_component.get("tileLayerIdentifier"), wmts_tile_layer.identifier
        )
        map_overlays = map_component.get("overlays", [])
        self.assertEqual(len(map_overlays), 1)
        self.assertEqual(map_overlays[0]["uuid"], str(wms_tile_layer.uuid))

    def test_form_restore_creates_new_resources_when_original_resources_have_been_changed(
        self,
    ):
        """
        Restoring a form version should use additional resources that conform to the
        original form. If the original resources have been changed, new resources should
        be created/used with the original configuration.
        """
        # Every OF instance has a couple default WMTS- and WMS-tile layer.
        # To simplify this test, we start at zero.
        MapTileLayer.objects.all().delete()
        MapWMSTileLayer.objects.all().delete()

        # Create the additional resources.
        product = ProductFactory.create(
            name="original product name",
            price=10,
            information="original product information",
        )
        wms_tile_layer = MapWMSTileLayerFactory.create(
            name="original wms layer", url="original-test-wms-url.com"
        )
        wmts_tile_layer = MapTileLayerFactory.create(
            identifier="original-wmts-layer",
            label="original wmts layer",
            url="original-test-wmts-url.com",
        )
        yivi_attribute_group = AttributeGroupFactory.create(
            name="original yivi attribute group",
            description="original yivi attribute group description",
            attributes=["original_attribute"],
        )

        # Basic form that implements the additional resources.
        form = FormFactory.create(
            generate_minimal_setup=True,
            product=product,
            authentication_backend="yivi_oidc",
            authentication_backend__options={
                "authentication_options": [AuthAttribute.bsn],
                "additional_attributes_groups": [yivi_attribute_group.uuid],
            },
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
                        "overlays": [
                            {
                                "url": "",
                                "type": "wms",
                                "uuid": str(wms_tile_layer.uuid),
                                "label": "Basisregistratie Adressen en Gebouwen (BAG)",
                                "layers": ["pand", "verblijfsobject"],
                            },
                        ],
                    },
                ],
            },
        )

        version = FormVersionFactory.create(form=form)
        assert version.export_blob

        # Update original product
        product.name = "updated product name"
        product.price = 20
        product.information = "updated product information"
        product.save()

        # Update original wms tile layer
        wms_tile_layer.name = "updated wms layer"
        wms_tile_layer.url = "updated-test-wms-url.com"
        wms_tile_layer.save()

        # Update original wmts tile layer
        # NOT changing the identifier, otherwise `.first()`/`.last()` becomes ambiguous
        wmts_tile_layer.label = "updated wmts layer"
        wmts_tile_layer.url = "updated-test-wmts-url.com"
        wmts_tile_layer.save()

        # Update original yivi attribute group
        yivi_attribute_group.name = "updated yivi attribute group"
        yivi_attribute_group.description = "updated yivi attribute group description"
        yivi_attribute_group.attributes = ["updated_attribute"]
        yivi_attribute_group.save()

        # Restore the previous version
        form.restore_old_version(version.uuid)

        # get all fresh DB records
        form.refresh_from_db()

        # Because the resources were updated after the version was made, new product,
        # wms/wmts tile layers and attribute groups should have been made.
        self.assertEqual(Product.objects.count(), 2)
        self.assertEqual(MapTileLayer.objects.count(), 2)
        self.assertEqual(MapWMSTileLayer.objects.count(), 2)
        self.assertEqual(AttributeGroup.objects.count(), 2)

        new_product = Product.objects.last()
        new_wms_tile_layer = MapWMSTileLayer.objects.last()
        new_wmts_tile_layer = MapTileLayer.objects.order_by("identifier").last()
        new_attribute_group = AttributeGroup.objects.last()
        assert new_product is not None
        assert new_wms_tile_layer is not None
        assert new_wmts_tile_layer is not None
        assert new_attribute_group is not None

        # Assert that the new product uses the original product data
        # and assert that the restored form uses the new product
        self.assertEqual(new_product.name, "original product name")
        self.assertEqual(new_product.price, 10)
        self.assertEqual(new_product.information, "original product information")
        self.assertEqual(form.product.uuid, new_product.uuid)

        form_step = form.formstep_set.first()
        assert form_step is not None
        map_component: MapComponent = form_step.form_definition.configuration[
            "components"
        ][0]

        # Assert that the new wms tile layer uses the original wms tile layer data
        # and assert that the restored form uses the new wms tile layer
        map_overlays = map_component.get("overlays", [])
        assert len(map_overlays) == 1
        self.assertEqual(new_wms_tile_layer.name, "original wms layer")
        self.assertEqual(new_wms_tile_layer.url, "original-test-wms-url.com")
        self.assertEqual(map_overlays[0]["uuid"], str(new_wms_tile_layer.uuid))

        # Assert that the new wmts tile layer uses the original wmts tile layer data
        # and assert that the restored form uses the new wmts tile layer
        self.assertEqual(new_wmts_tile_layer.label, "original wmts layer")
        self.assertEqual(new_wmts_tile_layer.url, "original-test-wmts-url.com")
        self.assertEqual(
            map_component.get("tileLayerIdentifier"),
            str(new_wmts_tile_layer.identifier),
        )

        self.assertEqual(form.auth_backends.count(), 1)
        auth_backend = form.auth_backends.first()
        assert auth_backend is not None

        # Assert that the new attribute group uses the original attribute group data
        # and assert that the restored form uses the new attribute group
        self.assertEqual(new_attribute_group.name, "original yivi attribute group")
        self.assertEqual(
            new_attribute_group.description, "original yivi attribute group description"
        )
        self.assertEqual(new_attribute_group.attributes, ["original_attribute"])
        self.assertEqual(
            auth_backend.options["additional_attributes_groups"],
            [str(new_attribute_group.uuid)],
        )

    def test_form_restore_using_resource_with_same_data(self):
        # Create the additional resources.
        product1 = ProductFactory.create(name="product name 1", price=1)
        product2 = ProductFactory.create(name="product name 2", price=2)
        wms_tile_layer1 = MapWMSTileLayerFactory.create(
            name="wms layer 1", url="test-wms-url-1.com"
        )
        wms_tile_layer2 = MapWMSTileLayerFactory.create(
            name="wms layer 2", url="test-wms-url-2.com"
        )
        wmts_tile_layer1 = MapTileLayerFactory.create(
            identifier="wmts-layer1", label="wmts layer 1", url="wmts-url-1.com"
        )
        wmts_tile_layer2 = MapTileLayerFactory.create(
            identifier="wmts-layer2", label="wmts layer 2", url="wmts-url-2.com"
        )
        yivi_attribute_group1 = AttributeGroupFactory.create(
            name="attribute group 1", attributes=["attribute1"]
        )
        yivi_attribute_group2 = AttributeGroupFactory.create(
            name="attribute group 2", attributes=["attribute2"]
        )

        # Basic form that implements the additional resources.
        form = FormFactory.create(
            generate_minimal_setup=True,
            product=product1,
            authentication_backend="yivi_oidc",
            authentication_backend__options={
                "authentication_options": [AuthAttribute.bsn],
                "additional_attributes_groups": [yivi_attribute_group1.uuid],
            },
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
                        "tileLayerIdentifier": wmts_tile_layer1.identifier,
                        "overlays": [
                            {
                                "url": "",
                                "type": "wms",
                                "uuid": str(wms_tile_layer1.uuid),
                                "label": "Basisregistratie Adressen en Gebouwen (BAG)",
                                "layers": ["pand", "verblijfsobject"],
                            },
                        ],
                    },
                ],
            },
        )

        # Create form version
        version = FormVersionFactory.create(form=form)
        assert version.export_blob

        # Change all the resources around
        # (resource 1 uses the data of resource 2, resource 2 uses the data of resource 1)
        product1.name = "product name 2"
        product1.price = 2
        product2.name = "product name 1"
        product2.price = 1
        product1.save()
        product2.save()

        wms_tile_layer1.name = "wms layer 2"
        wms_tile_layer1.url = "test-wms-url-2.com"
        wms_tile_layer2.name = "wms layer 1"
        wms_tile_layer2.url = "test-wms-url-1.com"
        wms_tile_layer1.save()
        wms_tile_layer2.save()

        wmts_tile_layer1.identifier = "wmts-layer2"
        wmts_tile_layer1.label = "wmts layer 2"
        wmts_tile_layer1.url = "wmts-url-2.com"
        wmts_tile_layer1.identifier = "wmts-layer1"
        wmts_tile_layer2.label = "wmts layer 1"
        wmts_tile_layer2.url = "wmts-url-1.com"
        wmts_tile_layer1.save()
        wmts_tile_layer2.save()

        yivi_attribute_group1.name = "attribute group 2"
        yivi_attribute_group1.attributes = ["attribute2"]
        yivi_attribute_group2.name = "attribute group 1"
        yivi_attribute_group2.attributes = ["attribute1"]
        yivi_attribute_group1.save()
        yivi_attribute_group2.save()

        # Restore the form
        form.restore_old_version(version.uuid)

        # get all fresh DB records
        form.refresh_from_db()

        # No new resources were created
        self.assertEqual(Product.objects.count(), 2)
        self.assertEqual(MapTileLayer.objects.count(), 2)
        self.assertEqual(MapWMSTileLayer.objects.count(), 2)
        self.assertEqual(AttributeGroup.objects.count(), 2)

        # The form should use product2, which currently has the same data as the product
        # in the form version data
        self.assertEqual(form.product.uuid, product2.uuid)

        form_step = form.formstep_set.first()
        assert form_step is not None
        map_component: MapComponent = form_step.form_definition.configuration[
            "components"
        ][0]

        # The form should use wms_tile_layer2, which currently has the same data as the
        # wms tile layer in the form version data
        map_overlays = map_component.get("overlays", [])
        assert len(map_overlays) == 1
        self.assertEqual(map_overlays[0]["uuid"], str(wms_tile_layer2.uuid))

        # The form should use wmts_tile_layer2, which currently has the same data as the
        # wmts tile layer in the form version data
        self.assertEqual(
            map_component.get("tileLayerIdentifier"), str(wmts_tile_layer2.identifier)
        )

        self.assertEqual(form.auth_backends.count(), 1)
        auth_backend = form.auth_backends.first()
        assert auth_backend is not None

        # The form should use yivi_attribute_group2, which currently has the same data as
        # the yivi attribute group in the form version data
        self.assertEqual(
            auth_backend.options["additional_attributes_groups"],
            [str(yivi_attribute_group2.uuid)],
        )

    def test_form_restore_theme_and_category_are_removed_if_not_available(self):
        theme = ThemeFactory.create()
        category = CategoryFactory.create()

        form = FormFactory.create(
            generate_minimal_setup=True, theme=theme, category=category
        )

        # Create form version
        version = FormVersionFactory.create(form=form)
        assert version.export_blob

        # We have to decouple category first before we can delete it, otherwise an
        # on_delete PROTECT will be triggered
        form.category = None
        form.save()

        # Delete theme and category
        theme.delete()
        category.delete()

        # Restore previous form version
        form.restore_old_version(version.uuid)

        # get all fresh DB records
        form.refresh_from_db()

        # Validate that no new theme or category was created
        self.assertFalse(Theme.objects.exists())
        self.assertFalse(Category.objects.exists())

        # Validate that theme and category are both unset
        self.assertIsNone(form.theme)
        self.assertIsNone(form.category)


FORM_STEP = [
    {
        "form": "http://testserver/api/v2/forms/324cadce-a627-4e3f-b117-37ca232f16b2",
        "form_definition": "http://testserver/api/v2/form-definitions/f0dad93b-333b-49af-868b-a6bcb94fa1b8",
        "index": 0,
        "slug": "icecream-form-step",
        "uuid": "3ca01601-cd20-4746-bce5-baab47636823",
    }
]

FORM = [
    {
        "active": True,
        "authentication_backends": [],
        "is_deleted": False,
        "login_required": False,
        "maintenance_mode": False,
        "name": "Icecream questionnaire",
        "internal_name": "Icecream questionnaire",
        "product": None,
        "show_progress_indicator": True,
        "slug": "icecream-questionnaire",
        "url": "http://testserver/api/v2/forms/324cadce-a627-4e3f-b117-37ca232f16b2",
        "uuid": "324cadce-a627-4e3f-b117-37ca232f16b2",
    }
]

FORM_DEFINITION = [
    {
        "configuration": {
            "components": [
                {
                    "type": "textfield",
                    "key": "favouriteFlavour",
                    "label": "favouriteFlavour",
                }
            ]
        },
        "name": "Icecream questions",
        "internal_name": "Icecream questions",
        "slug": "icecream-questions",
        "url": "http://testserver/api/v2/form-definitions/f0dad93b-333b-49af-868b-a6bcb94fa1b8",
        "uuid": "f0dad93b-333b-49af-868b-a6bcb94fa1b8",
    }
]

FORM_VARIABLES = [
    {
        "form": "http://testserver/api/v2/forms/324cadce-a627-4e3f-b117-37ca232f16b2",
        "name": "CO2 footprint",
        "key": "co2-footprint",
        "source": FormVariableSources.user_defined,
        "data_type": FormVariableDataTypes.float,
    }
]


class RestoreVersionsWithVariablesTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.export_blob = {
            "forms": json.dumps(FORM),
            "formDefinitions": json.dumps(
                FORM_DEFINITION
            ),  # contains one textfield component
            "formSteps": json.dumps(FORM_STEP),
            "formLogic": json.dumps([]),
        }

    def test_restore_form_with_more_component_variables(self):
        form_definition = FormDefinitionFactory.create(
            name="Icecream questionnaire",
            internal_name="Icecream questionnaire",
            configuration={"components": []},
        )
        form = FormFactory.create(name="Icecream questions")
        FormStepFactory.create(form=form, form_definition=form_definition)

        version = FormVersion.objects.create(
            form=form,
            created=datetime.datetime(2021, 7, 21, 12, 00, 00),
            export_blob=self.export_blob,  # Contains 1 textfield component
        )

        self.assertEqual(0, form.formvariable_set.count())

        form.restore_old_version(version.uuid)
        form.refresh_from_db()

        self.assertEqual(1, form.formvariable_set.count())

    def test_restore_form_with_fewer_component_variables(self):
        form_definition = FormDefinitionFactory.create(
            name="Icecream questionnaire",
            internal_name="Icecream questionnaire",
            configuration={
                "components": [
                    {
                        "key": "favouriteFlavour",
                        "type": "textfield",
                        "label": "favouriteFlavour",
                    },
                    {
                        "key": "whippedCream",
                        "type": "checkbox",
                        "label": "whippedCream",
                        "defaultValue": False,
                    },
                ]
            },
        )
        form = FormFactory.create(name="Icecream questions")
        FormStepFactory.create(form=form, form_definition=form_definition)

        version = FormVersion.objects.create(
            form=form,
            created=datetime.datetime(2021, 7, 21, 12, 00, 00),
            export_blob=self.export_blob,
        )

        self.assertEqual(2, form.formvariable_set.count())

        form.restore_old_version(version.uuid)
        form.refresh_from_db()

        self.assertEqual(1, form.formvariable_set.count())

    def test_restore_form_with_user_defined_variables(self):
        form_definition = FormDefinitionFactory.create(
            name="Icecream questionnaire",
            internal_name="Icecream questionnaire",
            configuration={
                "components": [
                    {
                        "key": "favouriteFlavour",
                        "type": "textfield",
                        "label": "favouriteFlavour",
                    },
                ]
            },
        )
        form = FormFactory.create(name="Icecream questions")
        FormStepFactory.create(form=form, form_definition=form_definition)
        FormVariableFactory.create(
            source=FormVariableSources.user_defined, key="customer-points", form=form
        )

        user_defined_vars = form.formvariable_set.filter(
            source=FormVariableSources.user_defined
        )
        self.assertEqual(1, user_defined_vars.count())
        self.assertEqual("customer-points", user_defined_vars.first().key)

        export_with_user_defined_var = copy.deepcopy(self.export_blob)
        export_with_user_defined_var["formVariables"] = json.dumps(FORM_VARIABLES)
        version = FormVersion.objects.create(
            form=form,
            created=datetime.datetime(2021, 7, 21, 12, 00, 00),
            export_blob=export_with_user_defined_var,
        )

        form.restore_old_version(version.uuid)
        form.refresh_from_db()

        restored_user_defined_vars = form.formvariable_set.filter(
            source=FormVariableSources.user_defined
        )
        self.assertEqual(1, restored_user_defined_vars.count())
        self.assertEqual("co2-footprint", restored_user_defined_vars.first().key)
