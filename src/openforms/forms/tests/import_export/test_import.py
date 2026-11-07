from decimal import Decimal
from io import BytesIO
from textwrap import dedent
from unittest.mock import patch

from django.test import TestCase, override_settings, tag
from django.utils import translation

from digid_eherkenning.choices import DigiDAssuranceLevels
from rest_framework.exceptions import ValidationError
from rest_framework.reverse import reverse
from tablib import Dataset

from openforms.authentication.constants import AuthAttribute
from openforms.authentication.contrib.yivi_oidc.models import AttributeGroup
from openforms.authentication.tests.factories import AttributeGroupFactory
from openforms.config.models import MapTileLayer, MapWMSTileLayer
from openforms.config.tests.factories import (
    MapTileLayerFactory,
    MapWMSTileLayerFactory,
)
from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory
from openforms.emails.tests.factories import ConfirmationEmailTemplateFactory
from openforms.formio.tests.assertions import FormioMixin
from openforms.payments.contrib.worldline.tests.factories import (
    WorldlineMerchantFactory,
)
from openforms.prefill.constants import IdentifierRoles
from openforms.products.tests.factories import ProductFactory
from openforms.variables.constants import (
    DataMappingTypes,
    FormVariableDataTypes,
    FormVariableSources,
)

from ...import_export.service import (
    AdditionalFormConfigurationOptions,
    Artifact,
    FormConfigurationOptions,
    FormExportOptions,
    FormImportOptions,
    get_export_artifact,
    import_form,
    import_form_data,
)
from ...models import Form, FormDefinition, FormStep, FormVariable
from ..factories import (
    FormDefinitionFactory,
    FormFactory,
    FormVariableFactory,
)


