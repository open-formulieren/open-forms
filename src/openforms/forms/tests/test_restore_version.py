import copy
import datetime
import json
import uuid

from django.test import TestCase
from django.utils import translation
from django.utils.translation import gettext as _

from freezegun import freeze_time

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
from openforms.forms.models import Category, FormDefinition, FormStep, FormVersion
from openforms.payments.contrib.worldline.tests.factories import (
    WorldlineMerchantFactory,
)
from openforms.prefill.constants import IdentifierRoles
from openforms.products.models import Product
from openforms.products.tests.factories import ProductFactory
from openforms.variables.constants import FormVariableDataTypes, FormVariableSources

from .factories import (
    CategoryFactory,
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
    FormVariableFactory,
    FormVersionFactory,
)
from .utils import EXPORT_BLOB


class RestoreVersionTest(TestCase):
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

    @freeze_time("2022-02-21T17:00:00Z")
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

        with freeze_time("2022-02-21T18:00:00Z"):
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

    def test_full_form_save_and_restore(self):
        """
        Tests that all form configuration that receives dedicated attention from the
        import/export is correctly saved and restored.

        Ensuring all configuration is kept, especially the product, theme, category, and
        service fetch. (@TODO service fetch is not yet implemented)
        """
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
        self.assertEqual(MapTileLayer.objects.count(), 6)
        self.assertEqual(MapWMSTileLayer.objects.count(), 2)
        self.assertEqual(AttributeGroup.objects.count(), 1)

        version = FormVersionFactory.create(form=form)
        self.assertNotEqual(version.export_blob, {})

        # Restore it
        form.restore_old_version(version.uuid)

        # get all fresh DB records
        form.refresh_from_db()

        # Validate that no new additional data was created
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(Theme.objects.count(), 1)
        self.assertEqual(Category.objects.count(), 1)
        self.assertEqual(MapTileLayer.objects.count(), 6)
        self.assertEqual(MapWMSTileLayer.objects.count(), 2)
        self.assertEqual(AttributeGroup.objects.count(), 1)

        # Validate product, theme and category
        self.assertEqual(form.product.uuid, product.uuid)
        self.assertEqual(form.theme.uuid, theme.uuid)
        self.assertEqual(form.category.uuid, category.uuid)

        # Validate payment backend
        self.assertEqual(form.payment_backend, "worldline")
        self.assertEqual(form.payment_backend_options["merchant"], merchant.pspid)

        # Validate auth backend
        self.assertEqual(form.auth_backends.count(), 1)
        auth_backend = form.auth_backends.first()
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
            form.internal_remark,
            "Some internal remark that should be kept",
        )
        self.assertEqual(form.registration_backends.count(), 1)
        registration_backend = form.registration_backends.first()
        self.assertEqual(registration_backend.backend, "email")
        self.assertEqual(registration_backend.options["to_emails"], ["abc@xyz.com"])

        # Validate map component tile layer configuration
        fd = form.formstep_set.first().form_definition
        map_component = fd.configuration["components"][1]
        self.assertEqual(map_component["type"], "map")
        self.assertEqual(
            map_component["tileLayerIdentifier"], wmts_tile_layer.identifier
        )
        self.assertEqual(len(map_component["overlays"]), 1)
        self.assertEqual(map_component["overlays"][0]["uuid"], str(wms_tile_layer.uuid))

    def test_form_restore_creating_new_resources_when_existing_have_been_altered(self):
        product = ProductFactory.create()
        theme = ThemeFactory.create(design_token_values={"key": "token"})
        category = CategoryFactory.create()

        form = FormFactory.create(
            product=product,
            theme=theme,
            category=category,
        )
        version = FormVersionFactory.create(form=form)
        self.assertNotEqual(version.export_blob, {})

        # now delete the product, and update the theme and category
        with self.subTest("Modify used resources"):
            product.delete()
            theme.organization_name = "Evil .inc"
            category.uuid = uuid.uuid4()

            self.assertEqual(Product.objects.count(), 0)
            self.assertEqual(Theme.objects.count(), 1)
            self.assertEqual(Category.objects.count(), 1)

        # Restore it
        form.restore_old_version(version.uuid)

        # get all fresh DB records
        form.refresh_from_db()

        # Because the product was deleted, a new product is created
        self.assertEqual(Product.objects.count(), 1)
        new_product = Product.objects.first()
        self.assertEqual(form.product.uuid, new_product.uuid)

        # Because the theme was modified, a new theme is created. This ensures that the
        # existing theme, which could be used in other forms, doesn't change.
        self.assertEqual(Theme.objects.count(), 2)
        new_theme = Theme.objects.first()
        self.assertEqual(form.theme.uuid, new_theme.uuid)

        # Because we don't use the uuid as an identifier for the resources, we can re-use
        # the category that was used in the original form.
        self.assertEqual(Category.objects.count(), 1)
        self.assertEqual(form.category.uuid, category.uuid)


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
