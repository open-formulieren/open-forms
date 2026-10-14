import json
from io import BytesIO
from zipfile import ZipFile

from django.test import override_settings, tag
from django.urls import reverse
from django.utils.translation import gettext as _

from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa

from openforms.accounts.tests.factories import UserFactory
from openforms.authentication.constants import AuthAttribute
from openforms.authentication.contrib.digid.constants import DIGID_DEFAULT_LOA
from openforms.authentication.contrib.yivi_oidc.models import AttributeGroup
from openforms.authentication.tests.factories import AttributeGroupFactory
from openforms.config.models import MapTileLayer, MapWMSTileLayer
from openforms.config.tests.factories import (
    MapTileLayerFactory,
    MapWMSTileLayerFactory,
    ThemeFactory,
)
from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory
from openforms.payments.contrib.worldline.tests.factories import (
    WorldlineMerchantFactory,
)
from openforms.prefill.constants import IdentifierRoles
from openforms.products.models import Product
from openforms.products.tests.factories import ProductFactory
from openforms.utils.tests.feature_flags import enable_feature_flag

from ...import_export.service import (
    EXPORT_META_KEY,
    AdditionalFormConfigurationOptions,
    FormConfigurationOptions,
)
from ...models import Form, FormDefinition
from ...tests.factories import FormDefinitionFactory, FormFactory
from ..factories import (
    CategoryFactory,
    FormLogicFactory,
    FormVariableFactory,
)


