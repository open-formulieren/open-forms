import copy
import uuid

from django.db import models
from django.test import TestCase, override_settings
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
from openforms.formio.tests.assertions import FormioMixin
from openforms.payments.contrib.worldline.tests.factories import (
    WorldlineMerchantFactory,
)
from openforms.prefill.constants import IdentifierRoles
from openforms.products.models import Product
from openforms.products.tests.factories import ProductFactory
from openforms.variables.constants import (
    FormVariableSources,
)

from ..models import Category, Form, FormDefinition, FormVersion
from .factories import (
    CategoryFactory,
    FormAuthenticationBackendFactory,
    FormDefinitionFactory,
    FormFactory,
    FormLogicFactory,
    FormStepFactory,
    FormVariableFactory,
    FormVersionFactory,
)


def _prepare_form_version_for_restore(
    *, form: Form, form_for_restore: Form
) -> FormVersion:
    version = FormVersion.objects.create_for(form)
    # hack - assign the version to the other form so it can be restored
    version.form = form_for_restore
    version.save()
    # set a different slug for the source form so that the restored form gets the proper
    # slug
    form.slug = str(uuid.uuid4())
    form.save()
    return version


class RestoreVersionTest(FormioMixin, ParametrizedTestCase, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # Every OF instance has a couple default WMTS- and WMS-tile layer.
        # To simplify tests, start at zero.
        MapTileLayer.objects.all().delete()
        MapWMSTileLayer.objects.all().delete()

    @override_settings(LANGUAGE_CODE="nl")
    def test_restoring_old_version_restores_all_aspects_of_a_form(self):
        product = ProductFactory.create()
        theme = ThemeFactory.create(design_token_values={"key": "token"})
        category = CategoryFactory.create()
        wmts_tile_layer = MapTileLayerFactory.create()
        wms_tile_layer = MapWMSTileLayerFactory.create()
        yivi_attribute_group = AttributeGroupFactory.create(attributes=["last_name"])
        merchant = WorldlineMerchantFactory.create()
        form = FormFactory.create(
            active=True,
            deleted_=False,
            maintenance_mode=False,
            name="Test form",
            internal_name="Test form (internal)",
            internal_remarks="Keep internal remarks",
            slug="test-form",
            product=product,
            theme=theme,
            category=category,
            payment_backend="worldline",
            payment_backend_options={"merchant": merchant.pspid},
            generate_minimal_setup=True,
            formstep__slug="step-1",
            formstep__form_definition__slug="fd-1",
            formstep__form_definition__name="Originele definitie",
            formstep__form_definition__internal_name="form def 1",
            formstep__form_definition__is_reusable=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "originalTextfield",
                        "label": "Original text field",
                    },
                    {
                        "type": "textfield",
                        "key": "prefilledTextfield",
                        "label": "Prefilled textfield",
                        "prefill": {
                            "plugin": "demo",
                            "attribute": "random_number",
                            "identifier_role": IdentifierRoles.authorizee,
                        },
                    },
                    {
                        "type": "map",
                        "label": "Map",
                        "key": "map",
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
                ]
            },
            formstep__form_definition__name_en="Original definition",
            formstep__form_definition__name_nl="Originele definitie",
            registration_backend="email",
            registration_backend_options={"to_emails": ["abc@xyz.com"]},
        )
        # add a second step with reusable FD that will be deleted - this must get restored
        FormStepFactory.create(
            form=form,
            form_definition__is_reusable=True,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "fd2Textfield",
                        "label": "FD2 text field",
                    },
                ]
            },
        )
        FormAuthenticationBackendFactory.create(form=form, backend="digid")
        FormAuthenticationBackendFactory.create(form=form, backend="eherkenning")
        FormAuthenticationBackendFactory.create(
            form=form,
            backend="yivi_oidc",
            options={
                "authentication_options": [AuthAttribute.bsn],
                "additional_attributes_groups": [yivi_attribute_group.uuid],
            },
        )
        step1, step2 = form.formstep_set.order_by("order")
        FormVariableFactory.create(
            form=form,
            key="var1",
            user_defined=True,
            prefill_plugin="demo",
            prefill_attribute="random_string",
            prefill_identifier_role=IdentifierRoles.authorizee,
        )
        FormVariableFactory.create(
            form=form,
            key="var2",
            user_defined=True,
            prefill_plugin="demo",
            prefill_options={"foo": "bar"},
        )
        FormLogicFactory.create(
            form=form,
            order=0,
            json_logic_trigger={"==": [{"var": "originalTextfield"}, "foo"]},
            actions=[
                {
                    "action": {"type": "disable-next"},
                    "form_step_uuid": str(step1.uuid),
                }
            ],
        )
        form_for_restore = FormFactory.create(
            product=None, category=None, _is_deleted=True, maintenance_mode=True
        )
        with time_machine.travel("2021-07-21T12:00:00+02:00"):
            version = _prepare_form_version_for_restore(
                form=form, form_for_restore=form_for_restore
            )
        # introduce FD configuration drift
        fd = step1.form_definition
        fd.configuration["components"].append(
            {"type": "email", "key": "email", "label": "Email"}
        )
        fd.save()
        # delete the second reusable FD to verify it gets restored
        step2.delete()
        step2.form_definition.delete()
        assert form_for_restore.name != form.name
        assert not form_for_restore.formstep_set.exists()
        assert not form_for_restore.formlogic_set.exists()
        assert FormVersion.objects.count() == 1
        assert FormDefinition.objects.count() == 1

        # restore into a different, blank form so we can assert the configuration is
        # updated rather than it being coincidentally the same
        form_for_restore.restore_old_version(version.uuid)
        form_for_restore.refresh_from_db()

        with self.subTest("restoring creates a new version itself"):
            self.assertEqual(FormVersion.objects.count(), 2)
            last_version = FormVersion.objects.order_by("-created")[0]
            self.assertEqual(
                last_version.description,
                _("Restored form version {version} (from {created}).").format(
                    version=1, created=version.created.isoformat()
                ),
            )

        with self.subTest("form properties are set to previous version"):
            self.assertTrue(form_for_restore.active)
            self.assertFalse(form_for_restore._is_deleted)
            self.assertFalse(form_for_restore.maintenance_mode)
            self.assertEqual(form_for_restore.name, "Test form")
            self.assertEqual(form_for_restore.internal_name, "Test form (internal)")
            self.assertEqual(form_for_restore.slug, "test-form")
            self.assertEqual(form.internal_remarks, "Keep internal remarks")

            self.assertEqual(form_for_restore.product, product)
            self.assertEqual(Product.objects.count(), 1)
            self.assertEqual(form_for_restore.theme, theme)
            self.assertEqual(Theme.objects.count(), 1)
            self.assertEqual(form_for_restore.category, category)
            self.assertEqual(Category.objects.count(), 1)

        restored_step1, restored_step2 = form_for_restore.formstep_set.order_by("order")
        with self.subTest("form steps are set to previous version"):
            self.assertEqual(restored_step1.slug, "step-1")

            # a new FD is created because the configuration has drifted
            self.assertNotEqual(
                restored_step1.form_definition,
                form.formstep_set.get().form_definition,
            )
            self.assertNotEqual(
                restored_step1.form_definition.uuid,
                form.formstep_set.get().form_definition.uuid,
            )
            self.assertEqual(restored_step1.form_definition.name, "Originele definitie")
            with translation.override("en"):
                self.assertEqual(
                    restored_step1.form_definition.name, "Original definition"
                )
            self.assertEqual(restored_step1.form_definition.internal_name, "form def 1")
            self.assertEqual(restored_step1.form_definition.slug, "fd-1")
            self.assertTrue(restored_step1.form_definition.is_reusable)

            configuration = restored_step1.form_definition.configuration
            self.assertFormioComponent(
                configuration,
                "originalTextfield",
                {
                    "type": "textfield",
                    "key": "originalTextfield",
                    "label": "Original text field",
                },
            )
            component_keys = {c["key"] for c in configuration["components"]}
            self.assertEqual(
                component_keys, {"originalTextfield", "prefilledTextfield", "map"}
            )  # no email component here

        with self.subTest("prefill configuration is restored"):
            configuration = restored_step1.form_definition.configuration
            self.assertFormioComponent(
                configuration,
                "prefilledTextfield",
                {
                    "type": "textfield",
                    "key": "prefilledTextfield",
                    "label": "Prefilled textfield",
                    "prefill": {
                        "plugin": "demo",
                        "attribute": "random_number",
                        "identifier_role": IdentifierRoles.authorizee,
                    },
                },
            )

            # and also on user defined variables
            var1, var2 = form_for_restore.formvariable_set.filter(
                source=FormVariableSources.user_defined
            ).order_by("pk")
            self.assertEqual(var1.prefill_plugin, "demo")
            self.assertEqual(var1.prefill_attribute, "random_string")
            self.assertEqual(var1.prefill_identifier_role, IdentifierRoles.authorizee)

            self.assertEqual(var2.prefill_plugin, "demo")
            self.assertEqual(var2.prefill_options, {"foo": "bar"})

        with self.subTest("map configuration is restored"):
            configuration = restored_step1.form_definition.configuration
            self.assertFormioComponent(
                configuration,
                "map",
                {
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
            )
            self.assertEqual(MapTileLayer.objects.count(), 1)
            self.assertEqual(MapWMSTileLayer.objects.count(), 1)

        # See gh-1348
        with self.subTest("form step 2 restores the reusable form definition"):
            # second step is expected to restore a re-usable form definition
            fd2 = restored_step2.form_definition
            self.assertTrue(fd2.is_reusable)
            self.assertFormioComponent(
                fd2.configuration,
                "fd2Textfield",
                {
                    "type": "textfield",
                    "key": "fd2Textfield",
                    "label": "FD2 text field",
                },
            )

        with self.subTest("authentication backends are restored"):
            self.assertEqual(form_for_restore.auth_backends.count(), 3)

            yivi_backend = form_for_restore.auth_backends.get(backend="yivi_oidc")
            self.assertEqual(
                yivi_backend.options["authentication_options"], [AuthAttribute.bsn]
            )
            self.assertEqual(
                yivi_backend.options["additional_attributes_groups"],
                [str(yivi_attribute_group.uuid)],
            )
            self.assertEqual(AttributeGroup.objects.count(), 1)

        with self.subTest("form variables are restored"):
            component_vars = form_for_restore.formvariable_set.filter(
                source=FormVariableSources.component
            )
            # 3 components in step 1, 1 in step 2
            self.assertEqual(component_vars.count(), 3 + 1)

        with self.subTest("logic rules are restored"):
            self.assertEqual(form_for_restore.formlogic_set.count(), 1)

        with self.subTest("payment backend configuration is restored"):
            self.assertEqual(form_for_restore.payment_backend, "worldline")
            self.assertEqual(
                form_for_restore.payment_backend_options["merchant"], merchant.pspid
            )

        with self.subTest("registration backends are restored"):
            registration_backend = form_for_restore.registration_backends.get()
            self.assertEqual(registration_backend.backend, "email")
            self.assertEqual(registration_backend.options["to_emails"], ["abc@xyz.com"])

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
                    last_version = FormVersion.objects.filter(form=form).order_by(
                        "-created", "-pk"
                    )[0]
                    self.assertEqual(
                        last_version.description,
                        _("Restored form version {version} (from {created}).").format(
                            version=2, created="2022-02-21T18:00:00+00:00"
                        ),
                    )

    def test_restoring_a_version_multiple_times_reuses_data(self):
        # multiple restores (accidentally) must not create garbage form definitions
        form = FormFactory.create(generate_minimal_setup=True)
        fd = form.formstep_set.get().form_definition
        form_for_restore = FormFactory.create()
        version = _prepare_form_version_for_restore(
            form=form, form_for_restore=form_for_restore
        )
        # clear database state
        form.delete()
        fd.delete()

        # do multiple restores
        for __ in range(2):
            form_for_restore.restore_old_version(version.uuid)
            form_for_restore.refresh_from_db()

        self.assertEqual(FormDefinition.objects.count(), 1)

    def test_resolve_existing_reusable_form_definitions(self):
        """
        Test restoring a reusable form definition the same configuration.

        Form definitions that are reusable and have identical configuration are
        reused rather than recreated.
        """
        reusable_fd = FormDefinitionFactory.create(
            is_reusable=True,
            configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "reusableTextfield",
                        "label": "Reusable textfield",
                    },
                ]
            },
        )
        non_reusable_fd = FormDefinitionFactory.create(
            is_reusable=False,
            configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "oneTimeUseTextfield",
                        "label": "One time textfield",
                    },
                ]
            },
        )
        form = FormFactory.create()
        FormStepFactory.create(form=form, form_definition=reusable_fd)
        FormStepFactory.create(form=form, form_definition=non_reusable_fd)
        form_for_restore = FormFactory.create()
        version = _prepare_form_version_for_restore(
            form=form, form_for_restore=form_for_restore
        )

        # restore the form
        form_for_restore.restore_old_version(version.uuid)
        form_for_restore.refresh_from_db()

        step1, step2 = form_for_restore.formstep_set.all()
        with self.subTest("reusable form definition is used in restore"):
            self.assertEqual(step1.form_definition, reusable_fd)

        with self.subTest("non-reusable fd is not used in restore"):
            self.assertNotEqual(step2.form_definition, non_reusable_fd)
            # 2 existing + 1 created during restore
            self.assertEqual(FormDefinition.objects.count(), 3)

    @parametrize("initial_active_state", [True, False])
    def test_form_restores_original_active_state(self, initial_active_state: bool):
        form = FormFactory.create(active=initial_active_state)
        version = FormVersionFactory.create(form=form)
        # Change active state after version was made
        form.active = not initial_active_state
        form.save()

        # Restore the previous version
        form.restore_old_version(version.uuid)

        # refresh DB records
        form.refresh_from_db()
        # Assert active state equals the initial active state
        self.assertEqual(form.active, initial_active_state)

    def test_form_restore_creates_new_resources_when_original_resources_have_been_changed(
        self,
    ):
        # Restoring a form version should use additional resources that conform to the
        # original form. If the original resources have been changed, new resources
        # must be created/used with the original configuration.

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

        with self.subTest("product resource"):
            self.assertEqual(Product.objects.count(), 2)
            new_product = Product.objects.order_by("-pk")[0]
            self.assertEqual(new_product.name, "original product name")
            self.assertEqual(new_product.price, 10)
            self.assertEqual(new_product.information, "original product information")
            self.assertEqual(form.product, new_product)

        with self.subTest("map layers"):
            self.assertEqual(MapTileLayer.objects.count(), 2)
            new_wms_tile_layer = MapWMSTileLayer.objects.order_by("-pk")[0]
            self.assertEqual(new_wms_tile_layer.name, "original wms layer")
            self.assertEqual(new_wms_tile_layer.url, "original-test-wms-url.com")

            self.assertEqual(MapTileLayer.objects.count(), 2)
            new_wmts_tile_layer = MapTileLayer.objects.order_by("-pk")[0]
            self.assertEqual(new_wmts_tile_layer.label, "original wmts layer")
            self.assertEqual(new_wmts_tile_layer.url, "original-test-wmts-url.com")

            form_step = form.formstep_set.get()
            configuration = form_step.form_definition.configuration
            self.assertFormioComponent(
                configuration,
                "map",
                {
                    "tileLayerIdentifier": new_wmts_tile_layer.identifier,
                    "overlays": [
                        {
                            "url": "",
                            "type": "wms",
                            "uuid": str(new_wms_tile_layer.uuid),
                            "label": "Basisregistratie Adressen en Gebouwen (BAG)",
                            "layers": ["pand", "verblijfsobject"],
                        },
                    ],
                },
            )

        with self.subTest("yivi attribute groups"):
            self.assertEqual(AttributeGroup.objects.count(), 2)
            new_attribute_group = AttributeGroup.objects.order_by("-pk")[0]
            self.assertEqual(new_attribute_group.name, "original yivi attribute group")
            self.assertEqual(
                new_attribute_group.description,
                "original yivi attribute group description",
            )
            self.assertEqual(new_attribute_group.attributes, ["original_attribute"])

            auth_backend = form.auth_backends.get()
            self.assertEqual(
                auth_backend.options["additional_attributes_groups"],
                [str(new_attribute_group.uuid)],
            )

    def test_form_restore_matches_other_resources_with_same_data_when_original_resources_have_been_changed(
        self,
    ):
        def _clone[T: models.Model](instance: T) -> T:
            clone = copy.copy(instance)
            if hasattr(clone, "uuid"):
                clone.uuid = uuid.uuid4()  # type: ignore
            clone.pk = None
            clone._state.adding = True
            return clone

        # Create the additional resources.
        original_product = ProductFactory.create(name="product name", price=1)
        new_product = _clone(original_product)
        original_wms_tile_layer = MapWMSTileLayerFactory.create(
            name="wms layer", url="test-wms-url.com"
        )
        new_wms_tile_layer = _clone(original_wms_tile_layer)
        original_wmts_tile_layer = MapTileLayerFactory.create(
            identifier="wmts-layer", label="wmts layer", url="wmts-url.com"
        )
        new_wmts_tile_layer = _clone(original_wmts_tile_layer)
        original_yivi_attribute_group = AttributeGroupFactory.create(
            name="attribute group", attributes=["attribute"]
        )
        new_yivi_attribute_group = _clone(original_yivi_attribute_group)

        # Basic form that implements the additional resources.
        form = FormFactory.create(
            generate_minimal_setup=True,
            product=original_product,
            authentication_backend="yivi_oidc",
            authentication_backend__options={
                "authentication_options": [AuthAttribute.bsn],
                "additional_attributes_groups": [original_yivi_attribute_group.uuid],
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
                        "tileLayerIdentifier": original_wmts_tile_layer.identifier,
                        "overlays": [
                            {
                                "url": "",
                                "type": "wms",
                                "uuid": str(original_wms_tile_layer.uuid),
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
        # Change all the resource data
        original_product.name = "different product name"
        original_product.price = 2
        original_product.save()
        new_product.save()

        original_wms_tile_layer.name = "different wms layer"
        original_wms_tile_layer.url = "different-test-wms-url.com"
        original_wms_tile_layer.save()
        new_wms_tile_layer.save()

        original_wmts_tile_layer.identifier = "different-wmts-layer"
        original_wmts_tile_layer.label = "different wmts layer"
        original_wmts_tile_layer.url = "different-wmts-url.com"
        original_wmts_tile_layer.save()
        new_wmts_tile_layer.save()

        original_yivi_attribute_group.name = "different attribute group"
        original_yivi_attribute_group.attributes = ["different_attribute"]
        original_yivi_attribute_group.save()
        new_yivi_attribute_group.save()

        # Restore the form
        form.restore_old_version(version.uuid)

        # get all fresh DB records
        form.refresh_from_db()

        with self.subTest("product resource"):
            self.assertEqual(Product.objects.count(), 2)  # original + our copy
            self.assertEqual(form.product, new_product)

        with self.subTest("map layers"):
            self.assertEqual(MapTileLayer.objects.count(), 2)  # original + our copy
            self.assertEqual(MapTileLayer.objects.count(), 2)  # original + our copy

            form_step = form.formstep_set.get()
            configuration = form_step.form_definition.configuration
            self.assertFormioComponent(
                configuration,
                "map",
                {
                    "tileLayerIdentifier": new_wmts_tile_layer.identifier,
                    "overlays": [
                        {
                            "url": "",
                            "type": "wms",
                            "uuid": str(new_wms_tile_layer.uuid),
                            "label": "Basisregistratie Adressen en Gebouwen (BAG)",
                            "layers": ["pand", "verblijfsobject"],
                        },
                    ],
                },
            )

        with self.subTest("yivi attribute groups"):
            self.assertEqual(AttributeGroup.objects.count(), 2)  # original + our copy
            auth_backend = form.auth_backends.get()
            self.assertEqual(
                auth_backend.options["additional_attributes_groups"],
                [str(new_yivi_attribute_group.uuid)],
            )

    def test_form_restore_theme_and_category_are_removed_if_not_available(self):
        theme = ThemeFactory.create()
        category = CategoryFactory.create()
        form = FormFactory.create(theme=theme, category=category, product=None)
        # Create form version
        version = FormVersionFactory.create(form=form)
        # We have to decouple category first before we can delete it, otherwise an
        # on_delete PROTECT will be triggered
        form.category = None
        form.save()
        # Delete theme and category
        theme.delete()
        category.delete()

        # Restore previous form version
        form.restore_old_version(version.uuid)

        form.refresh_from_db()
        # Validate that theme and category are both unset
        self.assertIsNone(form.theme)
        self.assertIsNone(form.category)
        # Validate that no new theme or category was created
        self.assertFalse(Theme.objects.exists())
        self.assertFalse(Category.objects.exists())