class ImportTests(FormioMixin, TestCase):
    def test_exported_zip_file_can_be_imported_without_errors(self):
        # create a form with registration backend, prefill, payment backend & auth
        # backends
        product = ProductFactory.create()
        yivi_attribute_group = AttributeGroupFactory.create()
        wmts_map = MapTileLayerFactory.create()
        wms_map = MapWMSTileLayerFactory.create()
        form = FormFactory.create(
            generate_minimal_setup=True,
            product=product,
            # include prefill configuration
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
                        "tileLayerIdentifier": wmts_map.identifier,
                        "overlays": [
                            {
                                "url": "",
                                "type": "wms",
                                "uuid": str(wms_map.uuid),
                                "label": "Basisregistratie Adressen en Gebouwen (BAG)",
                                "layers": ["pand", "verblijfsobject"],
                            },
                        ],
                    },
                ],
            },
            # ensure there's a registration backend
            registration_backend="email",
            registration_backend_options={
                "to_emails": ["abc@xyz.com"],
            },
            # ensure there's auth configured
            authentication_backend="yivi_oidc",
            authentication_backend__options={
                "authentication_options": [AuthAttribute.bsn],
                "additional_attributes_groups": [
                    yivi_attribute_group.uuid,
                ],
            },
        )
        # set up user defined variable with prefill
        FormVariableFactory.create(
            form=form,
            key="variable_with_demo_prefill",
            user_defined=True,
            prefill_plugin="demo",
            prefill_attribute="random_string",
            prefill_identifier_role=IdentifierRoles.authorizee,
        )
        export_artifact = get_export_artifact(
            form,
            export_options=FormExportOptions(
                remove_sensitive_content=False,
                form_configuration=list(FormConfigurationOptions),
                additional_form_configuration=list(AdditionalFormConfigurationOptions),
            ),
        )
        export_zip = BytesIO()
        export_artifact.write_zip(target=export_zip)
        export_zip.seek(0)
        # delete the configuration/content from the DB and verify they get re-created
        product.delete()
        form.delete()
        AttributeGroup.objects.all().delete()
        FormDefinition.objects.all().delete()
        MapTileLayer.objects.all().delete()
        MapWMSTileLayer.objects.all().delete()

        # now import from the zip file
        form = import_form(
            export_zip,
            import_options=FormImportOptions(
                additional_form_configuration=list(AdditionalFormConfigurationOptions)
            ),
        )

        assert form is not None
        self.assertEqual(Form.objects.count(), 1)
        self.assertEqual(FormDefinition.objects.count(), 1)
        self.assertEqual(FormStep.objects.count(), 1)
        self.assertEqual(FormVariable.objects.count(), 2 + 1)
        self.assertIsNotNone(form.product)
        self.assertEqual(form.registration_backends.count(), 1)
        self.assertEqual(form.auth_backends.count(), 1)
        self.assertEqual(AttributeGroup.objects.count(), 1)
        self.assertEqual(MapTileLayer.objects.count(), 1)
        self.assertEqual(MapWMSTileLayer.objects.count(), 1)

    def test_import_form_with_all_possible_features_in_clean_environment(self):
        assert not Form.objects.exists()
        MapTileLayer.objects.all().delete()
        MapWMSTileLayer.objects.all().delete()
        # integration test that covers the happy flow of form imports where every
        # aspect is imported
        merchant = WorldlineMerchantFactory.create()
        objects_api_group = ObjectsAPIGroupConfigFactory.create(identifier="objects")
        artifact = Artifact(
            forms=[
                {
                    "uuid": "324cadce-a627-4e3f-b117-37ca232f16b2",
                    "name": "Test form",
                    "slug": "test-form",
                    "active": True,
                    "is_deleted": False,
                    "maintenance_mode": False,
                    "auth_backends": [
                        {
                            "backend": "digid",
                            "options": {
                                "loa": "urn:oasis:names:tc:SAML:2.0:ac:classes:Smartcard"
                            },
                        },
                        {
                            "backend": "eherkenning",
                        },
                        {
                            "backend": "yivi_oidc",
                            "options": {
                                "authentication_options": [AuthAttribute.bsn],
                                "additional_attributes_groups": [
                                    "8e8f000c-8cad-4908-b7b8-f5634327a8b0",
                                ],
                            },
                        },
                    ],
                    "auto_login_authentication_backend": "digid",
                    "registration_backends": [
                        {
                            "name": "Email",
                            "key": "smtp",
                            "backend": "email",
                            "options": {
                                "to_emails": ["foo@bar.baz"],
                                "attach_files_to_email": None,
                            },
                        }
                    ],
                    "product": reverse(
                        "api:product-detail",
                        kwargs={"uuid": "368eae85-7047-46f8-8f70-60ca26069cc1"},
                    ),
                    "payment_backend": "worldline",
                    "payment_backend_options": {"merchant": merchant.pspid},
                    "translations": {
                        "nl": {"name": "Testformulier"},
                        "en": {"name": "Test form"},
                    },
                }
            ],
            form_definitions=[
                {
                    "uuid": "35bb5a63-d559-4350-b98e-f066980b8ff2",
                    "name": "Test form definition",
                    "slug": "test-form-definition",
                    "configuration": {
                        "components": [
                            {
                                "type": "textfield",
                                "key": "test-key",
                                "label": "test-key",
                            },
                            {
                                "type": "textfield",
                                "key": "textfield",
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
                                "tileLayerIdentifier": "pdok-basis",
                                "overlays": [
                                    {
                                        "url": "",
                                        "type": "wms",
                                        "uuid": "baa21641-422e-48b8-8ce0-68c314c9713a",
                                        "label": "Basisregistratie Adressen en Gebouwen (BAG)",
                                        "layers": ["pand", "verblijfsobject"],
                                    },
                                ],
                            },
                        ],
                    },
                    "login_required": True,
                    "is_reusable": True,
                    "translations": {
                        "nl": {"name": "Testformulierdefinitie"},
                        "en": {"name": "Test form definition"},
                    },
                }
            ],
            form_steps=[
                {
                    "uuid": "1e9ee006-cc5e-45e1-ab65-17f7fac5ce10",
                    "index": 0,
                    "slug": "step-1",
                    "form_definition": (
                        "http://testserver/api/v2/form-definitions/"
                        "35bb5a63-d559-4350-b98e-f066980b8ff2"
                    ),
                    "is_applicable": True,
                    "translations": {
                        "nl": {"next_text": "Volgende"},
                        "en": {"next_text": "Next"},
                    },
                }
            ],
            form_variables=[
                {
                    "form": "http://testserver/api/v2/forms/324cadce-a627-4e3f-b117-37ca232f16b2",
                    "name": "Test user defined",
                    "key": "test-user-defined",
                    "source": FormVariableSources.user_defined,
                    "service_fetch_configuration": None,
                    "data_type": FormVariableDataTypes.string,
                    "is_sensitive_data": False,
                    "initial_value": "mwapmwapmwap",
                },
                # service fetch configurations are not exported but that shouldn't break
                # import
                {
                    "form": "http://testserver/api/v2/forms/324cadce-a627-4e3f-b117-37ca232f16b2",
                    "name": "Far fetched",
                    "key": "farFetched",
                    "source": FormVariableSources.user_defined,
                    "service_fetch_configuration": {
                        "id": 1,
                        "name": "fetch the breast plate stretcher",
                        "service": "http://testserver/api/v2/services/4",
                        "path": "some/path",
                        "method": "GET",
                        "headers": {},
                        "query_params": {},
                        "data_mapping_type": DataMappingTypes.json_logic,
                        "mapping_expression": {"var": "foo"},
                    },
                    "data_type": FormVariableDataTypes.object,
                    "is_sensitive_data": True,
                    "initial_value": {},
                },
                # user defined variables with prefill
                {
                    "form": "http://testserver/api/v2/forms/324cadce-a627-4e3f-b117-37ca232f16b2",
                    "name": "Variable with prefill",
                    "key": "variable_demo_prefill",
                    "source": FormVariableSources.user_defined,
                    "data_type": FormVariableDataTypes.string,
                    "prefill_plugin": "demo",
                    "prefill_attribute": "random_string",
                    "prefill_identifier_role": IdentifierRoles.authorizee,
                },
                {
                    "form": "http://testserver/api/v2/forms/324cadce-a627-4e3f-b117-37ca232f16b2",
                    "name": "Objects prefill",
                    "key": "variable_objects_prefill",
                    "source": FormVariableSources.user_defined,
                    "data_type": FormVariableDataTypes.object,
                    "prefill_plugin": "objects_api",
                    "prefill_options": {
                        "objects_api_group": objects_api_group.identifier,
                        "objecttype_uuid": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                        "objecttype_version": 3,
                        "variables_mapping": [
                            {
                                "variable_key": "lastName",
                                "target_path": ["name", "last.name"],
                            },
                            {"variable_key": "age", "target_path": ["age"]},
                        ],
                        "auth_attribute_path": ["bsn"],
                    },
                },
            ],
            form_logic=[
                {
                    "uuid": "af9cbc0d-af10-47a9-9a65-4ba41f05a549",
                    "order": 0,
                    "form": "http://testserver/api/v2/forms/324cadce-a627-4e3f-b117-37ca232f16b2",
                    "json_logic_trigger": {"!": {"var": "farFetched"}},
                    "is_advanced": True,
                    "actions": [
                        {
                            "action": {"type": "fetch-from-service"},
                            "variable": "farFetched",
                        }
                    ],
                },
                {
                    "uuid": "e2ef49a3-4809-4806-9855-5f3d54c67c70",
                    "order": 1,
                    "form": "http://testserver/api/v2/forms/324cadce-a627-4e3f-b117-37ca232f16b2",
                    "json_logic_trigger": {"==": [{"var": "test-user-defined"}, 1]},
                    "is_advanced": False,
                    "actions": [
                        {
                            "action": {"type": "step-not-applicable"},
                            "form_step_uuid": "1e9ee006-cc5e-45e1-ab65-17f7fac5ce10",
                        },
                    ],
                },
            ],
            product=Dataset(
                (
                    "368eae85-7047-46f8-8f70-60ca26069cc1",
                    "A product",
                    "10,00",
                    "",
                ),
                headers=("uuid", "name", "price", "information"),
            ),
            wms_tile_layers=Dataset(
                (
                    "baa21641-422e-48b8-8ce0-68c314c9713a",
                    "BAG",
                    "https://example.com",
                ),
                headers=("uuid", "name", "url"),
            ),
            wmts_tile_layers=Dataset(
                ("pdok-basis", "PDOK basis", "https://example.com"),
                headers=("identifier", "label", "url"),
            ),
            yivi_attribute_groups=Dataset(
                (
                    "8e8f000c-8cad-4908-b7b8-f5634327a8b0",
                    "some attributes",
                    "",
                    "foo,bar",
                ),
                headers=("uuid", "name", "description", "attributes"),
            ),
        )

        form = import_form_data(
            artifact,
            import_options=FormImportOptions(
                additional_form_configuration=list(AdditionalFormConfigurationOptions),
            ),
        )
        step = None

        assert form is not None

        with self.subTest(feature="form details"):
            # expect a new UUID to be assigned
            self.assertNotEqual(form.uuid, "324cadce-a627-4e3f-b117-37ca232f16b2")
            self.assertEqual(form.slug, "test-form")
            self.assertFalse(form._is_deleted)
            self.assertFalse(form.maintenance_mode)
            # imported forms are deactivated
            self.assertFalse(form.active)
            # test that translations are imported
            with translation.override("en"):
                self.assertEqual(form.name, "Test form")
            with translation.override("nl"):
                self.assertEqual(form.name, "Testformulier")

        with self.subTest(feature="form product"):
            self.assertIsNotNone(form.product)
            # exact UUID does not match, so it's imported as a new record
            self.assertNotEqual(
                str(form.product.uuid), "368eae85-7047-46f8-8f70-60ca26069cc1"
            )
            self.assertEqual(form.product.price, Decimal("10.00"))
            self.assertEqual(form.product.name, "A product")

        with self.subTest(feature="registration"):
            # we expect exactly one backend to be imported
            registration_backend = form.registration_backends.get()
            self.assertEqual(registration_backend.name, "Email")
            self.assertEqual(registration_backend.key, "smtp")
            self.assertEqual(registration_backend.backend, "email")
            self.assertEqual(
                registration_backend.options,
                {
                    "to_emails": ["foo@bar.baz"],
                    "attach_files_to_email": None,
                },
            )

        auth_backends = {
            backend.backend: backend
            for backend in form.auth_backends.order_by("backend")
        }
        with self.subTest(feature="authentication"):
            self.assertEqual(len(auth_backends), 3)

            digid = auth_backends["digid"]
            self.assertEqual(
                digid.options,
                {"loa": "urn:oasis:names:tc:SAML:2.0:ac:classes:Smartcard"},
            )

            eherkenning = auth_backends["eherkenning"]
            self.assertIsNone(eherkenning.options)

        with self.subTest(feature="authentication (yivi)"):
            yivi = auth_backends["yivi_oidc"]
            attribute_group = AttributeGroup.objects.get()
            self.assertEqual(attribute_group.name, "some attributes")
            self.assertEqual(attribute_group.attributes, ["foo", "bar"])
            self.assertEqual(
                yivi.options["additional_attributes_groups"],
                [str(attribute_group.uuid)],
            )

        with self.subTest(feature="payment"):
            self.assertEqual(form.payment_backend, "worldline")
            self.assertEqual(
                form.payment_backend_options,
                {
                    "merchant": merchant.pspid,
                    "variant": "",
                    "descriptor_template": "",
                },
            )

        with self.subTest(feature="form steps"):
            # we expect the single form step and definition to be imported
            step = form.formstep_set.get()
            # a new UUID gets assigned
            self.assertNotEqual(step.uuid, "1e9ee006-cc5e-45e1-ab65-17f7fac5ce10")
            self.assertEqual(step.order, 0)
            self.assertEqual(step.slug, "step-1")
            self.assertTrue(step.is_applicable)
            # translations are imported
            with translation.override("en"):
                self.assertEqual(step.next_text, "Next")
            with translation.override("nl"):
                self.assertEqual(step.next_text, "Volgende")

            fd = step.form_definition
            # a new UUID gets assigned
            self.assertNotEqual(fd.uuid, "35bb5a63-d559-4350-b98e-f066980b8ff2")
            self.assertEqual(fd.slug, "test-form-definition")
            self.assertTrue(fd.is_reusable)
            self.assertTrue(fd.login_required)
            self.assertEqual(len(components := fd.configuration["components"]), 3)
            self.assertComponentProperties(
                components[0],
                {
                    "type": "textfield",
                    "key": "test-key",
                    "label": "test-key",
                },
            )
            # translations are imported
            with translation.override("en"):
                self.assertEqual(fd.name, "Test form definition")
            with translation.override("nl"):
                self.assertEqual(fd.name, "Testformulierdefinitie")
            # a form variable is created for the component
            form_var_qs = form.formvariable_set.filter(
                key="test-key", source=FormVariableSources.component
            )
            self.assertTrue(form_var_qs.exists())

        with self.subTest(feature="map layers"):
            map = components[2]
            map_tile_layer = MapTileLayer.objects.get()  # WMTS
            self.assertEqual(map_tile_layer.label, "PDOK basis")
            self.assertEqual(map_tile_layer.url, "https://example.com")

            wms_tile_layer = MapWMSTileLayer.objects.get()
            self.assertEqual(wms_tile_layer.name, "BAG")
            self.assertEqual(wms_tile_layer.url, "https://example.com")

            self.assertComponentProperties(
                map,
                {
                    "tileLayerIdentifier": "pdok-basis",
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

        with self.subTest(feature="variables"):
            user_defined_variables = {
                variable.key: variable
                for variable in form.formvariable_set.filter(
                    source=FormVariableSources.user_defined
                )
            }

            user_defined_var_1 = user_defined_variables["test-user-defined"]
            self.assertEqual(user_defined_var_1.data_type, FormVariableDataTypes.string)
            self.assertFalse(user_defined_var_1.is_sensitive_data)
            self.assertEqual(user_defined_var_1.initial_value, "mwapmwapmwap")

            user_defined_var_2 = user_defined_variables["farFetched"]
            self.assertEqual(user_defined_var_2.data_type, FormVariableDataTypes.object)
            self.assertTrue(user_defined_var_2.is_sensitive_data)
            self.assertEqual(user_defined_var_2.initial_value, {})
            self.assertIsNone(user_defined_var_2.service_fetch_configuration)

        with self.subTest(feature="prefill"):
            textfield = components[1]
            self.assertComponentProperties(
                textfield,
                {
                    "prefill": {
                        "plugin": "demo",
                        "attribute": "random_number",
                        "identifier_role": IdentifierRoles.authorizee,
                    },
                },
            )

            demo_prefill_variable = user_defined_variables["variable_demo_prefill"]
            self.assertEqual(demo_prefill_variable.prefill_plugin, "demo")
            self.assertEqual(demo_prefill_variable.prefill_attribute, "random_string")
            self.assertEqual(
                demo_prefill_variable.prefill_identifier_role,
                IdentifierRoles.authorizee,
            )

            objects_prefill_variable = user_defined_variables[
                "variable_objects_prefill"
            ]
            self.assertEqual(objects_prefill_variable.prefill_plugin, "objects_api")
            self.assertEqual(
                objects_prefill_variable.prefill_options,
                {
                    "objects_api_group": objects_api_group.identifier,
                    "objecttype_uuid": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                    "objecttype_version": 3,
                    "variables_mapping": [
                        {
                            "variable_key": "lastName",
                            "target_path": ["name", "last.name"],
                        },
                        {"variable_key": "age", "target_path": ["age"]},
                    ],
                    "auth_attribute_path": ["bsn"],
                },
            )

        with self.subTest(feature="logic"):
            rules = form.formlogic_set.order_by("order")
            self.assertEqual(len(rules), 2)
            rule_1, rule_2 = rules

            self.assertEqual(rule_1.json_logic_trigger, {"!": {"var": "farFetched"}})
            # expect a new UUID to be assigned
            self.assertNotEqual(rule_1.uuid, "af9cbc0d-af10-47a9-9a65-4ba41f05a549")
            self.assertEqual(
                rule_1.actions,
                [
                    {
                        "action": {"type": "fetch-from-service", "value": ""},
                        "variable": "farFetched",
                    }
                ],
            )

            self.assertEqual(
                rule_2.json_logic_trigger, {"==": [{"var": "test-user-defined"}, 1]}
            )
            # expect a new UUID to be assigned
            self.assertNotEqual(rule_2.uuid, "e2ef49a3-4809-4806-9855-5f3d54c67c70")
            self.assertNotEqual(
                rule_2.actions[0]["form_step_uuid"],
                "1e9ee006-cc5e-45e1-ab65-17f7fac5ce10",
            )
            self.assertEqual(
                rule_2.actions[0],
                {
                    "action": {"type": "step-not-applicable"},
                    "form_step_uuid": (step and str(step.uuid)),
                },
            )

    def test_import_does_not_break_on_broken_product_theme_category_refs(self):
        artifact = Artifact(
            forms=[
                {
                    "name": "Test form",
                    "slug": "test-form",
                    # product references were always cleared before OF 4.1 - as of 4.1
                    # with the rework, the product is exported alongside the form or the
                    # reference is cleared
                    "product": None,
                    "category": reverse(
                        "api:categories-detail",
                        kwargs={"uuid": "a1b4906f-99b5-45b6-8066-62aee9cf6f27"},
                    ),
                    "theme": reverse(
                        "api:themes-detail",
                        kwargs={"uuid": "3c8851f0-c250-4a24-8610-44a29faa3fe2"},
                    ),
                }
            ],
            form_definitions=[],
            form_steps=[],
            form_variables=[],
            form_logic=[],
        )

        form = import_form_data(artifact, import_options=FormImportOptions())

        assert form is not None
        self.assertIsNone(form.product)
        self.assertIsNone(form.category)
        self.assertIsNone(form.theme)

    def test_import_form_with_duplicated_slug_gets_a_suffix(self):
        FormFactory.create(slug="my-slug")
        artifact = Artifact(
            forms=[
                {
                    "name": "Test form",
                    "slug": "my-slug",
                }
            ],
            form_definitions=[],
            form_steps=[],
            form_variables=[],
            form_logic=[],
        )

        form = import_form_data(artifact, import_options=FormImportOptions())

        assert form is not None
        self.assertEqual(Form.objects.count(), 2)  # check that a new form was imported
        # the duplicated slug gets a random suffix
        self.assertRegex(form.slug, r"^my-slug-[0-9a-z]{6}$")

    def test_import_does_not_duplicate_identical_reusable_form_definitions(self):
        # the importer matches existing form definitions on the exact same configuration
        formio_configuration = {
            "components": [
                {
                    "type": "textfield",
                    "key": "test-key",
                    "label": "test-key",
                }
            ]
        }
        form_definition = FormDefinitionFactory.create(
            configuration=formio_configuration,
            is_reusable=True,
        )
        artifact = Artifact(
            forms=[{"name": "Test form", "slug": "my-slug"}],
            form_definitions=[
                {
                    "uuid": "35bb5a63-d559-4350-b98e-f066980b8ff2",
                    "name": "Irrelevant",
                    "slug": "Irrelevant",
                    "configuration": formio_configuration,
                    "is_reusable": True,
                }
            ],
            form_steps=[
                {
                    "uuid": "1e9ee006-cc5e-45e1-ab65-17f7fac5ce10",
                    "index": 0,
                    "slug": "step-1",
                    "form_definition": (
                        "http://testserver/api/v2/form-definitions/"
                        "35bb5a63-d559-4350-b98e-f066980b8ff2"
                    ),
                }
            ],
            form_variables=[],
            form_logic=[],
        )

        form = import_form_data(artifact, import_options=FormImportOptions())

        assert form is not None
        step = form.formstep_set.get()
        self.assertEqual(FormDefinition.objects.count(), 1)
        self.assertEqual(step.form_definition, form_definition)

    @tag("gh-1906")
    def test_import_creates_new_form_configuration_for_differing_configurations(self):
        # despite the form definitions in database & export file having the same UUID,
        # we still create a new form definition because the configuration is different
        form_definition = FormDefinitionFactory.create(
            uuid="63067a59-ace8-42ca-b04a-4f0c14c583c3",
            name="Reusable form definition",
            slug="fd-1",
            configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "test-key",
                        "label": "test-key",
                    }
                ]
            },
            is_reusable=True,
        )
        artifact = Artifact(
            forms=[{"name": "Test form", "slug": "my-slug"}],
            form_definitions=[
                {
                    "uuid": "63067a59-ace8-42ca-b04a-4f0c14c583c3",
                    "name": "Reusable form definition",
                    "slug": "fd-1",
                    "configuration": {
                        "components": [
                            {
                                "type": "textfield",
                                "key": "test-key-2",  # different component key
                                "label": "test-key",
                            }
                        ]
                    },
                    "is_reusable": True,
                }
            ],
            form_steps=[
                {
                    "uuid": "1e9ee006-cc5e-45e1-ab65-17f7fac5ce10",
                    "index": 0,
                    "slug": "step-1",
                    "form_definition": (
                        "http://testserver/api/v2/form-definitions/"
                        "63067a59-ace8-42ca-b04a-4f0c14c583c3"
                    ),
                }
            ],
            form_variables=[],
            form_logic=[],
        )

        form = import_form_data(artifact, import_options=FormImportOptions())

        assert form is not None
        step = form.formstep_set.get()
        self.assertEqual(FormDefinition.objects.count(), 2)
        self.assertNotEqual(step.form_definition, form_definition)
        self.assertNotEqual(
            step.form_definition.uuid, "63067a59-ace8-42ca-b04a-4f0c14c583c3"
        )
        self.assertEqual(
            step.form_definition.configuration,
            {
                "components": [
                    {
                        "type": "textfield",
                        "key": "test-key-2",  # different component key
                        "label": "test-key",
                    }
                ]
            },
        )

    @override_settings(LANGUAGE_CODE="nl")
    def test_translations_survive_an_export_import_roundtrip(self):
        form = FormFactory.create(
            # set required untranslated string
            name="Untranslated form name",
            submission_confirmation_template="Untranslated submission confirmation template",
            begin_text="Untranslated begin text",
            previous_text="Untranslated previous text",
            change_text="Untranslated change text",
            confirm_text="Untranslated confirm text",
            explanation_template="Some explanations template",
            # English translations
            translation_enabled=True,
            name_en="Some form name translation",
            submission_confirmation_template_en="Some submission confirmation template translation",
            begin_text_en="Some begin text translation",
            previous_text_en="Some previous text translation",
            change_text_en="Some change text translation",
            confirm_text_en="Some confirm text translation",
            explanation_template_en="Some explanations template",
            # form step and definition
            generate_minimal_setup=True,
            formstep__previous_text="Untranslated previous step text",
            formstep__save_text="Untranslated save step text",
            formstep__next_text="Untranslated next step text",
            formstep__previous_text_en="Some previous step text translation",
            formstep__save_text_en="Some save step text translation",
            formstep__next_text_en="Some next step text translation",
            formstep__form_definition__name="Untranslated form definition name",
            formstep__form_definition__name_en="Some form definition name translation",
        )
        email_template = ConfirmationEmailTemplateFactory.create(
            form=form,
            subject="Untranslated confirmation email subject",
            content=dedent(
                """
                        Untranslated confirmation email content with the obligatory
                        {% cosign_information %}
                        {% appointment_information %}
                        {% payment_information %}
                        """
            ).strip(),
            subject_en="Some confirmation email subject translation",
            content_en=dedent(
                """
                Some confirmation email content translation with the obligatory
                {% cosign_information %}
                {% appointment_information %}
                {% payment_information %}
                """
            ).strip(),
        )

        # export in English, while the default language is NL
        with translation.override("en"):
            artifact = get_export_artifact(form, export_options=FormExportOptions())
        # delete database state
        email_template.delete()
        form.delete()
        FormDefinition.objects.all().delete()

        # now do the actual import
        imported_form = import_form_data(artifact, import_options=FormImportOptions())
        assert imported_form is not None

        with self.subTest(verify_translations_of="form"):
            with translation.override("nl"):
                self.assertEqual(imported_form.name, "Untranslated form name")
                self.assertEqual(
                    imported_form.submission_confirmation_template,
                    "Untranslated submission confirmation template",
                )
                self.assertEqual(imported_form.begin_text, "Untranslated begin text")
                self.assertEqual(
                    imported_form.previous_text, "Untranslated previous text"
                )
                self.assertEqual(imported_form.change_text, "Untranslated change text")
                self.assertEqual(
                    imported_form.confirm_text, "Untranslated confirm text"
                )
                self.assertEqual(
                    imported_form.explanation_template, "Some explanations template"
                )

            with translation.override("en"):
                self.assertEqual(imported_form.name, "Some form name translation")
                self.assertEqual(
                    imported_form.submission_confirmation_template,
                    "Some submission confirmation template translation",
                )
                self.assertEqual(
                    imported_form.begin_text, "Some begin text translation"
                )
                self.assertEqual(
                    imported_form.previous_text, "Some previous text translation"
                )
                self.assertEqual(
                    imported_form.change_text, "Some change text translation"
                )
                self.assertEqual(
                    imported_form.confirm_text, "Some confirm text translation"
                )
                self.assertEqual(
                    imported_form.explanation_template, "Some explanations template"
                )

        with self.subTest(verify_translations_of="form step"):
            step = imported_form.formstep_set.get()
            with translation.override("nl"):
                self.assertEqual(step.previous_text, "Untranslated previous step text")
                self.assertEqual(step.save_text, "Untranslated save step text")
                self.assertEqual(step.next_text, "Untranslated next step text")
            with translation.override("en"):
                self.assertEqual(
                    step.previous_text, "Some previous step text translation"
                )
                self.assertEqual(step.save_text, "Some save step text translation")
                self.assertEqual(step.next_text, "Some next step text translation")

        with self.subTest(verify_translations_of="form definition"):
            fd = step.form_definition
            with translation.override("nl"):
                self.assertEqual(fd.name, "Untranslated form definition name")
            with translation.override("en"):
                self.assertEqual(fd.name, "Some form definition name translation")

        with self.subTest(verify_translations_of="confirmation email template"):
            template = imported_form.confirmation_email_template
            with translation.override("nl"):
                self.assertEqual(
                    template.subject, "Untranslated confirmation email subject"
                )
                self.assertEqual(
                    template.content,
                    dedent(
                        """
                        Untranslated confirmation email content with the obligatory
                        {% cosign_information %}
                        {% appointment_information %}
                        {% payment_information %}
                        """
                    ).strip(),  # trailing newline
                )
            with translation.override("en"):
                self.assertEqual(
                    template.subject,
                    "Some confirmation email subject translation",
                )
                self.assertEqual(
                    template.content,
                    dedent(
                        """
                        Some confirmation email content translation with the obligatory
                        {% cosign_information %}
                        {% appointment_information %}
                        {% payment_information %}
                        """
                    ).strip(),  # trailing newline
                )

    def test_export_import_export_roundtrip_produces_same_resources(self):
        form = FormFactory.create(generate_minimal_setup=True)
        email_template = ConfirmationEmailTemplateFactory.create(
            form=form, with_tags=True
        )
        artifact = get_export_artifact(form, export_options=FormExportOptions())
        original_resources = artifact.as_resources_mapping(encode=False)
        # delete database state
        email_template.delete()
        form.delete()
        FormDefinition.objects.all().delete()

        imported_form = import_form_data(artifact, import_options=FormImportOptions())
        assert imported_form is not None

        # create an export from the imported form, and compare against the initial
        # export - these should be (near) identical
        imported_form_artifact = get_export_artifact(
            imported_form, export_options=FormExportOptions()
        )
        resources_to_verify = imported_form_artifact.as_resources_mapping(encode=False)
        assert original_resources.keys() == resources_to_verify.keys()

        for part, expected_data in original_resources.items():
            imported_data = resources_to_verify[part]

            def _delete_keys(*keys: str):
                for key in keys:
                    for expected_item in expected_data:  # noqa: B023
                        del expected_item[key]
                    for imported_item in imported_data:  # noqa: B023
                        del imported_item[key]

            # ignore data that's known to differ, like newly generated UUIDs
            match part:
                case "_meta":
                    continue  # irrelevant for the form content itself
                case "forms":
                    _delete_keys(
                        "uuid",  # import gets assigned a new one
                        "url",  # contains uuid
                        "active",  # import gets set to inactive
                        "category",  # gets unset
                        "steps",  # duplicated in formSteps
                    )
                case "formSteps":
                    _delete_keys(
                        "form_definition",  # is a url with uuid
                        "uuid",
                        "url",
                    )
                case "formDefinitions":
                    _delete_keys("uuid", "url")
                    # TODO: msgspec rework will also require ignoring the configuration
                    # field, as it will normalize partial definitions
                case _:
                    pass

            with self.subTest("verify roundtrip", part=part):
                self.assertEqual(imported_data, expected_data)


