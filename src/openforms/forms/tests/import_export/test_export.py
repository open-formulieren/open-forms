import json
import zipfile
from io import BytesIO

from django.http import HttpResponse
from django.test import TestCase, tag

import msgspec
from tablib import Dataset

from openforms.authentication.constants import AuthAttribute
from openforms.authentication.tests.factories import AttributeGroupFactory
from openforms.config.tests.factories import (
    MapTileLayerFactory,
    MapWMSTileLayerFactory,
    ThemeFactory,
)
from openforms.prefill.constants import IdentifierRoles
from openforms.products.tests.factories import ProductFactory
from openforms.variables.constants import FormVariableSources

from ...import_export.service import (
    AdditionalFormConfigurationOptions,
    FormConfigurationOptions,
    FormExportOptions,
    export_form,
    get_export_artifact,
)
from ..factories import (
    CategoryFactory,
    FormDefinitionFactory,
    FormFactory,
    FormLogicFactory,
    FormStepFactory,
    FormVariableFactory,
)


class ExportTests(TestCase):
    def test_contains_expected_resources(self):
        form = FormFactory.create(authentication_backend="demo")
        form_definition = FormDefinitionFactory.create()
        FormStepFactory.create(form=form, form_definition=form_definition)
        FormStepFactory.create()
        FormLogicFactory.create(
            form=form,
            actions=[
                {
                    "component": "test_component",
                    "action": {
                        "type": "set-registration-backend",
                        "value": "foo",
                    },
                }
            ],
        )
        FormVariableFactory.create(
            form=form, source=FormVariableSources.user_defined, key="test-user-defined"
        )

        export = get_export_artifact(form, export_options=FormExportOptions())
        export_data = export.as_resources_mapping()

        with self.subTest("included resources check"):
            self.assertEqual(
                set(export_data),
                {
                    "forms",
                    "formSteps",
                    "formDefinitions",
                    "formLogic",
                    "formVariables",
                    "_meta",
                },
            )

        with self.subTest("forms resource smoketest"):
            forms = export_data["forms"]
            self.assertEqual(len(forms), 1)
            form_data = forms[0]

            self.assertEqual(form_data["uuid"], str(form.uuid))
            self.assertEqual(form_data["name"], form.name)
            self.assertEqual(form_data["internal_name"], form.internal_name)
            self.assertEqual(form_data["slug"], form.slug)
            self.assertEqual(
                form_data["auth_backends"],
                [
                    {
                        "backend": "demo",
                        "options": {},
                    }
                ],
            )
            assert isinstance(form_data["steps"], list)
            self.assertEqual(len(form_data["steps"]), form.formstep_set.count())
            self.assertEqual(form_data["product"], "")

        with self.subTest("form definitions resource smoketest"):
            form_definitions = export_data["formDefinitions"]
            self.assertEqual(len(form_definitions), 1)

            form_definition_data = form_definitions[0]
            self.assertEqual(form_definition_data["uuid"], str(form_definition.uuid))
            self.assertEqual(form_definition_data["name"], form_definition.name)
            self.assertEqual(
                form_definition_data["internal_name"], form_definition.internal_name
            )
            self.assertEqual(form_definition_data["slug"], form_definition.slug)
            self.assertEqual(
                form_definition_data["configuration"],
                form_definition.configuration,
            )

        with self.subTest("form steps resource smoketest"):
            form_steps = export_data["formSteps"]
            self.assertEqual(len(form_steps), 1)
            form_step_data = form_steps[0]
            self.assertEqual(
                form_step_data["configuration"], form_definition.configuration
            )

        with self.subTest("form logic resource smoketest"):
            rules = export_data["formLogic"]
            self.assertEqual(len(rules), 1)

            form_logic_data = rules[0]
            assert isinstance(form_logic_data["actions"], list)
            action = form_logic_data["actions"][0]
            assert isinstance(action, dict)
            self.assertEqual("test_component", action["component"])
            self.assertEqual(
                {"type": "set-registration-backend", "value": "foo"},
                action["action"],
            )
            assert isinstance(form_logic_data["form"], str)
            self.assertIn(str(form.uuid), form_logic_data["form"])

        with self.subTest("form variables resource smoketest"):
            form_variables = export_data["formVariables"]
            # Only user defined form variables are included in the export
            self.assertEqual(len(form_variables), 1)
            variable_data = form_variables[0]
            self.assertEqual(variable_data["source"], FormVariableSources.user_defined)

    def test_zipfile_contains_json_resources(self):
        # use a response as outfile - in practice we can write to anything file-like,
        # but this is effectively used in the admin/API.
        response = HttpResponse(content_type="application/zip", status=200)
        form = FormFactory.create(generate_minimal_setup=True)

        export_form(form.pk, FormExportOptions(), response=response)

        with zipfile.ZipFile(BytesIO(response.content), "r") as export_zip:
            files_in_zip = set(export_zip.namelist())
            expected_files = {
                "forms.json",
                "formSteps.json",
                "formDefinitions.json",
                "formLogic.json",
                "formVariables.json",
                "_meta.json",
            }

            self.assertEqual(files_in_zip, expected_files)

            for expected_file in expected_files:
                json_content = export_zip.read(expected_file)
                # verify that it's valid JSON
                with self.subTest(file=expected_file):
                    try:
                        json.loads(json_content)
                    except json.JSONDecodeError as exc:
                        raise self.failureException("Couldn't parse JSON") from exc

    @tag("gh-1906")
    def test_reusable_form_definition_does_not_apply_dynamic_rewriting(self):
        # uses file component because that gets dynamically rewritten for
        # a request by deriving the allowedTypesLabels from file.type
        file_component = {
            "type": "file",
            "key": "test-key",
            "url": "http://testserver/api/v2/formio/fileupload",
            "label": "test-key",
            "file": {"type": []},
            "filePattern": "",
        }
        assert "allowedTypesLabels" not in file_component["file"]
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={"components": [file_component]},
            formstep__form_definition__is_reusable=True,
        )
        fd = form.formstep_set.get().form_definition

        export = get_export_artifact(form, export_options=FormExportOptions())

        self.assertEqual(len(export.form_definitions), 1)
        exported_fd = export.form_definitions[0]
        self.assertEqual(exported_fd["uuid"], str(fd.uuid))
        self.assertEqual(exported_fd["name"], fd.name)
        self.assertEqual(exported_fd["internal_name"], fd.internal_name)
        self.assertEqual(exported_fd["slug"], fd.slug)
        self.assertEqual(exported_fd["configuration"], fd.configuration)

    def test_resets_submission_counter(self):
        form = FormFactory.create(submission_counter=10)

        export = get_export_artifact(form, export_options=FormExportOptions())

        assert len(export.forms) == 1
        form_data = export.forms[0]
        self.assertEqual(form_data["submission_counter"], 0)

    def test_anonymize_option_drives_export_content(self):
        # Set up a form with sensitive data in:
        # - form internal remarks
        # - user defined variable initial value
        # - user defined variable in logic rule
        # - e-mail address in e-mail registration to_emails
        # - e-mail address in e-mail registration payment_emails
        form = FormFactory.create(
            internal_remarks="Some internal remark that should be kept",
            registration_backend="email",
            registration_backend_options={
                "to_emails": ["submission@company.com"],
                "to_emails_from_variable": "variable_with_sensitive_data",
                "payment_emails": ["payment@company.com"],
            },
        )
        FormVariableFactory.create(
            form=form,
            user_defined=True,
            key="variable_with_sensitive_data",
            initial_value="personal@company.com",
        )
        FormVariableFactory.create(form=form, user_defined=True, key="trigger")
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "trigger"}, 1]},
            actions=[
                {
                    "variable": "variable_with_sensitive_data",
                    "action": {"type": "variable", "value": "internal@company.com"},
                }
            ],
        )

        with self.subTest(remove_sensitive_content=False):
            export = get_export_artifact(
                form,
                export_options=FormExportOptions(
                    remove_sensitive_content=False,
                    form_configuration=[FormConfigurationOptions.registration_backends],
                ),
            )

            assert len(export.forms) == 1
            form_data = export.forms[0]
            assert len(export.form_logic) == 1
            rule_data = export.form_logic[0]
            assert len(export.form_variables) == 2
            form_variables = {
                variable["key"]: variable for variable in export.form_variables
            }

            # Internal remarks should be kept
            self.assertEqual(
                form_data["internal_remarks"],
                "Some internal remark that should be kept",
            )

            # E-mail addresses and variable assigned to registration backend should be
            # kept
            self.assertEqual(len(form_data["registration_backends"]), 1)
            registration_backend = form_data["registration_backends"][0]
            self.assertEqual(
                registration_backend["options"]["to_emails"], ["submission@company.com"]
            )
            self.assertEqual(
                registration_backend["options"]["to_emails_from_variable"],
                "variable_with_sensitive_data",
            )
            self.assertEqual(
                registration_backend["options"]["payment_emails"],
                ["payment@company.com"],
            )

            # The initial data of the user-defined variable used by the e-mail
            # registration backend should be kept
            sensitive_variable = form_variables["variable_with_sensitive_data"]
            self.assertEqual(
                sensitive_variable["initial_value"], "personal@company.com"
            )

            # The logic rule that assigns the value of the sensitive user-defined
            # variable is kept
            self.assertEqual(len(rule_data["actions"]), 1)
            self.assertEqual(
                rule_data["actions"][0]["variable"], "variable_with_sensitive_data"
            )
            self.assertEqual(
                rule_data["actions"][0]["action"],
                {"type": "variable", "value": "internal@company.com"},
            )

        with self.subTest(remove_sensitive_content=True):
            export = get_export_artifact(
                form,
                export_options=FormExportOptions(
                    remove_sensitive_content=True,
                    form_configuration=[FormConfigurationOptions.registration_backends],
                ),
            )

            assert len(export.forms) == 1
            form_data = export.forms[0]
            assert len(export.form_logic) == 1
            rule_data = export.form_logic[0]
            assert len(export.form_variables) == 2
            form_variables = {
                variable["key"]: variable for variable in export.form_variables
            }

            # Internal remarks should be removed
            self.assertNotIn("internal_remarks", form_data)

            # E-mail addresses assigned in the registration backend should be cleared
            # The variable assigned in the registration backend should be kept
            self.assertEqual(len(form_data["registration_backends"]), 1)
            registration_backend = form_data["registration_backends"][0]

            self.assertEqual(registration_backend["options"]["to_emails"], [])
            self.assertEqual(
                registration_backend["options"]["to_emails_from_variable"],
                "variable_with_sensitive_data",
            )
            self.assertEqual(
                registration_backend["options"]["payment_emails"],
                [],
            )

            # The initial data of the user-defined variable used by the e-mail
            # registration backend should be cleared
            sensitive_variable = form_variables["variable_with_sensitive_data"]
            self.assertEqual(sensitive_variable["initial_value"], "")

            # The logic rule that assigns the value of the sensitive user-defined
            # variable is cleared
            self.assertEqual(len(rule_data["actions"]), 1)
            self.assertEqual(
                rule_data["actions"][0]["variable"], "variable_with_sensitive_data"
            )
            self.assertEqual(
                rule_data["actions"][0]["action"],
                {"type": "variable", "value": ""},
            )

    def test_anonymize_option_anonymizes_referenced_component_variable(self):
        # Set up a form with sensitive data in:
        # - component variable initial value
        # - component variable in logic rule
        form = FormFactory.create(
            generate_minimal_setup=True,
            registration_backend="email",
            registration_backend_options={"to_emails_from_variable": "textfield"},
            formstep__form_definition__configuration={
                "components": [
                    # put it in a nested fieldset to ensure nesting is covered as well
                    {
                        "key": "fieldset",
                        "label": "Fieldset",
                        "type": "fieldset",
                        "components": [
                            {
                                "key": "textfield",
                                "type": "textfield",
                                "label": "Textfield",
                                "defaultValue": "personal@me.com",
                            },
                        ],
                    },
                ],
            },
        )
        FormVariableFactory.create(form=form, user_defined=True, key="trigger")
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "trigger"}, 1]},
            actions=[
                {
                    "variable": "textfield",
                    "action": {"type": "variable", "value": "internal@company.com"},
                }
            ],
        )

        export = get_export_artifact(
            form,
            export_options=FormExportOptions(
                remove_sensitive_content=True,
                form_configuration=[FormConfigurationOptions.registration_backends],
            ),
        )

        self.assertEqual(len(export.form_variables), 1)
        with self.subTest("form data"):
            assert len(export.forms) == 1
            form_data = export.forms[0]
            assert len(form_data["registration_backends"]) == 1
            registration_backend = form_data["registration_backends"][0]
            self.assertEqual(
                registration_backend["options"]["to_emails_from_variable"],
                "textfield",
            )

        # The logic rule that assigns the value of the component variable is cleared
        with self.subTest("logic rule data"):
            assert len(export.form_logic) == 1
            rule_data = export.form_logic[0]
            assert len(rule_data["actions"]) == 1
            self.assertEqual(rule_data["actions"][0]["variable"], "textfield")
            self.assertEqual(
                rule_data["actions"][0]["action"],
                {"type": "variable", "value": ""},
            )

        # The default value of the component variable used in the e-mail registration
        # is cleared
        with self.subTest("form definition data"):
            assert len(export.form_definitions) == 1
            fd_data = export.form_definitions[0]
            assert len(fd_data["configuration"]["components"]) == 1
            fieldset = fd_data["configuration"]["components"][0]
            textfield = fieldset["components"][0]
            assert textfield["key"] == "textfield"
            self.assertEqual(textfield["defaultValue"], "")

    def test_export_options_result_in_omitted_export_data(self):
        # create a form with registration backend, prefill, payment backend & auth
        # backends & verify aspects can be excluded
        form = FormFactory.create(
            generate_minimal_setup=True,
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
                ],
            },
            # ensure there's a registration backend
            registration_backend="email",
            registration_backend_options={
                "to_emails": ["abc@xyz.com"],
            },
            # ensure there's payment configuration
            product=ProductFactory.create(),
            payment_backend="worldline",
            payment_backend_options={"merchant": "some-merchant-ref"},
            # ensure there's auth configured
            authentication_backend="digid",
            authentication_backend_options={"digid": {"loa": "some-loa"}},
        )
        # set up user defined variables with prefill
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
                "objects_api_group": "some-identifier",
                "objecttype_uuid": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                "objecttype_version": 3,
                "variables_mapping": [
                    {"variable_key": "lastName", "target_path": ["name", "last.name"]},
                    {"variable_key": "age", "target_path": ["age"]},
                ],
                "auth_attribute_path": ["bsn"],
            },
        )

        export = get_export_artifact(
            form,
            export_options=FormExportOptions(form_configuration=[]),  # export nothing
        )
        assert len(export.forms) == 1
        form_data = export.forms[0]

        with self.subTest(excluded="registration"):
            # Registration backends should not be in exportdata
            self.assertEqual(len(form_data["registration_backends"]), 0)

        with self.subTest(excluded="prefill"):
            assert len(export.form_variables) == 2
            var1, var2 = export.form_variables
            # Both variables should have empty prefill data
            self.assertEqual(var1["prefill_plugin"], "")
            self.assertEqual(var1["prefill_attribute"], "")
            self.assertEqual(var1["prefill_identifier_role"], "authorizee")
            self.assertEqual(var1["prefill_options"], {})

            self.assertEqual(var2["prefill_plugin"], "")
            self.assertEqual(var2["prefill_attribute"], "")
            self.assertEqual(var2["prefill_identifier_role"], "main")
            self.assertEqual(var2["prefill_options"], {})

            assert len(export.form_definitions) == 1
            fd_data = export.form_definitions[0]
            assert len(fd_data["configuration"]["components"]) == 1
            # The component prefill data must be cleared
            component_definition = fd_data["configuration"]["components"][0]
            self.assertEqual(component_definition["prefill"]["plugin"], "")
            self.assertEqual(component_definition["prefill"]["attribute"], "")
            self.assertEqual(
                component_definition["prefill"]["identifier_role"], "authorizee"
            )

        with self.subTest(excluded="payment"):
            self.assertEqual(form_data["payment_backend"], "")
            self.assertEqual(form_data["payment_backend_options"], {})

        with self.subTest(excluded="auth"):
            self.assertEqual(form_data["auth_backends"], [])

    def test_additional_form_configuration_options_drive_export_content(self):
        # create a form that uses all additional configuration types
        product = ProductFactory.create()
        theme = ThemeFactory.create()
        category = CategoryFactory.create()
        yivi_attribute_group1 = AttributeGroupFactory.create(
            attributes=["first_name", "last_name"]
        )
        yivi_attribute_group2 = AttributeGroupFactory.create(
            attributes=["email_address"]
        )
        wmts_map1 = MapTileLayerFactory.create()
        wmts_map2 = MapTileLayerFactory.create()
        wms_map1 = MapWMSTileLayerFactory.create()
        wms_map2 = MapWMSTileLayerFactory.create()
        wms_map3 = MapWMSTileLayerFactory.create()

        form = FormFactory.create(
            generate_minimal_setup=True,
            product=product,
            theme=theme,
            category=category,
            authentication_backend="yivi_oidc",
            authentication_backend__options={
                "authentication_options": [AuthAttribute.bsn],
                "additional_attributes_groups": [
                    # The uuids of the `personal` and `mail` attributegroups
                    yivi_attribute_group1.uuid,
                    yivi_attribute_group2.uuid,
                ],
            },
            formstep__form_definition__configuration={
                "components": [
                    {
                        "label": "Map 1",
                        "key": "map",
                        "type": "map",
                        "useConfigDefaultMapSettings": False,
                        "interactions": {
                            "marker": True,
                            "polygon": False,
                            "polyline": False,
                        },
                        "tileLayerIdentifier": wmts_map1.identifier,
                        "overlays": [
                            {
                                "url": "",
                                "type": "wms",
                                "uuid": str(wms_map1.uuid),
                                "label": "Basisregistratie Adressen en Gebouwen (BAG)",
                                "layers": ["pand", "verblijfsobject"],
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
                        "tileLayerIdentifier": wmts_map2.identifier,
                        "overlays": [
                            {
                                "url": "",
                                "type": "wms",
                                "uuid": str(wms_map2.uuid),
                                "label": "height",
                                "layers": ["EL.GridCoverage"],
                            },
                            {
                                "url": "",
                                "type": "wms",
                                "uuid": str(wms_map3.uuid),
                                "label": "LGN",
                                "layers": ["lgn-actueel"],
                            },
                        ],
                    },
                ],
            },
        )
        setup_auth_backend = form.auth_backends.get()
        setup_fd = form.formstep_set.get().form_definition

        with self.subTest(additional_form_configuration="none"):
            export = get_export_artifact(
                form, export_options=FormExportOptions(additional_form_configuration=[])
            )

            assert len(export.forms) == 1
            self.assertIs(export.product, msgspec.UNSET)
            self.assertIs(export.wms_tile_layers, msgspec.UNSET)
            self.assertIs(export.wmts_tile_layers, msgspec.UNSET)
            self.assertIs(export.yivi_attribute_groups, msgspec.UNSET)
            resources = export.as_resources_mapping(encode=False)
            self.assertEqual(
                set(resources),
                {
                    "forms",
                    "formSteps",
                    "formDefinitions",
                    "formLogic",
                    "formVariables",
                    "_meta",
                },
            )

            form_data = export.forms[0]

            # Assert product is not in exportdata
            self.assertEqual(form_data["product"], "")
            # Assert theme and category are in exportdata
            self.assertEqual(
                form_data["theme"], f"http://testserver/api/v2/themes/{theme.uuid}"
            )
            self.assertEqual(
                form_data["category"],
                f"http://testserver/api/v2/public/categories/{category.uuid}",
            )

            # Assert Yivi authentication_backend is in exportdata, but without
            # additional_attributes_groups
            self.assertEqual(len(form_data["auth_backends"]), 1)
            auth_backend_data = form_data["auth_backends"][0]
            self.assertEqual(auth_backend_data["backend"], "yivi_oidc")
            self.assertEqual(
                auth_backend_data["options"]["additional_attributes_groups"], []
            )
            # Assert that no mutations of the database content are made
            current_auth_backend = form.auth_backends.get()
            self.assertEqual(current_auth_backend.options, setup_auth_backend.options)

            # Assert that the WMS and WMTS tile layers are removed from the exportdata
            assert len(export.form_definitions) == 1
            components = export.form_definitions[0]["configuration"]["components"]
            assert len(components) == 2
            map1, map2 = components

            self.assertEqual(map1["type"], "map")
            self.assertEqual(map1["tileLayerIdentifier"], "")
            self.assertEqual(len(map1["overlays"]), 1)
            self.assertEqual(map1["overlays"][0]["uuid"], "")
            self.assertEqual(map1["overlays"][0]["layers"], [])

            self.assertEqual(map2["type"], "map")
            self.assertEqual(map2["tileLayerIdentifier"], "")
            self.assertEqual(len(map2["overlays"]), 2)
            self.assertEqual(map2["overlays"][0]["uuid"], "")
            self.assertEqual(map2["overlays"][0]["layers"], [])
            self.assertEqual(map2["overlays"][1]["uuid"], "")
            self.assertEqual(map2["overlays"][1]["layers"], [])

            # Assert that no mutations of the database content are made
            current_fd = form.formstep_set.get().form_definition
            self.assertEqual(current_fd.configuration, setup_fd.configuration)

        with self.subTest(additional_form_configuration="everything"):
            export = get_export_artifact(
                form,
                export_options=FormExportOptions(
                    additional_form_configuration=list(
                        AdditionalFormConfigurationOptions
                    )
                ),
            )

            assert len(export.forms) == 1
            form_data = export.forms[0]

            resources = export.as_resources_mapping(encode=False)
            self.assertEqual(
                set(resources),
                {
                    "forms",
                    "formSteps",
                    "formDefinitions",
                    "formLogic",
                    "formVariables",
                    "_meta",
                    "product",
                    "wmsTileLayers",
                    "wmtsTileLayers",
                    "yiviAttributeGroups",
                },
            )

            # check that exporting to ZIP contains the additional resources
            output = BytesIO()
            export.write_zip(output)
            output.seek(0)
            with zipfile.ZipFile(output, "r") as export_zip:
                namelist = export_zip.namelist()
            self.assertIn("product.json", namelist)
            self.assertIn("wmsTileLayers.json", namelist)
            self.assertIn("wmtsTileLayers.json", namelist)
            self.assertIn("yiviAttributeGroups.json", namelist)

            # Assert product, theme and category are in exportdata
            self.assertEqual(
                form_data["product"],
                f"http://testserver/api/v2/products/{product.uuid}",
            )
            self.assertEqual(
                form_data["theme"], f"http://testserver/api/v2/themes/{theme.uuid}"
            )
            self.assertEqual(
                form_data["category"],
                f"http://testserver/api/v2/public/categories/{category.uuid}",
            )

            # Assert Yivi authentication_backend is in exportdata with
            # additional_attributes_groups
            self.assertEqual(len(form_data["auth_backends"]), 1)
            auth_backend_data = form_data["auth_backends"][0]
            self.assertEqual(auth_backend_data["backend"], "yivi_oidc")
            self.assertEqual(
                auth_backend_data["options"]["additional_attributes_groups"],
                [str(yivi_attribute_group1.uuid), str(yivi_attribute_group2.uuid)],
            )

            # Assert WMS and WMTS tile layers are in exportdata
            assert len(export.form_definitions) == 1
            components = export.form_definitions[0]["configuration"]["components"]
            assert len(components) == 2
            map1, map2 = components

            self.assertEqual(map1["type"], "map")
            self.assertEqual(map1["tileLayerIdentifier"], str(wmts_map1.identifier))
            self.assertEqual(len(map1["overlays"]), 1)
            self.assertEqual(map1["overlays"][0]["uuid"], str(wms_map1.uuid))
            self.assertEqual(map1["overlays"][0]["layers"], ["pand", "verblijfsobject"])

            self.assertEqual(map2["type"], "map")
            self.assertEqual(map2["tileLayerIdentifier"], str(wmts_map2.identifier))
            self.assertEqual(len(map2["overlays"]), 2)
            self.assertEqual(map2["overlays"][0]["uuid"], str(wms_map2.uuid))
            self.assertEqual(map2["overlays"][0]["layers"], ["EL.GridCoverage"])
            self.assertEqual(map2["overlays"][1]["uuid"], str(wms_map3.uuid))
            self.assertEqual(map2["overlays"][1]["layers"], ["lgn-actueel"])

            # Validate the export contents
            assert isinstance(export.product, Dataset)
            self.assertEqual(
                export.product.dict,
                [
                    {
                        "uuid": str(product.uuid),
                        "name": product.name,
                        "price": str(product.price).replace(".", ","),
                        "information": product.information,
                    }
                ],
            )

            assert isinstance(export.wms_tile_layers, Dataset)
            self.assertEqual(len(export.wms_tile_layers), 3)
            wms_tile_layer_data = export.wms_tile_layers.dict
            self.assertIn(
                {
                    "uuid": str(wms_map1.uuid),
                    "name": wms_map1.name,
                    "url": wms_map1.url,
                },
                wms_tile_layer_data,
            )
            self.assertIn(
                {
                    "uuid": str(wms_map2.uuid),
                    "name": wms_map2.name,
                    "url": wms_map2.url,
                },
                wms_tile_layer_data,
            )
            self.assertIn(
                {
                    "uuid": str(wms_map3.uuid),
                    "name": wms_map3.name,
                    "url": wms_map3.url,
                },
                wms_tile_layer_data,
            )

            assert isinstance(export.wmts_tile_layers, Dataset)
            self.assertEqual(len(export.wmts_tile_layers), 2)
            wmts_tile_layer_data = export.wmts_tile_layers.dict
            self.assertIn(
                {
                    "identifier": wmts_map1.identifier,
                    "label": wmts_map1.label,
                    "url": wmts_map1.url,
                },
                wmts_tile_layer_data,
            )
            self.assertIn(
                {
                    "identifier": wmts_map2.identifier,
                    "label": wmts_map2.label,
                    "url": wmts_map2.url,
                },
                wmts_tile_layer_data,
            )

            assert isinstance(export.yivi_attribute_groups, Dataset)
            self.assertEqual(len(export.yivi_attribute_groups), 2)
            yivi_attribute_group_data = export.yivi_attribute_groups.dict
            self.assertIn(
                {
                    "uuid": str(yivi_attribute_group1.uuid),
                    "name": yivi_attribute_group1.name,
                    "description": yivi_attribute_group1.description,
                    "attributes": ",".join(yivi_attribute_group1.attributes),
                },
                yivi_attribute_group_data,
            )
            self.assertIn(
                {
                    "uuid": str(yivi_attribute_group2.uuid),
                    "name": yivi_attribute_group2.name,
                    "description": yivi_attribute_group2.description,
                    "attributes": ",".join(yivi_attribute_group2.attributes),
                },
                yivi_attribute_group_data,
            )

    def test_with_unknown_additional_form_configuration_option(self):
        form = FormFactory.create()

        with self.assertRaisesMessage(
            ValueError,
            "Invalid additional form configuration option(s): {'some_unknown_option'}",
        ):
            # Pass some unknown option to the export
            get_export_artifact(
                form,
                export_options=FormExportOptions(
                    additional_form_configuration=["some_unknown_option"],  # pyright: ignore[reportArgumentType]
                ),
            )