@disable_admin_mfa()
class FormAdminExportTests(WebTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory.create(is_superuser=True, is_staff=True)

    def test_form_admin_export(self):
        self.client.force_login(self.user)
        form = FormFactory.create(
            authentication_backend="digid",
            authentication_backend_options={
                "loa": DIGID_DEFAULT_LOA,
            },
        )
        admin_url = reverse("admin:forms_form_change", args=(form.pk,))

        response = self.client.post(admin_url, data={"_export": "Export"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["content-type"], "application/zip")

        zf = ZipFile(BytesIO(response.content))

        self.assertEqual(
            zf.namelist(),
            [
                "forms.json",
                "formSteps.json",
                "formDefinitions.json",
                "formLogic.json",
                "formVariables.json",
                f"{EXPORT_META_KEY}.json",
            ],
        )

        forms = json.loads(zf.read("forms.json"))
        self.assertEqual(len(forms), 1)
        self.assertEqual(forms[0]["uuid"], str(form.uuid))
        self.assertEqual(
            forms[0]["auth_backends"],
            [
                {
                    "backend": "digid",
                    "options": {
                        "loa": DIGID_DEFAULT_LOA,
                    },
                }
            ],
        )

        form_definitions = json.loads(zf.read("formDefinitions.json"))
        self.assertEqual(len(form_definitions), 0)

        form_steps = json.loads(zf.read("formSteps.json"))
        self.assertEqual(len(form_steps), 0)

    def test_form_admin_export_without_unknown_export_options(self):
        self.client.force_login(self.user)

        product = ProductFactory.create()
        form = FormFactory.create(
            internal_remarks="Some internal remark that should be removed",
            product=product,
            registration_backend="demo",
        )
        admin_url = reverse("admin:forms_form_change", args=(form.pk,))

        response = self.client.post(
            admin_url,
            data={
                "_export": "Export",
                "export_options": json.dumps(
                    {
                        "unknown-option": True,
                        "another-unknown-option": "some-value",
                    }
                ),
            },
        )

        # When passing unknown export options, the export should still work
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["content-type"], "application/zip")

        zf = ZipFile(BytesIO(response.content))
        self.assertEqual(
            zf.namelist(),
            [
                "forms.json",
                "formSteps.json",
                "formDefinitions.json",
                "formLogic.json",
                "formVariables.json",
                f"{EXPORT_META_KEY}.json",
            ],
        )

        forms = json.loads(zf.read("forms.json"))

        self.assertEqual(len(forms), 1)

        # We fall back to the default export options, so sensitive data should be removed
        self.assertNotIn("internal_remarks", forms[0])

        # The regular form configuration should be kept
        self.assertEqual(len(forms[0]["registration_backends"]), 1)
        self.assertEqual(forms[0]["registration_backends"][0]["backend"], "demo")

        # Additional form configuration should be removed
        self.assertEqual(forms[0]["product"], "")

    def test_form_admin_export_with_broken_export_options(self):
        self.client.force_login(self.user)

        product = ProductFactory.create()
        form = FormFactory.create(
            internal_remarks="Some internal remark that should be removed",
            product=product,
            registration_backend="demo",
        )
        admin_url = reverse("admin:forms_form_change", args=(form.pk,))

        response = self.client.post(
            admin_url,
            data={
                "_export": "Export",
                "export_options": json.dumps(
                    {
                        # The value of the "remove_sensitive_content" option should be a boolean
                        "remove_sensitive_content": "some unexpected value",
                    }
                ),
            },
        )

        self.assertEqual(response.status_code, 302)

    def test_form_admin_export_with_broken_export_options_invalid_json(self):
        self.client.force_login(self.user)

        product = ProductFactory.create()
        form = FormFactory.create(
            internal_remarks="Some internal remark that should be removed",
            product=product,
            registration_backend="demo",
        )
        admin_url = reverse("admin:forms_form_change", args=(form.pk,))

        response = self.client.post(
            admin_url,
            data={
                "_export": "Export",
                "export_options": '{"broken',
            },
        )

        self.assertEqual(response.status_code, 302)

    def test_form_admin_export_remove_all_sensitive_data(self):
        self.client.force_login(self.user)

        form = FormFactory.create(
            internal_remarks="Some internal remark that should be removed",
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

        admin_url = reverse("admin:forms_form_change", args=(form.pk,))

        response = self.client.post(
            admin_url,
            data={
                "_export": "Export",
                "export_options": json.dumps(
                    {
                        "remove_sensitive_content": True,
                        "form_configuration": [
                            FormConfigurationOptions.registration_backends,
                        ],
                    }
                ),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["content-type"], "application/zip")

        zf = ZipFile(BytesIO(response.content))
        self.assertEqual(
            zf.namelist(),
            [
                "forms.json",
                "formSteps.json",
                "formDefinitions.json",
                "formLogic.json",
                "formVariables.json",
                f"{EXPORT_META_KEY}.json",
            ],
        )

        forms = json.loads(zf.read("forms.json"))
        form_logic = json.loads(zf.read("formLogic.json"))
        form_variables = json.loads(zf.read("formVariables.json"))

        self.assertEqual(len(forms), 1)
        self.assertEqual(len(form_logic), 1)
        self.assertEqual(len(form_variables), 2)

        # Internal remarks should be removed
        self.assertNotIn("internal_remarks", forms[0])

        # E-mail addresses assigned in the registration backend should be cleared
        # The variable assigned in the registration backend should be kept
        self.assertEqual(len(forms[0]["registration_backends"]), 1)
        registration_backend = forms[0]["registration_backends"][0]

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
        sensitive_variable = next(
            variable
            for variable in form_variables
            if variable["key"] == "variable_with_sensitive_data"
        )
        self.assertEqual(sensitive_variable["initial_value"], "")

        # The logic rule that assigns the value of the sensitive user-defined
        # variable is cleared
        self.assertEqual(len(form_logic[0]["actions"]), 1)
        self.assertEqual(
            form_logic[0]["actions"][0]["variable"], "variable_with_sensitive_data"
        )
        self.assertEqual(
            form_logic[0]["actions"][0]["action"],
            {"type": "variable", "value": ""},
        )

    def test_form_admin_export_keep_all_sensitive_data(self):
        self.client.force_login(self.user)

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

        admin_url = reverse("admin:forms_form_change", args=(form.pk,))

        response = self.client.post(
            admin_url,
            data={
                "_export": "Export",
                "export_options": json.dumps(
                    {
                        "remove_sensitive_content": False,
                        "form_configuration": [
                            FormConfigurationOptions.registration_backends,
                        ],
                    }
                ),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["content-type"], "application/zip")

        zf = ZipFile(BytesIO(response.content))
        self.assertEqual(
            zf.namelist(),
            [
                "forms.json",
                "formSteps.json",
                "formDefinitions.json",
                "formLogic.json",
                "formVariables.json",
                f"{EXPORT_META_KEY}.json",
            ],
        )

        forms = json.loads(zf.read("forms.json"))
        form_logic = json.loads(zf.read("formLogic.json"))
        form_variables = json.loads(zf.read("formVariables.json"))

        self.assertEqual(len(forms), 1)
        self.assertEqual(len(form_logic), 1)
        self.assertEqual(len(form_variables), 2)

        # Internal remarks should be left untouched
        self.assertEqual(
            forms[0]["internal_remarks"], "Some internal remark that should be kept"
        )

        # E-mail addresses and variable assigned in the registration backend should be
        # kept.
        self.assertEqual(len(forms[0]["registration_backends"]), 1)
        registration_backend = forms[0]["registration_backends"][0]

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
        sensitive_variable = next(
            variable
            for variable in form_variables
            if variable["key"] == "variable_with_sensitive_data"
        )
        self.assertEqual(sensitive_variable["initial_value"], "personal@company.com")

        # The logic rule that assigns the value of the sensitive user-defined
        # variable is kept
        self.assertEqual(len(form_logic[0]["actions"]), 1)
        self.assertEqual(
            form_logic[0]["actions"][0]["variable"], "variable_with_sensitive_data"
        )
        self.assertEqual(
            form_logic[0]["actions"][0]["action"],
            {"type": "variable", "value": "internal@company.com"},
        )

    def test_form_admin_export_include_all_form_configuration(self):
        self.client.force_login(self.user)

        product = ProductFactory.create()
        merchant = WorldlineMerchantFactory.create()
        objects_api_group = ObjectsAPIGroupConfigFactory.create(
            identifier="test-objects-api-group"
        )
        form = FormFactory.create(
            generate_minimal_setup=True,
            product=product,
            authentication_backend="digid",
            payment_backend="worldline",
            payment_backend_options={"merchant": merchant.pspid},
            registration_backend="email",
            registration_backend_options={
                "to_emails": ["abc@xyz.com"],
            },
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

        admin_url = reverse("admin:forms_form_change", args=(form.pk,))

        response = self.client.post(
            admin_url,
            data={
                "_export": "Export",
                "export_options": json.dumps(
                    {
                        # Keep sensitive data to keep the email registration config complete
                        "remove_sensitive_content": False,
                        "form_configuration": [
                            FormConfigurationOptions.registration_backends,
                            FormConfigurationOptions.prefill,
                            FormConfigurationOptions.payment_backend,
                        ],
                    }
                ),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["content-type"], "application/zip")

        zf = ZipFile(BytesIO(response.content))
        self.assertEqual(
            zf.namelist(),
            [
                "forms.json",
                "formSteps.json",
                "formDefinitions.json",
                "formLogic.json",
                "formVariables.json",
                f"{EXPORT_META_KEY}.json",
            ],
        )

        forms = json.loads(zf.read("forms.json"))
        self.assertEqual(len(forms), 1)

        # Registration backend should be in exportdata
        self.assertEqual(len(forms[0]["registration_backends"]), 1)
        registration_backend = forms[0]["registration_backends"][0]
        self.assertEqual(registration_backend["backend"], "email")
        self.assertEqual(registration_backend["options"]["to_emails"], ["abc@xyz.com"])

        # Payment backend should be in exportdata
        self.assertEqual(forms[0]["payment_backend"], "worldline")
        self.assertEqual(
            forms[0]["payment_backend_options"], {"merchant": merchant.pspid}
        )

        form_variables = json.loads(zf.read("formVariables.json"))
        form_definitions = json.loads(zf.read("formDefinitions.json"))

        self.assertEqual(len(form_variables), 2)
        self.assertEqual(len(form_definitions), 1)

        # Both variables should have their prefill data
        self.assertEqual(form_variables[0]["prefill_plugin"], "demo")
        self.assertEqual(form_variables[0]["prefill_attribute"], "random_string")
        self.assertEqual(form_variables[0]["prefill_identifier_role"], "authorizee")

        self.assertEqual(form_variables[1]["prefill_plugin"], "objects_api")
        self.assertEqual(
            form_variables[1]["prefill_options"],
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

        # The component prefill data should be kept
        self.assertEqual(len(form_definitions[0]["configuration"]["components"]), 1)
        component_definition = form_definitions[0]["configuration"]["components"][0]
        self.assertEqual(component_definition["prefill"]["plugin"], "demo")
        self.assertEqual(component_definition["prefill"]["attribute"], "random_number")
        self.assertEqual(
            component_definition["prefill"]["identifier_role"], "authorizee"
        )

    def test_form_admin_export_exclude_all_form_configuration(self):
        self.client.force_login(self.user)

        product = ProductFactory.create()
        merchant = WorldlineMerchantFactory.create()
        objects_api_group = ObjectsAPIGroupConfigFactory.create(
            identifier="test-objects-api-group"
        )
        form = FormFactory.create(
            generate_minimal_setup=True,
            product=product,
            authentication_backend="digid",
            payment_backend="worldline",
            payment_backend_options={"merchant": merchant.pspid},
            registration_backend="email",
            registration_backend_options={
                "to_emails": ["abc@xyz.com"],
            },
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "textfield",
                        "type": "textfield",
                        "label": "Textfield",
                        "prefill": {
                            "plugin": "demo",
                            "attribute": "random_number",
                            "identifier_role": "authorised_person",
                        },
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
            prefill_identifier_role="authorised_person",
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

        admin_url = reverse("admin:forms_form_change", args=(form.pk,))

        response = self.client.post(
            admin_url,
            data={
                "_export": "Export",
                "export_options": json.dumps(
                    {
                        "form_configuration": [],
                    }
                ),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["content-type"], "application/zip")

        zf = ZipFile(BytesIO(response.content))
        self.assertEqual(
            zf.namelist(),
            [
                "forms.json",
                "formSteps.json",
                "formDefinitions.json",
                "formLogic.json",
                "formVariables.json",
                f"{EXPORT_META_KEY}.json",
            ],
        )

        forms = json.loads(zf.read("forms.json"))
        self.assertEqual(len(forms), 1)

        # Registration backend should not be in exportdata
        self.assertEqual(forms[0]["registration_backends"], [])

        # Payment backend should not be in exportdata
        self.assertEqual(forms[0]["payment_backend"], "")
        self.assertEqual(forms[0]["payment_backend_options"], {})

        form_variables = json.loads(zf.read("formVariables.json"))
        form_definitions = json.loads(zf.read("formDefinitions.json"))

        self.assertEqual(len(form_variables), 2)
        self.assertEqual(len(form_definitions), 1)

        # Both variables should have empty prefill data
        self.assertEqual(form_variables[0]["prefill_plugin"], "")
        self.assertEqual(form_variables[0]["prefill_attribute"], "")
        self.assertEqual(
            form_variables[0]["prefill_identifier_role"], "authorised_person"
        )
        self.assertEqual(form_variables[0]["prefill_options"], {})

        self.assertEqual(form_variables[1]["prefill_plugin"], "")
        self.assertEqual(form_variables[1]["prefill_attribute"], "")
        self.assertEqual(form_variables[1]["prefill_identifier_role"], "main")
        self.assertEqual(form_variables[1]["prefill_options"], {})

        # The component prefill data should be cleared
        self.assertEqual(len(form_definitions[0]["configuration"]["components"]), 1)
        component_definition = form_definitions[0]["configuration"]["components"][0]
        self.assertEqual(component_definition["prefill"]["plugin"], "")
        self.assertEqual(component_definition["prefill"]["attribute"], "")
        self.assertEqual(
            component_definition["prefill"]["identifier_role"], "authorised_person"
        )

    def test_form_admin_export_including_all_additional_form_configuration(self):
        self.client.force_login(self.user)

        product = ProductFactory.create()
        theme = ThemeFactory.create()
        category = CategoryFactory.create()

        wmts_tile_layer = MapTileLayerFactory.create()
        wms_tile_layer = MapWMSTileLayerFactory.create()

        yivi_attribute_group = AttributeGroupFactory.create(
            attributes=["first_name", "last_name"]
        )

        # Define form with all additional form configuration
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

        admin_url = reverse("admin:forms_form_change", args=(form.pk,))

        response = self.client.post(
            admin_url,
            data={
                "_export": "Export",
                "export_options": json.dumps(
                    {
                        "additional_form_configuration": [
                            AdditionalFormConfigurationOptions.product,
                            AdditionalFormConfigurationOptions.wms_tile_layers,
                            AdditionalFormConfigurationOptions.wmts_tile_layers,
                            AdditionalFormConfigurationOptions.yivi_attribute_groups,
                        ]
                    }
                ),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["content-type"], "application/zip")

        zf = ZipFile(BytesIO(response.content))
        self.assertEqual(
            zf.namelist(),
            [
                "forms.json",
                "formSteps.json",
                "formDefinitions.json",
                "formLogic.json",
                "formVariables.json",
                "product.json",
                "wmsTileLayers.json",
                "wmtsTileLayers.json",
                "yiviAttributeGroups.json",
                f"{EXPORT_META_KEY}.json",
            ],
        )

        exported_product = json.loads(zf.read("product.json"))
        self.assertEqual(len(exported_product), 1)
        self.assertEqual(
            exported_product,
            [
                {
                    "uuid": str(product.uuid),
                    "name": product.name,
                    "price": str(product.price).replace(".", ","),
                    "information": product.information,
                }
            ],
        )

        exported_wms_tile_layers = json.loads(zf.read("wmsTileLayers.json"))
        self.assertEqual(len(exported_wms_tile_layers), 1)
        self.assertEqual(
            exported_wms_tile_layers,
            [
                {
                    "uuid": str(wms_tile_layer.uuid),
                    "name": wms_tile_layer.name,
                    "url": wms_tile_layer.url,
                },
            ],
        )

        exported_wmts_tile_layers = json.loads(zf.read("wmtsTileLayers.json"))
        self.assertEqual(len(exported_wmts_tile_layers), 1)
        self.assertEqual(
            exported_wmts_tile_layers,
            [
                {
                    "identifier": wmts_tile_layer.identifier,
                    "label": wmts_tile_layer.label,
                    "url": wmts_tile_layer.url,
                },
            ],
        )

        exported_yivi_attribute_groups = json.loads(zf.read("yiviAttributeGroups.json"))
        self.assertEqual(len(exported_yivi_attribute_groups), 1)
        self.assertEqual(
            exported_yivi_attribute_groups,
            [
                {
                    "uuid": str(yivi_attribute_group.uuid),
                    "name": yivi_attribute_group.name,
                    "description": yivi_attribute_group.description,
                    "attributes": ",".join(yivi_attribute_group.attributes),
                },
            ],
        )

    def test_form_admin_export_excluding_all_additional_form_configuration(self):
        self.client.force_login(self.user)

        product = ProductFactory.create()
        theme = ThemeFactory.create(design_token_values={"key": "token"})
        category = CategoryFactory.create()

        wmts_tile_layer = MapTileLayerFactory.create()
        wms_tile_layer = MapWMSTileLayerFactory.create()

        yivi_attribute_group = AttributeGroupFactory.create(
            attributes=["first_name", "last_name"]
        )

        # Define form with all additional form configuration
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

        admin_url = reverse("admin:forms_form_change", args=(form.pk,))

        response = self.client.post(
            admin_url,
            data={
                "_export": "Export",
                "export_options": json.dumps({"additional_form_configuration": []}),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["content-type"], "application/zip")

        zf = ZipFile(BytesIO(response.content))
        self.assertEqual(
            zf.namelist(),
            [
                "forms.json",
                "formSteps.json",
                "formDefinitions.json",
                "formLogic.json",
                "formVariables.json",
                f"{EXPORT_META_KEY}.json",
            ],
        )

        exported_forms = json.loads(zf.read("forms.json"))
        self.assertEqual(len(exported_forms), 1)

        # The product reference on the form is removed, theme and category are kept
        self.assertEqual(exported_forms[0]["product"], "")
        self.assertIsNotNone(exported_forms[0]["theme"])
        self.assertIsNotNone(exported_forms[0]["category"])


@disable_admin_mfa()
class FormAdminImportTests(WebTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory.create(is_superuser=True, is_staff=True)

    @override_settings(LANGUAGE_CODE="en")
    def test_form_admin_import_button(self):
        response = self.app.get(reverse("admin:forms_form_changelist"), user=self.user)

        response = response.click(href=reverse("admin:forms_import"))

        self.assertEqual(response.status_code, 200)

        # Page should have the import form
        self.assertIn("file", response.form.fields)

    def test_form_admin_import(self):
        file = BytesIO()
        with ZipFile(file, mode="w") as zf:
            with zf.open("forms.json", "w") as f:
                f.write(
                    json.dumps(
                        [
                            {
                                "uuid": "b8315e1d-3134-476f-8786-7661d8237c51",
                                "name": "Form 000",
                                "internal_name": "Form internal",
                                "slug": "bed",
                                "product": None,
                                "authentication_backends": ["digid"],
                            }
                        ]
                    ).encode("utf-8")
                )

            with zf.open("formSteps.json", "w") as f:
                f.write(b"[]")

            with zf.open("formDefinitions.json", "w") as f:
                f.write(b"[]")

            with zf.open("formLogic.json", "w") as f:
                f.write(b"[]")

        response = self.app.get(reverse("admin:forms_import"), user=self.user)

        file.seek(0)

        html_form = response.form
        html_form["file"] = (
            "file.zip",
            file.read(),
        )

        response = html_form.submit("_import")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, reverse("admin:forms_form_changelist"))

        self.assertEqual(Form.objects.count(), 1)

        form = Form.objects.get()
        self.assertNotEqual(form.uuid, "b8315e1d-3134-476f-8786-7661d8237c51")
        self.assertEqual(form.name, "Form 000")
        self.assertEqual(form.internal_name, "Form internal")
        self.assertEqual(form.auth_backends.count(), 1)
        self.assertEqual(form.auth_backends.get().backend, "digid")

    def test_form_admin_import_staff_required(self):
        self.user.is_superuser = False
        self.user.save()

        response = self.app.get(
            reverse("admin:forms_import"), user=self.user, status=403
        )

        self.assertEqual(response.status_code, 403)

    def test_form_admin_import_error(self):
        FormFactory.create(slug="test")

        file = BytesIO()
        with ZipFile(file, mode="w") as zf:
            with zf.open("forms.json", "w") as f:
                f.write(
                    json.dumps(
                        [
                            {
                                "model": "forms.form",
                                "pk": 1,
                                "fields": {
                                    "uuid": "b8315e1d-3134-476f-8786-7661d8237c51",
                                    "name": "Form 000",
                                    "slug": "test",
                                    "active": True,
                                    "product": None,
                                    "backend": "",
                                },
                            }
                        ]
                    ).encode("utf-8")
                )

            with zf.open("formSteps.json", "w") as f:
                f.write(b"[]")

            with zf.open("formDefinitions.json", "w") as f:
                f.write(b"[]")

        response = self.app.get(reverse("admin:forms_import"), user=self.user)

        file.seek(0)

        html_form = response.form
        html_form["file"] = (
            "file.zip",
            file.read(),
        )

        response = html_form.submit("_import")

        self.assertEqual(response.status_code, 200)

        error_message = response.html.find("li", {"class": "error"})
        self.assertTrue(
            error_message.text.startswith(
                _("Something went wrong while importing form: {}").format("")
            )
        )

    @override_settings(LANGUAGE_CODE="en")
    def test_form_admin_import_feedback_messages(self):
        form = FormFactory.create(slug="test")
        form_definition = FormDefinitionFactory.create(slug="testform")

        file = BytesIO()
        with ZipFile(file, mode="w") as zf:
            with zf.open("forms.json", "w") as f:
                f.write(
                    json.dumps(
                        [
                            {
                                "uuid": "2a231070-89c9-45dc-9ff8-ffd80ef15343",
                                "name": "testform",
                                "login_required": False,
                                "product": None,
                                "slug": "testform_old",
                                "url": "http://testserver/api/v2/forms/2a231070-89c9-45dc-9ff8-ffd80ef15343",
                                "steps": [
                                    {
                                        "uuid": "a44c90c5-d0ba-4783-8201-0094a0e44885",
                                        "form_definition": "testform",
                                        "index": 0,
                                        "url": "http://testserver/api/v2/forms/2a231070-89c9-45dc-9ff8-ffd80ef15343/steps/a44c90c5-d0ba-4783-8201-0094a0e44885",
                                    }
                                ],
                            }
                        ]
                    ).encode("utf-8")
                )

            with zf.open("formDefinitions.json", "w") as f:
                f.write(
                    json.dumps(
                        [
                            {
                                "url": "http://testserver/api/v2/form-definitions/78a18366-f9c0-47f2-8fd6-a6c31920440e",
                                "uuid": "78a18366-f9c0-47f2-8fd6-a6c31920440e",
                                "name": "testform",
                                "internal_name": "test internal",
                                "slug": "testform",
                                "configuration": {
                                    "components": [
                                        {
                                            "id": "eer6qln",
                                            "key": "email",
                                            "type": "email",
                                        }
                                    ]
                                },
                                "translations": {
                                    "en": {"name": "testform"},
                                    "nl": {"name": "testformulier"},
                                },
                            }
                        ]
                    ).encode("utf-8")
                )

            with zf.open("formSteps.json", "w") as f:
                f.write(
                    json.dumps(
                        [
                            {
                                "index": 0,
                                "configuration": {
                                    "components": [
                                        {
                                            "id": "eer6qln",
                                            "key": "email",
                                            "type": "email",
                                        }
                                    ]
                                },
                                "form_definition": "http://testserver/api/v2/form-definitions/78a18366-f9c0-47f2-8fd6-a6c31920440e",
                            }
                        ]
                    ).encode("utf-8")
                )

            with zf.open("formLogic.json", "w") as f:
                f.write(b"[]")

        response = self.app.get(reverse("admin:forms_import"), user=self.user)

        file.seek(0)

        html_form = response.form
        html_form["file"] = (
            "file.zip",
            file.read(),
        )

        response = html_form.submit("_import")

        self.assertEqual(response.status_code, 302)

        response = response.follow()

        success_message = response.html.find("li", {"class": "success"})
        self.assertEqual(success_message.text, _("Form successfully imported!"))

        self.assertEqual(Form.objects.count(), 2)

        form = Form.objects.last()
        self.assertNotEqual(form.uuid, "b8315e1d-3134-476f-8786-7661d8237c51")
        self.assertEqual(form.name, "testform")

        self.assertEqual(FormDefinition.objects.count(), 2)

        form_definition = FormDefinition.objects.last()
        self.assertNotEqual(
            form_definition.uuid, "b8315e1d-3134-476f-8786-7661d8237c51"
        )
        self.assertEqual(form_definition.name, "testform")
        self.assertEqual(form_definition.internal_name, "test internal")
        self.assertEqual(form_definition.slug, "testform")

    @tag("gh-2851")
    def test_form_admin_import_with_english_default(self):
        file = BytesIO()
        with ZipFile(file, mode="w") as zf:
            with zf.open("forms.json", "w") as f:
                f.write(
                    json.dumps(
                        [
                            {
                                "uuid": "b8315e1d-3134-476f-8786-7661d8237c51",
                                "name": "Form 000",
                                "internal_name": "Form internal",
                                "slug": "bed",
                                "product": None,
                                "authentication_backends": ["digid"],
                            }
                        ]
                    ).encode("utf-8")
                )

            with zf.open("formSteps.json", "w") as f:
                f.write(b"[]")

            with zf.open("formDefinitions.json", "w") as f:
                f.write(b"[]")

            with zf.open("formLogic.json", "w") as f:
                f.write(b"[]")

        response = self.app.get(
            reverse("admin:forms_import"),
            user=self.user,
            headers={"Accept-Language": "en"},
        )

        file.seek(0)

        html_form = response.form
        html_form["file"] = (
            "file.zip",
            file.read(),
        )

        response = html_form.submit("_import", headers={"Accept-Language": "en"})

        self.assertEqual(response.status_code, 302)

        form = Form.objects.get(slug="bed")

        self.assertEqual(form.name_nl, "Form 000")

    def test_importing_form_with_form_step_url_and_uuid(self):
        file = BytesIO()
        with ZipFile(file, mode="w") as zf:
            with zf.open("forms.json", "w") as f:
                f.write(
                    json.dumps(
                        [
                            {
                                "uuid": "b8315e1d-3134-476f-8786-7661d8237c51",
                                "name": "Form 000",
                                "internal_name": "Form internal",
                                "slug": "bed",
                                "product": None,
                                "authentication_backends": [],
                            }
                        ]
                    ).encode("utf-8")
                )

            with zf.open("formSteps.json", "w") as f:
                f.write(
                    json.dumps(
                        [
                            {
                                "form": "http://openforms.nl/api/v2/forms/b8315e1d-3134-476f-8786-7661d8237c51",
                                "form_definition": "http://openforms.nl/api/v2/form-definitions/f0dad93b-333b-49af-868b-a6bcb94fa1b8",
                                "index": 0,
                                "slug": "test-step-1",
                                "uuid": "3ca01601-cd20-4746-bce5-baab47636823",
                            }
                        ]
                    ).encode("utf-8")
                )

            with zf.open("formDefinitions.json", "w") as f:
                f.write(
                    json.dumps(
                        [
                            {
                                "configuration": {
                                    "components": [
                                        {
                                            "key": "radio",
                                            "type": "radio",
                                            "values": [
                                                {"label": "yes", "value": "yes"},
                                                {"label": "no", "value": "no"},
                                            ],
                                        },
                                    ]
                                },
                                "name": "Def 1 - With condition",
                                "slug": "test-definition-1",
                                "url": "http://openforms.nl/api/v2/form-definitions/f0dad93b-333b-49af-868b-a6bcb94fa1b8",
                                "uuid": "f0dad93b-333b-49af-868b-a6bcb94fa1b8",
                            }
                        ]
                    ).encode("utf-8")
                )

            with zf.open("formLogic.json", "w") as f:
                f.write(
                    json.dumps(
                        [
                            {
                                "actions": [
                                    {
                                        "action": {"type": "step-not-applicable"},
                                        "form_step": (
                                            "http://openforms.nl/api/v2/forms/b8315e1d-3134-476f-8786-7661d8237c51/steps/f65ab5ac-b9eb-4513-9b41-581e81f3dd2e"
                                        ),  # UUID different from that of the step!
                                        "form_step_uuid": "3ca01601-cd20-4746-bce5-baab47636823",
                                    }
                                ],
                                "form": "http://openforms.nl/api/v2/forms/b8315e1d-3134-476f-8786-7661d8237c51",
                                "json_logic_trigger": {"==": [{"var": "radio"}, "ja"]},
                                "uuid": "b92342be-05e0-4070-b2cc-1b88af472091",
                                "order": 0,
                            }
                        ]
                    ).encode("utf-8")
                )

        response = self.app.get(
            reverse("admin:forms_import"),
            user=self.user,
            headers={"Accept-Language": "en"},
        )

        file.seek(0)

        html_form = response.form
        html_form["file"] = (
            "file.zip",
            file.read(),
        )

        response = html_form.submit("_import")

        self.assertEqual(response.status_code, 302)

        form = Form.objects.get(slug="bed")

        self.assertEqual(form.name_nl, "Form 000")

    def test_form_admin_import_exclude_all_form_configuration(self):
        file = BytesIO()
        with ZipFile(file, mode="w") as zf:
            with zf.open("forms.json", "w") as f:
                f.write(
                    json.dumps(
                        [
                            {
                                "uuid": "b8315e1d-3134-476f-8786-7661d8237c51",
                                "name": "Form 000",
                                "internal_name": "Form internal",
                                "slug": "bed",
                                "product": None,
                                "auth_backends": [
                                    {"backend": "digid", "options": {"loa": ""}}
                                ],
                                "registration_backends": [
                                    {
                                        "key": "backend1",
                                        "name": "email",
                                        "backend": "email",
                                        "options": {
                                            "to_emails": ["test@mail.com"],
                                            "payment_emails": [],
                                            "attach_files_to_email": None,
                                        },
                                    }
                                ],
                                "payment_backend": "demo",
                                "payment_backend_options": {},
                            }
                        ]
                    ).encode("utf-8")
                )

            with zf.open("formSteps.json", "w") as f:
                f.write(
                    json.dumps(
                        [
                            {
                                "form": "http://openforms.nl/api/v2/forms/b8315e1d-3134-476f-8786-7661d8237c51",
                                "form_definition": "http://openforms.nl/api/v2/form-definitions/2b5b53d6-6fcd-4092-b0b2-19e273636935",
                                "index": 0,
                                "slug": "test-step-1",
                                "uuid": "3ca01601-cd20-4746-bce5-baab47636823",
                            }
                        ]
                    ).encode("utf-8")
                )

            with zf.open("formDefinitions.json", "w") as f:
                f.write(
                    json.dumps(
                        [
                            {
                                "url": "http://testserver/api/v2/form-definitions/2b5b53d6-6fcd-4092-b0b2-19e273636935",
                                "uuid": "2b5b53d6-6fcd-4092-b0b2-19e273636935",
                                "name": "Step",
                                "internal_name": "",
                                "slug": "step",
                                "configuration": {
                                    "components": [
                                        {
                                            "key": "textfield",
                                            "type": "textfield",
                                            "label": "Textfield",
                                            "prefill": {
                                                "plugin": "demo",
                                                "attribute": "random_number",
                                                "identifierRole": "main",
                                            },
                                        }
                                    ],
                                },
                            }
                        ]
                    ).encode("utf-8")
                )

            with zf.open("formLogic.json", "w") as f:
                f.write(b"[]")

        response = self.app.get(reverse("admin:forms_import"), user=self.user)

        file.seek(0)

        html_form = response.form
        html_form["file"] = (
            "file.zip",
            file.read(),
        )
        html_form[
            "form_configuration"
        ] = []  # Don't include any core form configuration

        response = html_form.submit("_import")

        self.assertEqual(response.status_code, 302)

        form = Form.objects.get(slug="bed")

        self.assertEqual(form.name_nl, "Form 000")
        # Form should be imported without the registration_backends, auth backends and payment backend
        self.assertFalse(form.registration_backends.exists())
        self.assertFalse(form.auth_backends.exists())
        self.assertEqual(form.payment_backend, "")
        self.assertEqual(form.payment_backend_options, {})

        form_step = form.formstep_set.get(slug="test-step-1")
        component1 = form_step.form_definition.configuration["components"][0]

        # The prefill config should be removed
        self.assertEqual(component1["key"], "textfield")
        self.assertEqual(component1["prefill"]["plugin"], "")
        self.assertEqual(component1["prefill"]["attribute"], "")
        self.assertEqual(component1["prefill"]["identifierRole"], "main")

    @enable_feature_flag("ENABLE_DEMO_PLUGINS")
    def test_form_admin_import_include_all_form_configuration(self):
        file = BytesIO()
        with ZipFile(file, mode="w") as zf:
            with zf.open("forms.json", "w") as f:
                f.write(
                    json.dumps(
                        [
                            {
                                "uuid": "b8315e1d-3134-476f-8786-7661d8237c51",
                                "name": "Form 000",
                                "internal_name": "Form internal",
                                "slug": "bed",
                                "product": None,
                                "auth_backends": [
                                    {"backend": "digid", "options": {"loa": ""}}
                                ],
                                "registration_backends": [
                                    {
                                        "key": "backend1",
                                        "name": "email",
                                        "backend": "email",
                                        "options": {
                                            "to_emails": ["test@mail.com"],
                                            "payment_emails": [],
                                            "attach_files_to_email": None,
                                        },
                                    }
                                ],
                                "payment_backend": "demo",
                                "payment_backend_options": {},
                            }
                        ]
                    ).encode("utf-8")
                )

            with zf.open("formSteps.json", "w") as f:
                f.write(
                    json.dumps(
                        [
                            {
                                "form": "http://openforms.nl/api/v2/forms/b8315e1d-3134-476f-8786-7661d8237c51",
                                "form_definition": "http://openforms.nl/api/v2/form-definitions/2b5b53d6-6fcd-4092-b0b2-19e273636935",
                                "index": 0,
                                "slug": "test-step-1",
                                "uuid": "3ca01601-cd20-4746-bce5-baab47636823",
                            }
                        ]
                    ).encode("utf-8")
                )

            with zf.open("formDefinitions.json", "w") as f:
                f.write(
                    json.dumps(
                        [
                            {
                                "url": "http://testserver/api/v2/form-definitions/2b5b53d6-6fcd-4092-b0b2-19e273636935",
                                "uuid": "2b5b53d6-6fcd-4092-b0b2-19e273636935",
                                "name": "Step",
                                "internal_name": "",
                                "slug": "step",
                                "configuration": {
                                    "components": [
                                        {
                                            "key": "textfield",
                                            "type": "textfield",
                                            "label": "Textfield",
                                            "prefill": {
                                                "plugin": "demo",
                                                "attribute": "random_number",
                                                "identifierRole": "main",
                                            },
                                        }
                                    ],
                                },
                            }
                        ]
                    ).encode("utf-8")
                )

            with zf.open("formLogic.json", "w") as f:
                f.write(b"[]")

        response = self.app.get(reverse("admin:forms_import"), user=self.user)

        file.seek(0)

        html_form = response.form
        html_form["file"] = (
            "file.zip",
            file.read(),
        )
        html_form["form_configuration"] = [
            FormConfigurationOptions.registration_backends.value,
            FormConfigurationOptions.auth_backends.value,
            FormConfigurationOptions.payment_backend.value,
            FormConfigurationOptions.prefill.value,
        ]

        response = html_form.submit("_import")

        self.assertEqual(response.status_code, 302)

        form = Form.objects.get(slug="bed")

        self.assertEqual(form.name_nl, "Form 000")
        # Form should be imported with the registration_backends, auth backends and payment backend
        self.assertEqual(form.registration_backends.count(), 1)
        self.assertEqual(form.auth_backends.count(), 1)
        self.assertEqual(form.payment_backend, "demo")
        self.assertEqual(form.payment_backend_options, {})

        form_step = form.formstep_set.get(slug="test-step-1")
        component1 = form_step.form_definition.configuration["components"][0]

        # The prefill config should be removed
        self.assertEqual(component1["key"], "textfield")
        self.assertEqual(component1["prefill"]["plugin"], "demo")
        self.assertEqual(component1["prefill"]["attribute"], "random_number")
        self.assertEqual(component1["prefill"]["identifierRole"], "main")

    @enable_feature_flag("ENABLE_DEMO_PLUGINS")
    def test_form_admin_import_exclude_all_additional_form_configuration(self):
        # Every OF instance has a couple default WMTS- and WMS-tile layer.
        # To simplify this test, we start at zero.
        MapTileLayer.objects.all().delete()
        MapWMSTileLayer.objects.all().delete()

        file = BytesIO()
        with ZipFile(file, mode="w") as zf:
            with zf.open("forms.json", "w") as f:
                f.write(
                    json.dumps(
                        [
                            {
                                "uuid": "b8315e1d-3134-476f-8786-7661d8237c51",
                                "name": "Form 000",
                                "internal_name": "Form internal",
                                "slug": "bed",
                                "auth_backends": [
                                    {
                                        "backend": "yivi_oidc",
                                        "options": {
                                            "bsn_loa": "urn:oasis:names:tc:SAML:2.0:ac:classes:MobileTwoFactorContract",
                                            "kvk_loa": "urn:etoegang:core:assurance-class:loa3",
                                            "authentication_options": ["bsn"],
                                            "additional_attributes_groups": [
                                                "235182b7-51ec-40f9-a2f3-bdad43d7a80c"
                                            ],
                                        },
                                    }
                                ],
                                "registration_backends": [
                                    {
                                        "key": "backend1",
                                        "name": "email",
                                        "backend": "email",
                                        "options": {
                                            "to_emails": ["test@mail.com"],
                                            "payment_emails": [],
                                            "attach_files_to_email": None,
                                        },
                                    }
                                ],
                                "payment_backend": "demo",
                                "payment_backend_options": {},
                                "product": "http://testserver/api/v2/products/b0044e5a-1eb1-471a-b9a8-5e860d821c88",
                            }
                        ]
                    ).encode("utf-8")
                )

            with zf.open("formSteps.json", "w") as f:
                f.write(
                    json.dumps(
                        [
                            {
                                "form": "http://openforms.nl/api/v2/forms/b8315e1d-3134-476f-8786-7661d8237c51",
                                "form_definition": "http://openforms.nl/api/v2/form-definitions/2b5b53d6-6fcd-4092-b0b2-19e273636935",
                                "index": 0,
                                "slug": "test-step-1",
                                "uuid": "3ca01601-cd20-4746-bce5-baab47636823",
                            }
                        ]
                    ).encode("utf-8")
                )

            with zf.open("formDefinitions.json", "w") as f:
                f.write(
                    json.dumps(
                        [
                            {
                                "url": "http://testserver/api/v2/form-definitions/2b5b53d6-6fcd-4092-b0b2-19e273636935",
                                "uuid": "2b5b53d6-6fcd-4092-b0b2-19e273636935",
                                "name": "Step",
                                "internal_name": "",
                                "slug": "step",
                                "configuration": {
                                    "components": [
                                        {
                                            "id": "9ddd9bfa-86a9-4efd-bffc-9e05db329e2c",
                                            "key": "map",
                                            "type": "map",
                                            "label": "Map",
                                            "overlays": [
                                                {
                                                    "url": "",
                                                    "type": "wms",
                                                    "uuid": "c277a089-10d0-4fb6-a4f3-58edd764b76a",
                                                    "label": "Actueel Hoogtebestand Nederland",
                                                    "layers": ["dtm_05m"],
                                                }
                                            ],
                                            "interactions": {
                                                "marker": True,
                                                "polygon": False,
                                                "polyline": False,
                                            },
                                            "tileLayerIdentifier": "brt-grijs",
                                            "useConfigDefaultMapSettings": False,
                                        }
                                    ],
                                },
                            }
                        ]
                    ).encode("utf-8")
                )

            with zf.open("formLogic.json", "w") as f:
                f.write(b"[]")

            with zf.open("product.json", "w") as f:
                f.write(
                    json.dumps(
                        [
                            {
                                "uuid": "b0044e5a-1eb1-471a-b9a8-5e860d821c88",
                                "name": "Product",
                                "price": "12.50",
                                "information": "",
                            }
                        ]
                    ).encode("utf-8")
                )

            with zf.open("wmsTileLayers.json", "w") as f:
                f.write(
                    json.dumps(
                        [
                            {
                                "uuid": "c277a089-10d0-4fb6-a4f3-58edd764b76a",
                                "name": "Actueel Hoogtebestand Nederland",
                                "url": "https://service.pdok.nl/rws/ahn/wms/v1_0?request=GetCapabilities&service=WMS",
                            }
                        ]
                    ).encode("utf-8")
                )

            with zf.open("wmtsTileLayers.json", "w") as f:
                f.write(
                    json.dumps(
                        [
                            {
                                "identifier": "brt-grijs",
                                "label": "BRT (grijs)",
                                "url": "https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0/grijs/EPSG:28992/{z}/{x}/{y}.png",
                            }
                        ]
                    ).encode("utf-8")
                )

            with zf.open("yiviAttributeGroups.json", "w") as f:
                f.write(
                    json.dumps(
                        [
                            {
                                "uuid": "235182b7-51ec-40f9-a2f3-bdad43d7a80c",
                                "name": "profil",
                                "description": "voor profile data",
                                "attributes": "irma-demo.gemeente.personalData.over18",
                            }
                        ]
                    ).encode("utf-8")
                )

        response = self.app.get(reverse("admin:forms_import"), user=self.user)

        file.seek(0)

        html_form = response.form
        html_form["file"] = (
            "file.zip",
            file.read(),
        )
        html_form["additional_form_configuration"] = []

        response = html_form.submit("_import")

        self.assertEqual(response.status_code, 302)

        form = Form.objects.get(slug="bed")

        # Product should be unset
        self.assertEqual(form.product, None)

        # Auth backends should be set, but without the additional attributes groups
        self.assertEqual(form.auth_backends.count(), 1)
        auth_backend = form.auth_backends.first()
        assert auth_backend is not None

        self.assertEqual(auth_backend.backend, "yivi_oidc")
        self.assertEqual(auth_backend.options["additional_attributes_groups"], [])

        # Map components don't have configured background and overlay tile layers
        fd = form.formstep_set.get().form_definition
        assert len(fd.configuration["components"]) == 1
        map_component = fd.configuration["components"][0]

        self.assertEqual(map_component["tileLayerIdentifier"], "")
        self.assertEqual(
            map_component["overlays"],
            [
                {
                    "url": "",
                    "type": "wms",
                    "uuid": "",
                    "label": "Actueel Hoogtebestand Nederland",
                    "layers": [],
                }
            ],
        )

        # No additional form configuration has been created
        self.assertFalse(Product.objects.count())
        self.assertFalse(MapTileLayer.objects.count())
        self.assertFalse(MapWMSTileLayer.objects.count())
        self.assertFalse(AttributeGroup.objects.count())

    @enable_feature_flag("ENABLE_DEMO_PLUGINS")
    def test_form_admin_import_include_all_additional_form_configuration(self):
        # Every OF instance has a couple default WMTS- and WMS-tile layer.
        # To simplify this test, we start at zero.
        MapTileLayer.objects.all().delete()
        MapWMSTileLayer.objects.all().delete()

        file = BytesIO()
        with ZipFile(file, mode="w") as zf:
            with zf.open("forms.json", "w") as f:
                f.write(
                    json.dumps(
                        [
                            {
                                "uuid": "b8315e1d-3134-476f-8786-7661d8237c51",
                                "name": "Form 000",
                                "internal_name": "Form internal",
                                "slug": "bed",
                                "auth_backends": [
                                    {
                                        "backend": "yivi_oidc",
                                        "options": {
                                            "bsn_loa": "urn:oasis:names:tc:SAML:2.0:ac:classes:MobileTwoFactorContract",
                                            "kvk_loa": "urn:etoegang:core:assurance-class:loa3",
                                            "authentication_options": ["bsn"],
                                            "additional_attributes_groups": [
                                                "235182b7-51ec-40f9-a2f3-bdad43d7a80c"
                                            ],
                                        },
                                    }
                                ],
                                "registration_backends": [
                                    {
                                        "key": "backend1",
                                        "name": "email",
                                        "backend": "email",
                                        "options": {
                                            "to_emails": ["test@mail.com"],
                                            "payment_emails": [],
                                            "attach_files_to_email": None,
                                        },
                                    }
                                ],
                                "payment_backend": "demo",
                                "payment_backend_options": {},
                                "product": "http://testserver/api/v2/products/b0044e5a-1eb1-471a-b9a8-5e860d821c88",
                            }
                        ]
                    ).encode("utf-8")
                )

            with zf.open("formSteps.json", "w") as f:
                f.write(
                    json.dumps(
                        [
                            {
                                "form": "http://openforms.nl/api/v2/forms/b8315e1d-3134-476f-8786-7661d8237c51",
                                "form_definition": "http://openforms.nl/api/v2/form-definitions/2b5b53d6-6fcd-4092-b0b2-19e273636935",
                                "index": 0,
                                "slug": "test-step-1",
                                "uuid": "3ca01601-cd20-4746-bce5-baab47636823",
                            }
                        ]
                    ).encode("utf-8")
                )

            with zf.open("formDefinitions.json", "w") as f:
                f.write(
                    json.dumps(
                        [
                            {
                                "url": "http://testserver/api/v2/form-definitions/2b5b53d6-6fcd-4092-b0b2-19e273636935",
                                "uuid": "2b5b53d6-6fcd-4092-b0b2-19e273636935",
                                "name": "Step",
                                "internal_name": "",
                                "slug": "step",
                                "configuration": {
                                    "components": [
                                        {
                                            "id": "9ddd9bfa-86a9-4efd-bffc-9e05db329e2c",
                                            "key": "map",
                                            "type": "map",
                                            "label": "Map",
                                            "overlays": [
                                                {
                                                    "url": "",
                                                    "type": "wms",
                                                    "uuid": "c277a089-10d0-4fb6-a4f3-58edd764b76a",
                                                    "label": "Actueel Hoogtebestand Nederland",
                                                    "layers": ["dtm_05m"],
                                                }
                                            ],
                                            "interactions": {
                                                "marker": True,
                                                "polygon": False,
                                                "polyline": False,
                                            },
                                            "tileLayerIdentifier": "brt-grijs",
                                            "useConfigDefaultMapSettings": False,
                                        }
                                    ],
                                },
                            }
                        ]
                    ).encode("utf-8")
                )

            with zf.open("formLogic.json", "w") as f:
                f.write(b"[]")

            with zf.open("product.json", "w") as f:
                f.write(
                    json.dumps(
                        [
                            {
                                "uuid": "b0044e5a-1eb1-471a-b9a8-5e860d821c88",
                                "name": "Product",
                                "price": "12.50",
                                "information": "",
                            }
                        ]
                    ).encode("utf-8")
                )

            with zf.open("wmsTileLayers.json", "w") as f:
                f.write(
                    json.dumps(
                        [
                            {
                                "uuid": "c277a089-10d0-4fb6-a4f3-58edd764b76a",
                                "name": "Actueel Hoogtebestand Nederland",
                                "url": "https://service.pdok.nl/rws/ahn/wms/v1_0?request=GetCapabilities&service=WMS",
                            }
                        ]
                    ).encode("utf-8")
                )

            with zf.open("wmtsTileLayers.json", "w") as f:
                f.write(
                    json.dumps(
                        [
                            {
                                "identifier": "brt-grijs",
                                "label": "BRT (grijs)",
                                "url": "https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0/grijs/EPSG:28992/{z}/{x}/{y}.png",
                            }
                        ]
                    ).encode("utf-8")
                )

            with zf.open("yiviAttributeGroups.json", "w") as f:
                f.write(
                    json.dumps(
                        [
                            {
                                "uuid": "235182b7-51ec-40f9-a2f3-bdad43d7a80c",
                                "name": "profil",
                                "description": "voor profile data",
                                "attributes": "irma-demo.gemeente.personalData.over18",
                            }
                        ]
                    ).encode("utf-8")
                )

        response = self.app.get(reverse("admin:forms_import"), user=self.user)

        file.seek(0)

        html_form = response.form
        html_form["file"] = (
            "file.zip",
            file.read(),
        )
        html_form["additional_form_configuration"] = [
            AdditionalFormConfigurationOptions.product.value,
            AdditionalFormConfigurationOptions.wms_tile_layers.value,
            AdditionalFormConfigurationOptions.wmts_tile_layers.value,
            AdditionalFormConfigurationOptions.yivi_attribute_groups.value,
        ]

        response = html_form.submit("_import")

        self.assertEqual(response.status_code, 302)

        form = Form.objects.get(slug="bed")

        # Additional form configuration have been created
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(MapTileLayer.objects.count(), 1)
        self.assertEqual(MapWMSTileLayer.objects.count(), 1)
        self.assertEqual(AttributeGroup.objects.count(), 1)

        imported_product = Product.objects.first()
        imported_wms_tile_layer = MapWMSTileLayer.objects.first()
        imported_attribute_group = AttributeGroup.objects.first()
        assert imported_product is not None
        assert imported_wms_tile_layer is not None
        assert imported_attribute_group is not None

        # Product should be set
        self.assertEqual(form.product, imported_product)

        # Auth backends should be set with the additional attributes groups
        self.assertEqual(form.auth_backends.count(), 1)
        auth_backend = form.auth_backends.first()
        assert auth_backend is not None

        self.assertEqual(auth_backend.backend, "yivi_oidc")
        self.assertEqual(
            auth_backend.options["additional_attributes_groups"],
            [str(imported_attribute_group.uuid)],
        )

        # Map component has configured background and overlay tile layers
        fd = form.formstep_set.get().form_definition
        assert len(fd.configuration["components"]) == 1
        map_component = fd.configuration["components"][0]

        self.assertEqual(map_component["tileLayerIdentifier"], "brt-grijs")
        self.assertEqual(
            map_component["overlays"],
            [
                {
                    "url": "",
                    "type": "wms",
                    "uuid": str(imported_wms_tile_layer.uuid),
                    "label": "Actueel Hoogtebestand Nederland",
                    "layers": ["dtm_05m"],
                }
            ],
        )

    def test_form_admin_import_with_theme_and_category(self):
        theme1 = ThemeFactory.create(uuid="b907b3ad-6d03-4d26-a2d9-1a50fc6c122c")
        theme2 = ThemeFactory.create(uuid="0d67a1b2-501a-4989-8226-880880cd7f0b")
        category1 = CategoryFactory.create(uuid="f4f0f698-ada5-4cc6-90cc-93583817c476")
        category2 = CategoryFactory.create(uuid="70f105b6-f03b-415e-93a4-c2a28d9ce3e6")

        file = BytesIO()
        # Configure the forms.json file with theme1 and category1
        with ZipFile(file, mode="w") as zf:
            with zf.open("forms.json", "w") as f:
                f.write(
                    json.dumps(
                        [
                            {
                                "uuid": "b8315e1d-3134-476f-8786-7661d8237c51",
                                "name": "Form 000",
                                "internal_name": "Form internal",
                                "slug": "bed",
                                "product": None,
                                "auth_backends": [],
                                "registration_backends": [],
                                "theme": str(theme1.uuid),
                                "category": str(category1.uuid),
                            }
                        ]
                    ).encode("utf-8")
                )

            with zf.open("formSteps.json", "w") as f:
                f.write(
                    json.dumps(
                        [
                            {
                                "form": "http://openforms.nl/api/v2/forms/b8315e1d-3134-476f-8786-7661d8237c51",
                                "form_definition": "http://openforms.nl/api/v2/form-definitions/2b5b53d6-6fcd-4092-b0b2-19e273636935",
                                "index": 0,
                                "slug": "test-step-1",
                                "uuid": "3ca01601-cd20-4746-bce5-baab47636823",
                            }
                        ]
                    ).encode("utf-8")
                )

            with zf.open("formDefinitions.json", "w") as f:
                f.write(
                    json.dumps(
                        [
                            {
                                "url": "http://testserver/api/v2/form-definitions/2b5b53d6-6fcd-4092-b0b2-19e273636935",
                                "uuid": "2b5b53d6-6fcd-4092-b0b2-19e273636935",
                                "name": "Step",
                                "internal_name": "",
                                "slug": "step",
                                "configuration": {
                                    "components": [
                                        {
                                            "key": "textfield",
                                            "type": "textfield",
                                            "label": "Textfield",
                                        }
                                    ],
                                },
                            }
                        ]
                    ).encode("utf-8")
                )

            with zf.open("formLogic.json", "w") as f:
                f.write(b"[]")

        response = self.app.get(reverse("admin:forms_import"), user=self.user)

        file.seek(0)

        html_form = response.form
        html_form["file"] = (
            "file.zip",
            file.read(),
        )
        # Set the ID's of the theme2 and category2 defined above
        html_form["theme"] = str(theme2.uuid)
        html_form["category"] = str(category2.uuid)

        response = html_form.submit("_import")

        self.assertEqual(response.status_code, 302)

        form = Form.objects.get(slug="bed")

        self.assertEqual(form.theme, theme2)
        self.assertEqual(form.category, category2)

    def test_form_admin_import_without_theme_and_category(self):
        theme1 = ThemeFactory.create(uuid="b907b3ad-6d03-4d26-a2d9-1a50fc6c122c")
        category1 = CategoryFactory.create(uuid="f4f0f698-ada5-4cc6-90cc-93583817c476")

        file = BytesIO()
        # Configure the forms.json file with theme1 and category1
        with ZipFile(file, mode="w") as zf:
            with zf.open("forms.json", "w") as f:
                f.write(
                    json.dumps(
                        [
                            {
                                "uuid": "b8315e1d-3134-476f-8786-7661d8237c51",
                                "name": "Form 000",
                                "internal_name": "Form internal",
                                "slug": "bed",
                                "product": None,
                                "auth_backends": [],
                                "registration_backends": [],
                                "theme": str(theme1.uuid),
                                "category": str(category1.uuid),
                            }
                        ]
                    ).encode("utf-8")
                )

            with zf.open("formSteps.json", "w") as f:
                f.write(
                    json.dumps(
                        [
                            {
                                "form": "http://openforms.nl/api/v2/forms/b8315e1d-3134-476f-8786-7661d8237c51",
                                "form_definition": "http://openforms.nl/api/v2/form-definitions/2b5b53d6-6fcd-4092-b0b2-19e273636935",
                                "index": 0,
                                "slug": "test-step-1",
                                "uuid": "3ca01601-cd20-4746-bce5-baab47636823",
                            }
                        ]
                    ).encode("utf-8")
                )

            with zf.open("formDefinitions.json", "w") as f:
                f.write(
                    json.dumps(
                        [
                            {
                                "url": "http://testserver/api/v2/form-definitions/2b5b53d6-6fcd-4092-b0b2-19e273636935",
                                "uuid": "2b5b53d6-6fcd-4092-b0b2-19e273636935",
                                "name": "Step",
                                "internal_name": "",
                                "slug": "step",
                                "configuration": {
                                    "components": [
                                        {
                                            "key": "textfield",
                                            "type": "textfield",
                                            "label": "Textfield",
                                        }
                                    ],
                                },
                            }
                        ]
                    ).encode("utf-8")
                )

            with zf.open("formLogic.json", "w") as f:
                f.write(b"[]")

        response = self.app.get(reverse("admin:forms_import"), user=self.user)

        file.seek(0)

        html_form = response.form
        html_form["file"] = (
            "file.zip",
            file.read(),
        )
        # Set the theme and category to empty strings
        html_form["theme"] = ""
        html_form["category"] = ""

        response = html_form.submit("_import")

        self.assertEqual(response.status_code, 302)

        form = Form.objects.get(slug="bed")

        self.assertIsNone(form.theme)
        self.assertIsNone(form.category)