class ComponentConversionTests(FormioMixin, TestCase):
    """
    Test the component converter application during import.
    """

    def test_import_applies_converters(self):
        def add_foo(component):
            component["foo"] = "bar"
            return True

        CONVERTERS = {"textfield": {"add_foo": add_foo}}

        artifact = Artifact(
            forms=[{"name": "Test form", "slug": "my-slug"}],
            form_definitions=[
                {
                    "uuid": "63067a59-ace8-42ca-b04a-4f0c14c583c3",
                    "name": "Test",
                    "slug": "fd-1",
                    "configuration": {
                        "components": [
                            {
                                "type": "textfield",
                                "key": "textfield",
                                "label": "textfield",
                            },
                            {
                                "type": "email",
                                "key": "nottextfield",
                                "label": "nottextfield",
                            },
                        ]
                    },
                }
            ],
            form_steps=[
                {
                    "uuid": "1e9ee006-cc5e-45e1-ab65-17f7fac5ce10",
                    "index": 0,
                    "slug": "step-1",
                    "form_definition": (
                        "http://testserver/api/v2/form-definitions/"
                        "63067a59-ace8-42ca-b04a-4f0c14c583c3"
                    ),
                }
            ],
            form_variables=[],
            form_logic=[],
        )

        with patch(
            "openforms.forms.import_export.serializers.form_definition.CONVERTERS",
            new=CONVERTERS,
        ):
            form = import_form_data(artifact, import_options=FormImportOptions())

        assert form is not None
        fd = form.formstep_set.get().form_definition
        self.assertFormioComponent(
            fd.configuration,
            "textfield",
            {
                "type": "textfield",
                "key": "textfield",
                "label": "textfield",
                "foo": "bar",
            },
        )
        self.assertFormioComponentPropertyAbsent(
            fd.configuration, "nottextfield", "foo"
        )

    @tag("gh-3964")
    def test_simple_conditionals_stringified_numbers_converted_to_numbers(self):
        """
        Assert that form imports correct broken conditional configurations.

        The conditional.eq must be data-type aware of the target component it's
        comparing against.
        """
        artifact = Artifact(
            forms=[{"name": "Test form", "slug": "my-slug"}],
            form_definitions=[
                {
                    "uuid": "63067a59-ace8-42ca-b04a-4f0c14c583c3",
                    "name": "Test",
                    "slug": "fd-1",
                    "configuration": {
                        "components": [
                            {
                                "key": "number",
                                "type": "number",
                                "label": "Number",
                            },
                            {
                                "key": "currency",
                                "type": "currency",
                                "label": "Currency",
                            },
                            {
                                "key": "textfield",
                                "type": "textfield",
                                "label": "Text Field",
                            },
                            {
                                "key": "textArea1",
                                "type": "textarea",
                                "label": "Text Area 1",
                                "conditional": {
                                    "eq": "0",
                                    "show": True,
                                    "when": "number",
                                },
                                "clearOnHide": True,
                            },
                            {
                                "key": "textArea2",
                                "type": "textarea",
                                "label": "Text Area 2",
                                "conditional": {
                                    "eq": "0.555",
                                    "show": True,
                                    "when": "number",
                                },
                                "clearOnHide": True,
                            },
                            {
                                "key": "textArea3",
                                "type": "textarea",
                                "label": "Text Area 3",
                                "conditional": {"eq": "", "show": None, "when": ""},
                                "clearOnHide": True,
                            },
                            {
                                "key": "textArea4",
                                "type": "textarea",
                                "label": "Text Area 4",
                                "conditional": {
                                    "when": "currency",
                                    "eq": "0.55",
                                    "show": True,
                                },
                                "clearOnHide": True,
                            },
                            {
                                "key": "textArea5",
                                "type": "textarea",
                                "label": "Text Area 5",
                                "conditional": {
                                    "eq": "1.00",
                                    "when": "currency",
                                    "show": True,
                                },
                                "clearOnHide": True,
                            },
                            {
                                "key": "textArea6",
                                "type": "textarea",
                                "label": "Text Area 6",
                                "conditional": {
                                    "eq": "1.00",
                                    "when": "textfield",
                                    "show": True,
                                },
                                "clearOnHide": True,
                            },
                            {
                                "key": "repeatingGroup",
                                "type": "editgrid",
                                "label": "Repeating group",
                                "groupLabel": "Item",
                                "components": [
                                    {
                                        "key": "textArea7",
                                        "type": "textarea",
                                        "label": "Text Area 7",
                                        "conditional": {
                                            "eq": "0",
                                            "show": True,
                                            "when": "number",
                                        },
                                        "clearOnHide": True,
                                    },
                                ],
                            },
                            {
                                "key": "textArea8",
                                "type": "textarea",
                                "label": "Text Area 8",
                                "conditional": {
                                    "eq": 0,
                                    "show": True,
                                    "when": "number",
                                },
                                "clearOnHide": True,
                            },
                        ]
                    },
                }
            ],
            form_steps=[
                {
                    "uuid": "1e9ee006-cc5e-45e1-ab65-17f7fac5ce10",
                    "index": 0,
                    "slug": "step-1",
                    "form_definition": (
                        "http://testserver/api/v2/form-definitions/"
                        "63067a59-ace8-42ca-b04a-4f0c14c583c3"
                    ),
                }
            ],
            form_variables=[],
            form_logic=[],
        )

        form = import_form_data(artifact, import_options=FormImportOptions())

        assert form is not None
        configuration = form.formstep_set.get().form_definition.configuration

        self.assertFormioComponentPropertyAbsent(configuration, "number", "conditional")
        self.assertFormioComponentPropertyAbsent(
            configuration, "currency", "conditional"
        )
        self.assertFormioComponentPropertyAbsent(
            configuration, "textfield", "conditional"
        )
        self.assertFormioComponent(
            configuration,
            "textArea1",
            {"conditional": {"eq": 0, "show": True, "when": "number"}},
        )
        self.assertFormioComponent(
            configuration,
            "textArea2",
            {"conditional": {"eq": 0.555, "show": True, "when": "number"}},
        )
        self.assertFormioComponent(
            configuration, "textArea3", {"conditional": {"show": None}}
        )
        self.assertFormioComponent(
            configuration,
            "textArea4",
            {"conditional": {"eq": 0.55, "show": True, "when": "currency"}},
        )
        self.assertFormioComponent(
            configuration,
            "textArea5",
            {"conditional": {"eq": 1.00, "show": True, "when": "currency"}},
        )
        self.assertFormioComponent(
            configuration,
            "textArea6",
            {"conditional": {"eq": "1.00", "show": True, "when": "textfield"}},
        )
        self.assertFormioComponent(
            configuration,
            "textArea7",
            {"conditional": {"eq": 0, "show": True, "when": "number"}},
        )
        self.assertFormioComponent(
            configuration,
            "textArea8",
            {"conditional": {"eq": 0, "show": True, "when": "number"}},
        )


