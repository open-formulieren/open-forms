import json
from io import BytesIO
from unittest.mock import patch
from zipfile import ZIP_DEFLATED, ZipFile

from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpRequest
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import TokenFactory, UserFactory
from openforms.appointments.models import AppointmentsConfig
from openforms.authentication.constants import AuthAttribute
from openforms.authentication.tests.factories import AttributeGroupFactory
from openforms.config.tests.factories import (
    MapTileLayerFactory,
    MapWMSTileLayerFactory,
    ThemeFactory,
)
from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory
from openforms.forms.import_export.constants import EXPORT_META_KEY
from openforms.forms.import_export.typing import (
    AdditionalFormConfigurationOptions,
    FormConfigurationOptions,
)
from openforms.payments.contrib.worldline.tests.factories import (
    WorldlineMerchantFactory,
)
from openforms.prefill.constants import IdentifierRoles
from openforms.products.tests.factories import ProductFactory
from openforms.variables.constants import FormVariableSources

from ...emails.tests.factories import ConfirmationEmailTemplateFactory
from ..constants import FormTypeChoices
from ..models import Form, FormDefinition, FormStep
from .factories import (
    CategoryFactory,
    FormDefinitionFactory,
    FormFactory,
    FormLogicFactory,
    FormRegistrationBackendFactory,
    FormStepFactory,
    FormVariableFactory,
)


