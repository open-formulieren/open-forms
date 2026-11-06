from io import BytesIO
from unittest.mock import patch

from django.test import TestCase, tag
from django.utils import translation

from rest_framework.reverse import reverse

from openforms.authentication.constants import AuthAttribute
from openforms.authentication.contrib.yivi_oidc.models import AttributeGroup
from openforms.authentication.tests.factories import AttributeGroupFactory
from openforms.config.models import MapTileLayer, MapWMSTileLayer
from openforms.config.tests.factories import (
    MapTileLayerFactory,
    MapWMSTileLayerFactory,
)
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
    # CategoryFactory,
    FormDefinitionFactory,
    FormFactory,
    #     FormLogicFactory,
    #     FormStepFactory,
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
                form_configuration=list(FormConfigurationOptions),
                additional_form_configuration=list(AdditionalFormConfigurationOptions),
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
        # integration test that covers the happy flow of form imports where every
        # aspect is imported
        merchant = WorldlineMerchantFactory.create()
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
        )

        form = import_form_data(
            artifact,
            import_options=FormImportOptions(
                form_configuration=list(FormConfigurationOptions),
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

        with self.subTest(feature="authentication"):
            auth_backends = form.auth_backends.order_by("backend")
            # we expect exactly 2 backends
            digid, eherkenning = auth_backends
            self.assertEqual(digid.backend, "digid")
            self.assertEqual(
                digid.options,
                {"loa": "urn:oasis:names:tc:SAML:2.0:ac:classes:Smartcard"},
            )
            self.assertEqual(eherkenning.backend, "eherkenning")
            self.assertIsNone(eherkenning.options)

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
            self.assertEqual(len(components := fd.configuration["components"]), 1)
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