class AuthBackendsConversionTests(TestCase):
    def test_old_auth_backends_format_without_options_is_converted(self):
        artifact = Artifact(
            forms=[
                {
                    "name": "Test form",
                    "slug": "my-slug",
                    "authentication_backends": ["digid", "demo"],
                },
            ],
            form_definitions=[],
            form_steps=[],
            form_variables=[],
            form_logic=[],
        )

        form = import_form_data(artifact, import_options=FormImportOptions())

        assert form is not None
        authentication_backends = {
            backend.backend: backend
            for backend in form.auth_backends.order_by("backend")
        }
        self.assertEqual(len(authentication_backends), 2)
        demo = authentication_backends["demo"]
        self.assertIsNone(demo.options)
        digid = authentication_backends["digid"]
        self.assertEqual(digid.options, {"loa": ""})

    def test_old_auth_backends_format_with_only_options_is_converted(self):
        artifact = Artifact(
            forms=[
                {
                    "name": "Test form",
                    "slug": "my-slug",
                    "authentication_backend_options": {
                        "digid": {
                            "loa": DigiDAssuranceLevels.substantial,
                            "unknown_attribute": "will be removed",
                        }
                    },
                },
            ],
            form_definitions=[],
            form_steps=[],
            form_variables=[],
            form_logic=[],
        )

        form = import_form_data(artifact, import_options=FormImportOptions())

        assert form is not None
        digid = form.auth_backends.first()
        assert digid is not None, "Backend expected to be imported from options"
        self.assertEqual(digid.backend, "digid")
        # Unknown attributes are expected to be removed
        self.assertEqual(digid.options, {"loa": DigiDAssuranceLevels.substantial})

    def test_both_backends_without_options_and_with_options_are_converted(self):
        artifact = Artifact(
            forms=[
                {
                    "name": "Test form",
                    "slug": "my-slug",
                    "authentication_backends": ["demo"],
                    "authentication_backend_options": {
                        "digid": {
                            "loa": DigiDAssuranceLevels.substantial,
                            "unknown_attribute": "will be removed",
                        }
                    },
                },
            ],
            form_definitions=[],
            form_steps=[],
            form_variables=[],
            form_logic=[],
        )

        form = import_form_data(artifact, import_options=FormImportOptions())

        assert form is not None
        authentication_backends = {
            backend.backend: backend
            for backend in form.auth_backends.order_by("backend")
        }
        self.assertEqual(len(authentication_backends), 2)
        demo = authentication_backends["demo"]
        self.assertIsNone(demo.options)
        digid = authentication_backends["digid"]
        self.assertEqual(digid.options, {"loa": DigiDAssuranceLevels.substantial})

    def test_mix_of_new_and_old_data_gets_merged(self):
        artifact = Artifact(
            forms=[
                {
                    "name": "Test form",
                    "slug": "my-slug",
                    # new
                    "auth_backends": [
                        {
                            "backend": "demo",
                            "options": None,
                        },
                        {
                            "backend": "digid",
                            "options": {
                                "loa": DigiDAssuranceLevels.substantial,
                            },
                        },
                        {
                            "backend": "eherkenning",
                            "options": None,
                        },
                    ],
                    # legacy
                    "authentication_backends": ["demo", "digid", "digid_oidc"],
                    "authentication_backend_options": {
                        "demo": {
                            "some_custom_attribute": "will be added",
                        },
                        "digid": {
                            "loa": DigiDAssuranceLevels.high,
                        },
                    },
                },
            ],
            form_definitions=[],
            form_steps=[],
            form_variables=[],
            form_logic=[],
        )

        form = import_form_data(artifact, import_options=FormImportOptions())

        assert form is not None
        authentication_backends = {
            backend.backend: backend
            for backend in form.auth_backends.order_by("backend")
        }
        self.assertEqual(len(authentication_backends), 4)

        # Because the demo `auth_backends` plugin options where undefined, the config was
        # supplied by `authentication_backend_options`
        with self.subTest(backend="demo"):
            demo = authentication_backends["demo"]
            self.assertEqual(demo.options, {"some_custom_attribute": "will be added"})

        # Config defined in `auth_backends` plugins will be used in favor of
        # `authentication_backend_options`
        with self.subTest(backend="digid"):
            digid = authentication_backends["digid"]
            self.assertEqual(
                digid.options,
                {"loa": DigiDAssuranceLevels.substantial.value},
            )

        # Plugins that exist in `auth_backends`, but not in `authentication_backends`,
        # will remain
        with self.subTest(backend="eherkenning"):
            eherkenning = authentication_backends["eherkenning"]
            self.assertIsNone(eherkenning.options)

        # Plugins that exist in `authentication_backends`, but not in `auth_backends`,
        # will be added
        with self.subTest(backend="digid_oidc"):
            digid_oidc = authentication_backends["digid_oidc"]
            self.assertIsNone(digid_oidc.options)

    def test_yivi_attribute_groups_name_references_converted_to_uuids(self):
        AttributeGroupFactory.create(
            name="group_1", uuid="a1c9df69-927c-4390-be26-f39daf107691"
        )
        AttributeGroupFactory.create(
            name="group_2", uuid="5da6539b-6f3c-451a-a591-9083bb94d70e"
        )
        artifact = Artifact(
            forms=[
                {
                    "name": "Test form",
                    "slug": "my-slug",
                    "auth_backends": [
                        {
                            "backend": "yivi_oidc",
                            "options": {
                                "authentication_options": ["bsn", "kvk"],
                                "additional_attributes_groups": [
                                    # name, to be converted to UUID during import
                                    "group_2",
                                    # The uuid of the existing attribute group
                                    "a1c9df69-927c-4390-be26-f39daf107691",
                                ],
                                # "bsn_loa": DigiDAssuranceLevels.substantial,
                                # "kvk_loa": AssuranceLevels.low,
                            },
                        }
                    ],
                },
            ],
            form_definitions=[],
            form_steps=[],
            form_variables=[],
            form_logic=[],
        )

        form = import_form_data(
            artifact,
            import_options=FormImportOptions(
                additional_form_configuration=[
                    AdditionalFormConfigurationOptions.yivi_attribute_groups
                ],
            ),
        )

        assert form is not None
        yivi_backend = form.auth_backends.get()
        self.assertEqual(
            set(yivi_backend.options["additional_attributes_groups"]),
            {
                "a1c9df69-927c-4390-be26-f39daf107691",
                "5da6539b-6f3c-451a-a591-9083bb94d70e",
            },
        )