class ImportExportAPITests(APITestCase):
    def setUp(self):
        self.user = UserFactory.create()
        self.token = TokenFactory(user=self.user)

    def test_form_export(self):
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()

        form, _ = FormFactory.create_batch(2)
        form_definition, _ = FormDefinitionFactory.create_batch(2)
        # This creates one form variable for the component in the default definition
        FormStepFactory.create(form=form, form_definition=form_definition)
        FormStepFactory.create()
        FormVariableFactory.create(
            form=form, source=FormVariableSources.user_defined, key="test-user-defined"
        )

        url = reverse("api:form-export", args=(form.uuid,))
        response = self.client.post(
            url, format="json", HTTP_AUTHORIZATION=f"Token {self.token.key}"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

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
        self.assertEqual(forms[0]["name"], form.name)
        self.assertEqual(forms[0]["slug"], form.slug)
        self.assertEqual(len(forms[0]["steps"]), form.formstep_set.count())
        self.assertIsNone(forms[0]["product"])

        form_definitions = json.loads(zf.read("formDefinitions.json"))
        self.assertEqual(len(form_definitions), 1)
        self.assertEqual(form_definitions[0]["uuid"], str(form_definition.uuid))
        self.assertEqual(form_definitions[0]["name"], form_definition.name)
        self.assertEqual(form_definitions[0]["slug"], form_definition.slug)
        self.assertEqual(
            form_definitions[0]["configuration"],
            form_definition.configuration,
        )

        form_steps = json.loads(zf.read("formSteps.json"))
        self.assertEqual(len(form_steps), 1)
        self.assertEqual(form_steps[0]["configuration"], form_definition.configuration)

        form_variables = json.loads(zf.read("formVariables.json"))
        # Only user defined form variables are included in the export
        self.assertEqual(len(form_variables), 1)
        self.assertEqual(FormVariableSources.user_defined, form_variables[0]["source"])

    def test_form_export_token_auth_required(self):
        form, _ = FormFactory.create_batch(2)

        url = reverse("api:form-export", args=(form.uuid,))
        response = self.client.post(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_form_export_session_auth_not_allowed(self):
        self.user.is_staff = True
        self.user.save()

        self.client.login(
            request=HttpRequest(), username=self.user.username, password="secret"
        )

        form, _ = FormFactory.create_batch(2)

        url = reverse("api:form-export", args=(form.uuid,))
        response = self.client.post(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_form_export_staff_required(self):
        self.user.is_staff = False
        self.user.save()

        form, _ = FormFactory.create_batch(2)
        form_definition, _ = FormDefinitionFactory.create_batch(2)
        form_step, _ = FormStepFactory.create_batch(2)
        form_step.form = form
        form_step.form_definition = form_definition
        form_step.save()

        url = reverse("api:form-export", args=(form.uuid,))
        response = self.client.post(
            url, format="json", HTTP_AUTHORIZATION=f"Token {self.token.key}"
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_form_export_remove_all_sensitive_data(self):
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()

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

        url = reverse("api:form-export", args=(form.uuid,))
        response = self.client.post(
            url,
            format="json",
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
            data={
                "remove_sensitive_content": True,
                "form_configuration": [
                    FormConfigurationOptions.registration_backends,
                ],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

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
        self.assertEqual(forms[0]["internal_remarks"], "")

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

    def test_form_export_keep_all_sensitive_data(self):
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()

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

        url = reverse("api:form-export", args=(form.uuid,))
        response = self.client.post(
            url,
            format="json",
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
            data={
                "remove_sensitive_content": False,
                "form_configuration": [
                    FormConfigurationOptions.registration_backends,
                ],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

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

    def test_form_export_include_all_form_configuration(self):
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()

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

        url = reverse("api:form-export", args=(form.uuid,))
        response = self.client.post(
            url,
            format="json",
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
            data={
                # Keep sensitive data to keep the email registration config complete
                "remove_sensitive_content": False,
                "form_configuration": [
                    FormConfigurationOptions.registration_backends,
                    FormConfigurationOptions.prefill,
                    FormConfigurationOptions.payment_backend,
                ],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

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

    def test_form_export_exclude_all_form_configuration(self):
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()

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

        url = reverse("api:form-export", args=(form.uuid,))
        response = self.client.post(
            url,
            format="json",
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
            data={
                "form_configuration": [],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

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
        self.assertEqual(form_variables[0]["prefill_identifier_role"], "main")
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
        self.assertEqual(component_definition["prefill"]["identifier_role"], "main")

    def test_form_export_including_all_additional_form_configuration(self):
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()

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

        url = reverse("api:form-export", args=(form.uuid,))
        response = self.client.post(
            url,
            format="json",
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
            data={
                "additional_form_configuration": [
                    AdditionalFormConfigurationOptions.product,
                    AdditionalFormConfigurationOptions.theme,
                    AdditionalFormConfigurationOptions.category,
                    AdditionalFormConfigurationOptions.wms_tile_layers,
                    AdditionalFormConfigurationOptions.wmts_tile_layers,
                    AdditionalFormConfigurationOptions.yivi_attribute_groups,
                ]
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

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
                "theme.json",
                "category.json",
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

        exported_theme = json.loads(zf.read("theme.json"))
        self.assertEqual(len(exported_theme), 1)
        self.assertEqual(
            exported_theme,
            [
                {
                    "uuid": str(theme.uuid),
                    "name": theme.name,
                    "organization_name": theme.organization_name,
                    "main_website": theme.main_website,
                    "favicon": str(theme.favicon),
                    "email_logo": str(theme.email_logo),
                    "classname": theme.classname,
                    "stylesheet": theme.stylesheet,
                    "stylesheet_file": str(theme.stylesheet_file),
                    # Simple stringify results in the wrong quotes being used, so we
                    # have to json.dump the design_token_values
                    "design_token_values": json.dumps(theme.design_token_values),
                }
            ],
        )

        exported_category = json.loads(zf.read("category.json"))
        self.assertEqual(len(exported_category), 1)
        self.assertEqual(
            exported_category,
            [
                {
                    "uuid": str(category.uuid),
                    "name": category.name,
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

    def test_form_export_excluding_all_additional_form_configuration(self):
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()

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

        url = reverse("api:form-export", args=(form.uuid,))
        response = self.client.post(
            url,
            format="json",
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
            data={"additional_form_configuration": []},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

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

        # The references on the form are also removed
        self.assertEqual(exported_forms[0]["product"], None)
        self.assertEqual(exported_forms[0]["theme"], None)
        self.assertEqual(exported_forms[0]["category"], None)

    def test_form_import(self):
        # export, delete, import roundtrip
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()

        form1 = FormFactory.create(send_confirmation_email=True)
        original_registration_backends = form1.registration_backends.order_by("id")
        form2 = FormFactory.create()
        FormRegistrationBackendFactory.create_batch(2, form=form1, backend="demo")
        form_definition1, form_definition2 = FormDefinitionFactory.create_batch(2)
        form_step1 = FormStepFactory.create(
            form=form1, form_definition=form_definition1
        )
        FormStepFactory.create(form=form2, form_definition=form_definition2)

        email_tpl = ConfirmationEmailTemplateFactory.create(form=form1, with_tags=True)

        url = reverse("api:form-export", args=(form1.uuid,))
        response = self.client.post(
            url, format="json", HTTP_AUTHORIZATION=f"Token {self.token.key}"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form1.delete()
        form_definition1.delete()
        form_step1.delete()

        f = SimpleUploadedFile(
            "file.zip", response.content, content_type="application/zip"
        )
        url = reverse("api:forms-import")
        response = self.client.post(
            url,
            {"file": f},
            format="multipart",
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
            HTTP_CONTENT_DISPOSITION="attachment;filename=file.zip",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Form.objects.count(), 2)
        self.assertEqual(FormDefinition.objects.count(), 2)
        self.assertEqual(FormStep.objects.count(), 2)

        form_uuid = response.json()["uuid"]
        location = response.headers["Location"]
        imported_form = Form.objects.last()
        imported_form_step = imported_form.formstep_set.first()
        imported_form_definition = imported_form_step.form_definition

        self.assertEqual(form_uuid, str(imported_form.uuid))
        form_detail_full_url = "http://testserver" + reverse(
            "api:form-detail", kwargs={"uuid_or_slug": form_uuid}
        )
        self.assertEqual(form_detail_full_url, location)
        self.assertNotEqual(imported_form.pk, form1.pk)
        self.assertNotEqual(imported_form.uuid, str(form1.uuid))
        self.assertEqual(imported_form.active, False)
        for imported, original in zip(
            imported_form.registration_backends.order_by("id"),
            original_registration_backends,
            strict=False,
        ):
            self.assertEqual(imported.key, original.key)
            self.assertEqual(imported.name, original.name)
            self.assertEqual(imported.backend, original.backend)
            self.assertEqual(imported.options, original.options)
        self.assertEqual(imported_form.name, form1.name)
        self.assertIsNone(imported_form.product)
        self.assertEqual(imported_form.slug, form1.slug)

        self.assertEqual(
            imported_form.confirmation_email_template.content, email_tpl.content
        )
        self.assertEqual(
            imported_form.confirmation_email_template.subject, email_tpl.subject
        )

        self.assertNotEqual(imported_form_definition.pk, form_definition1.pk)
        self.assertNotEqual(imported_form_definition.uuid, str(form_definition1.uuid))
        self.assertEqual(
            imported_form_definition.configuration, form_definition1.configuration
        )
        self.assertEqual(
            imported_form_definition.login_required, form_definition1.login_required
        )
        self.assertEqual(imported_form_definition.name, form_definition1.name)
        self.assertEqual(imported_form_definition.slug, form_definition1.slug)

        self.assertNotEqual(imported_form_step.pk, form_step1.pk)
        self.assertNotEqual(imported_form_step.uuid, str(form_step1.uuid))
        self.assertEqual(imported_form_step.form.pk, imported_form.pk)
        self.assertEqual(
            imported_form_step.form_definition.pk, imported_form_definition.pk
        )
        self.assertEqual(imported_form_step.order, form_step1.order)

    def test_old_appointment_form_import_v4(self):
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()

        config = AppointmentsConfig.get_solo()
        config.plugin = "demo"
        config.save()

        form = FormFactory.create()

        url = reverse("api:form-export", args=(form.uuid,))
        response = self.client.post(
            url, format="json", HTTP_AUTHORIZATION=f"Token {self.token.key}"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # need to inject the old `is_appointment` property as now the serializer rejects
        # it (has been removed in favor of the form type field)
        zf = ZipFile(BytesIO(response.content))
        forms_data = json.loads(zf.read("forms.json"))
        forms_data[0]["appointment_options"] = {
            "is_appointment": True,
            "supports_multiple_products": None,
        }
        output_zip = BytesIO()

        with ZipFile(output_zip, "w", ZIP_DEFLATED) as zfw:
            zfw.writestr("forms.json", json.dumps(forms_data))

        modified_content = output_zip.getvalue()

        form.delete()

        f = SimpleUploadedFile(
            "file.zip", modified_content, content_type="application/zip"
        )
        url = reverse("api:forms-import")
        response = self.client.post(
            url,
            {"file": f},
            format="multipart",
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
            HTTP_CONTENT_DISPOSITION="attachment;filename=file.zip",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Form.objects.count(), 1)
        self.assertEqual(FormDefinition.objects.count(), 0)
        self.assertEqual(FormStep.objects.count(), 0)

        form_uuid = response.json()["uuid"]
        location = response.headers["Location"]
        imported_form = Form.objects.last()

        self.assertEqual(form_uuid, str(imported_form.uuid))
        form_detail_full_url = "http://testserver" + reverse(
            "api:form-detail", kwargs={"uuid_or_slug": form_uuid}
        )
        self.assertEqual(form_detail_full_url, location)
        self.assertNotEqual(imported_form.pk, form.pk)
        self.assertNotEqual(imported_form.uuid, str(form.uuid))
        self.assertEqual(imported_form.active, False)
        self.assertEqual(imported_form.type, FormTypeChoices.appointment)

    @patch(
        "openforms.api.exception_handling.uuid.uuid4",
        return_value="95a55a81-d316-44e8-b090-0519dd21be5f",
    )
    def test_form_import_form_slug_already_exists(self, _mock):
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()

        form1 = FormFactory.create(slug="my-slug")
        form_definition1 = FormDefinitionFactory.create(is_reusable=True)
        FormStepFactory.create(form=form1, form_definition=form_definition1)

        url = reverse("api:form-export", args=(form1.uuid,))
        response = self.client.post(
            url, format="json", HTTP_AUTHORIZATION=f"Token {self.token.key}"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        f = SimpleUploadedFile(
            "file.zip", response.content, content_type="application/zip"
        )
        url = reverse("api:forms-import")
        response = self.client.post(
            url,
            {"file": f},
            format="multipart",
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
            HTTP_CONTENT_DISPOSITION="attachment;filename=file.zip",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        form_uuid = response.json()["uuid"]
        location = response.headers["Location"]
        imported_form = Form.objects.last()
        imported_form_step = imported_form.formstep_set.first()
        imported_form_definition = imported_form_step.form_definition

        # Check that the return response's uuid is the same as the last form in the db
        self.assertEqual(form_uuid, str(imported_form.uuid))
        # Check that the return Location header is the same as the full 'form-detail' api url.
        form_detail_full_url = "http://testserver" + reverse(
            "api:form-detail", kwargs={"uuid_or_slug": form_uuid}
        )
        self.assertEqual(form_detail_full_url, location)
        # check we imported a new form
        self.assertNotEqual(form1.pk, imported_form.pk)
        # check we added random hex chars
        self.assertRegex(imported_form.slug, r"^my-slug-[0-9a-f]{6}$")
        # check uuid mapping still works
        self.assertEqual(imported_form_definition.uuid, form_definition1.uuid)

    def test_form_import_token_auth_required(self):
        url = reverse("api:forms-import")
        response = self.client.post(
            url,
            {"file": b""},
            format="multipart",
            HTTP_CONTENT_DISPOSITION="attachment;filename=file.zip",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_form_import_session_auth_not_allowed(self):
        self.user.is_staff = True
        self.user.save()

        self.client.login(
            request=HttpRequest(), username=self.user.username, password="secret"
        )

        url = reverse("api:forms-import")
        response = self.client.post(
            url,
            {"file": b""},
            format="multipart",
            HTTP_CONTENT_DISPOSITION="attachment;filename=file.zip",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_form_import_staff_required(self):
        self.user.is_staff = False
        self.user.save()

        url = reverse("api:forms-import")
        response = self.client.post(
            url,
            {"file", b""},
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
            HTTP_CONTENT_DISPOSITION="attachment;filename=file.zip",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