class AuthBackendValidationTests(TestCase):
    def test_backend_is_required_and_must_be_known(self):
        artifact = Artifact(
            forms=[
                {
                    "name": "Test form",
                    "slug": "my-slug",
                    "auth_backends": [
                        # 'backend' key missing
                        {
                            "options": {
                                "loa": DigiDAssuranceLevels.substantial,
                                "unknown_attribute": "will be removed",
                            }
                        },
                        # unknown backend
                        {
                            "backend": "unknown_backend",
                        },
                    ],
                },
            ],
            form_definitions=[],
            form_steps=[],
            form_variables=[],
            form_logic=[],
        )

        with self.assertRaises(ValidationError) as exc_context:
            import_form_data(artifact, import_options=FormImportOptions())

        assert isinstance(exc_context.exception.detail, dict)
        errors = exc_context.exception.detail["auth_backends"]

        self.assertEqual(
            errors[0]["backend"][0].code,  # pyright: ignore[reportArgumentType,reportAttributeAccessIssue, reportCallIssue]
            "required",
        )
        self.assertEqual(
            errors[1]["backend"][0].code,  # pyright: ignore[reportArgumentType,reportAttributeAccessIssue, reportCallIssue]
            "invalid",
        )

    def test_yivi_attribute_group_uuids_must_be_known(self):
        AttributeGroupFactory.create(
            name="some_known_scope", uuid="447aad2c-dc7d-4220-ba5c-dd15183c7a02"
        )
        artifact = Artifact(
            forms=[
                {
                    "name": "Test form",
                    "slug": "my-slug",
                    "auth_backends": [
                        {
                            "backend": "yivi_oidc",
                            "options": {
                                "additional_attributes_groups": [
                                    # A known uuid
                                    "447aad2c-dc7d-4220-ba5c-dd15183c7a02",
                                    # An unknown/invalid uuid
                                    "86ed3db9-8aad-4d9d-a516-a4c3794ed036",
                                ]
                            },
                        }
                    ],
                },
            ],
            form_definitions=[],
            form_steps=[],
            form_variables=[],
            form_logic=[],
        )

        with self.assertRaises(ValidationError) as exc_context:
            import_form_data(
                artifact,
                import_options=FormImportOptions(
                    additional_form_configuration=[
                        AdditionalFormConfigurationOptions.yivi_attribute_groups
                    ],
                ),
            )

        assert isinstance(exc_context.exception.detail, dict)
        errors = exc_context.exception.detail["auth_backends"]
        self.assertEqual(
            errors[0]["options"]["additional_attributes_groups"][0].code,  # pyright: ignore[reportArgumentType,reportAttributeAccessIssue, reportCallIssue]
            "does_not_exist",
        )


class StUFZDSConversionTests(TestCase):
    def test_conversion_to_variables_mapping(self):
        artifact = Artifact(
            forms=[
                {
                    "name": "Test form",
                    "slug": "my-slug",
                    "registration_backends": [
                        {
                            "name": "StUF-ZDS",
                            "key": "stuf-zds",
                            "backend": "stuf-zds-create-zaak",
                            "options": {
                                "payment_status_update_mapping": [
                                    {
                                        "stuf_name": "payment_completed",
                                        "form_variable": "payment_completed",
                                    },
                                    {
                                        "stuf_name": "payment_amount",
                                        "form_variable": "payment_amount",
                                    },
                                    {
                                        "stuf_name": "payment_public_order_ids",
                                        "form_variable": "payment_public_order_ids",
                                    },
                                    {
                                        "stuf_name": "provider_payment_ids",
                                        "form_variable": "provider_payment_ids",
                                    },
                                ],
                                "zds_zaaktype_code": "test",
                                "zds_zaaktype_status_code": "",
                                "zds_zaaktype_omschrijving": "",
                                "zds_zaakdoc_vertrouwelijkheid": "OPENBAAR",
                                "zds_zaaktype_status_omschrijving": "",
                                "zds_documenttype_omschrijving_inzending": "",
                            },
                        }
                    ],
                },
            ],
            form_definitions=[],
            form_steps=[],
            form_variables=[],
            form_logic=[],
        )

        form = import_form_data(artifact, import_options=FormImportOptions())

        assert form is not None
        backend = form.registration_backends.get()
        self.assertEqual(backend.backend, "stuf-zds-create-zaak")
        self.assertNotIn("payment_status_update_mapping", backend.options)
        self.assertEqual(
            backend.options["variables_mapping"],
            [
                {
                    "stuf_name": "payment_completed",
                    "form_variable": "payment_completed",
                    "serialize_list_to_csv": False,
                },
                {
                    "stuf_name": "payment_amount",
                    "form_variable": "payment_amount",
                    "serialize_list_to_csv": False,
                },
                {
                    "stuf_name": "payment_public_order_ids",
                    "form_variable": "payment_public_order_ids",
                    "serialize_list_to_csv": False,
                },
                {
                    "stuf_name": "provider_payment_ids",
                    "form_variable": "provider_payment_ids",
                    "serialize_list_to_csv": False,
                },
            ],
        )
