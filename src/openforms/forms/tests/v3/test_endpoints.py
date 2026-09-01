import base64
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from datetime import timedelta
from uuid import UUID, uuid4

from django.db import connections
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.text import get_text_list
from django.utils.translation import gettext as _

from digid_eherkenning.choices import DigiDAssuranceLevels
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient, APITestCase, APITransactionTestCase
from zgw_consumers.test.factories import ServiceFactory

from openforms.accounts.models import User
from openforms.accounts.tests.factories import UserFactory
from openforms.appointments.models import AppointmentsConfig
from openforms.config.tests.factories import ThemeFactory
from openforms.contrib.customer_interactions.tests.factories import (
    CustomerInteractionsAPIGroupConfigFactory,
)
from openforms.data_removal.constants import RemovalMethods
from openforms.payments.contrib.worldline.tests.factories import (
    WorldlineMerchantFactory,
)
from openforms.prefill.contrib.customer_interactions.constants import (
    PLUGIN_IDENTIFIER as COMMUNICATION_PREFERENCES_PLUGIN_IDENTIFIER,
)
from openforms.products.tests.factories import ProductFactory
from openforms.typing import JSONObject
from openforms.utils.tests.feature_flags import enable_feature_flag
from openforms.variables.constants import (
    FormVariableDataTypes,
    FormVariableSources,
    ServiceFetchMethods,
)
from openforms.variables.tests.factories import ServiceFetchConfigurationFactory

from ...constants import (
    FormTypeChoices,
    StatementCheckboxChoices,
    SubmissionAllowedChoices,
)
from ...models import (
    Form,
    FormAuthenticationBackend,
    FormDefinition,
    FormLogic,
    FormRegistrationBackend,
)
from ...tests.factories import (
    CategoryFactory,
    FormDefinitionFactory,
    FormFactory,
    FormLogicFactory,
    FormStepFactory,
)


class FormEndpointTests(APITestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin_user = UserFactory.create(
            is_staff=True, user_permissions=("forms.change_form",)
        )

    def setUp(self) -> None:
        super().setUp()

        self.client.force_authenticate(user=self.admin_user)

    def test_create_minimal_form(self):
        form_definition_uuid = uuid4()
        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": "559812e7-9bff-4142-ab41-0cc8cf4e5e32"},
        )
        data = {
            "name": "Create form",
            "slug": "create-form",
            "steps": [
                {
                    "slug": "step-1",
                    "formDefinition": {
                        "uuid": form_definition_uuid,
                        "configuration": {
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "component1",
                                    "label": "component1",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                            ],
                        },
                        "translations": {
                            "en": {
                                "name": "Form configuration 1",
                                "internalName": "Form configuration 1",
                            },
                            "nl": {
                                "name": "Form configuratie 1",
                                "internalName": "Form configuratie 1",
                            },
                        },
                    },
                },
            ],
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Form.objects.count(), 1)
        form = Form.objects.get()

        self.assertEqual(form.name, "Create form")
        self.assertEqual(form.slug, "create-form")

        with self.subTest("formio config is kept as-is"):
            fd = FormDefinition.objects.get()
            self.assertEqual(
                fd.configuration,
                {
                    "components": [
                        {
                            "type": "textfield",
                            "key": "component1",
                            "label": "component1",
                            "hidden": False,
                            "clearOnHide": True,
                        },
                    ],
                },
            )

    def test_create_detailed_form(self):
        product = ProductFactory.create()
        category = CategoryFactory.create()
        theme = ThemeFactory.create()
        form_definition_uuid = str(uuid4())
        merchant = WorldlineMerchantFactory.create(pspid="wordline-merchant")
        activate_on = timezone.now() + timedelta(days=1)
        deactivate_on = timezone.now() + timedelta(days=2)
        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": "559812e7-9bff-4142-ab41-0cc8cf4e5e32"},
        )
        data = {
            "name": "Create form",
            "internalName": "Create form internal",
            "internalRemarks": "This form is used for xyz",
            "translationEnabled": True,
            "authBackends": [
                {
                    "backend": "digid",
                    "options": {"loa": DigiDAssuranceLevels.substantial},
                }
            ],
            "autoLoginAuthenticationBackend": "digid",
            "registrationBackends": [
                {
                    "name": "Email registration",
                    "key": "email-fu",
                    "backend": "email",
                    "options": {
                        "to_emails": ["foo@example.com"],
                    },
                }
            ],
            "payment": {
                "backend": "worldline",
                "options": {
                    "merchant": merchant.pspid,
                    "variant": "Form v3 payments",
                    "descriptorTemplate": "{{ foo }}",
                },
            },
            "literals": {
                "beginText": {"value": "Different Begin Text"},
                "previousText": {"value": "Different Previous Text"},
                "changeText": {"value": "Different Change Text"},
                "confirmText": {"value": "Different Confirm Text"},
            },
            "product": product.uuid,
            "slug": "create-form",
            "type": FormTypeChoices.regular,
            "category": category.uuid,
            "theme": theme.uuid,
            "showProgressIndicator": True,
            "showSummaryProgress": True,
            "steps": [
                {
                    "slug": "step-1",
                    "formDefinition": {
                        "uuid": form_definition_uuid,
                        "isReusable": True,
                        "loginRequired": True,
                        "configuration": {
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "component1",
                                    "label": "component1",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                                {
                                    "type": "textfield",
                                    "key": "component2",
                                    "label": "component2",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                            ],
                        },
                        "translations": {
                            "en": {
                                "name": "Form configuration 1",
                                "internalName": "Form configuration 1",
                            },
                            "nl": {
                                "name": "Form configuratie 1",
                                "internalName": "Form configuratie 1",
                            },
                        },
                    },
                }
            ],
            "variables": [
                {
                    "name": "extra_var",
                    "key": "extra_var",
                    "source": FormVariableSources.user_defined,
                    "data_type": FormVariableDataTypes.string,
                },
                {
                    "name": "extra_var_2",
                    "key": "extra_var_2",
                    "source": FormVariableSources.user_defined,
                    "data_type": FormVariableDataTypes.string,
                },
            ],
            "maintenanceMode": True,
            "active": True,
            "activateOn": activate_on.isoformat(),
            "deactivateOn": deactivate_on.isoformat(),
            "isDeleted": False,
            "submissionConfirmationTemplate": "Have a cookie",
            "introductionPageContent": "You can ask for cookies here",
            "explanationTemplate": "Get ready to ask for some cookies",
            "submissionAllowed": SubmissionAllowedChoices.yes,
            "submissionLimit": 10,
            "submissionCounter": 0,
            "suspensionAllowed": True,
            "askPrivacyConsent": StatementCheckboxChoices.required,
            "askStatementOfTruth": StatementCheckboxChoices.required,
            "submissionsRemovalOptions": {
                "successfulSubmissionsRemovalLimit": 10,
                "successfulSubmissionsRemovalMethod": RemovalMethods.delete_permanently,
                "incompleteSubmissionsRemovalLimit": 5,
                "incompleteSubmissionsRemovalMethod": RemovalMethods.delete_permanently,
                "erroredSubmissionsRemovalLimit": 20,
                "erroredSubmissionsRemovalMethod": RemovalMethods.delete_permanently,
                "allSubmissionsRemovalLimit": 30,
            },
            "confirmationEmailTemplate": {
                "translations": {
                    "en": {
                        "subject": "Submission received",
                        "content": "{% confirmation_summary %} {% appointment_information %} {% payment_information %}",
                        "cosign_subject": "Cosign submission received",
                        "cosign_content": "{% confirmation_summary %} {% appointment_information %} {% payment_information %} {% cosign_information %}",
                    },
                    "nl": {
                        "subject": "Inzending ontvangen",
                        "content": "{% confirmation_summary %} {% appointment_information %} {% payment_information %}",
                        "cosign_subject": "Cosign inzending ontvangen",
                        "cosign_content": "{% confirmation_summary %} {% appointment_information %} {% payment_information %} {% cosign_information %}",
                    },
                }
            },
            "sendConfirmationEmail": True,
            "displayMainWebsiteLink": True,
            "includeConfirmationPageContentInPdf": True,
            "translations": {
                "en": {
                    "name": "Create form",
                    "beginText": "start",
                    "previousText": "previous",
                    "changeText": "change",
                    "confirmText": "confirm",
                    "submissionConfirmationTemplate": "Have a cookie",
                    "introductionPageContent": "You can ask for cookies here",
                    "explanationTemplate": "Get ready to ask for some cookies",
                    "helpDialogContent": "help information",
                },
                "nl": {
                    "name": "Create formulier",
                    "beginText": "start",
                    "previousText": "vorige",
                    "changeText": "wijzigen",
                    "confirmText": "bevestigen",
                    "submissionConfirmationTemplate": "Neem een koekje",
                    "introductionPageContent": "Je kan hier voor koekjes vragen",
                    "explanationTemplate": "Wees klaar om voor koekjes te vragen",
                    "helpDialogContent": "hulpinformatie",
                },
            },
            "helpCalloutPage": {"display": "before_start_page"},
            "helpDialog": {
                "content": "Hello there",
                "image": base64.b64encode(
                    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02"
                    b"\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01"
                    b"\xf6\x178U\x00\x00\x00\x00IEND\xaeB`\x82"
                ).decode("ascii"),
            },
            "logic_rules": [
                {
                    "order": 0,
                    "jsonLogicTrigger": {"==": [{"var": "component1"}, "foo"]},
                    "actions": [
                        {
                            "component": "component2",
                            "action": {
                                "type": "property",
                                "property": {"type": "bool", "value": "hidden"},
                                "value": "",
                                "state": True,
                            },
                        }
                    ],
                },
            ],
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Form.objects.count(), 1)
        form = Form.objects.get()
        self.addCleanup(
            lambda: form.help_dialog_image.storage.delete(form.help_dialog_image.name)
        )

        self.assertEqual(form.name_en, "Create form")
        self.assertEqual(form.name_nl, "Create formulier")
        self.assertEqual(form.internal_name, "Create form internal")
        self.assertEqual(form.internal_remarks, "This form is used for xyz")
        self.assertTrue(form.login_required)
        self.assertTrue(form.translation_enabled)

        self.assertEqual(form.type, FormTypeChoices.regular)
        self.assertEqual(form.slug, "create-form")
        self.assertEqual(form.help_callout_page_display, "before_start_page")

        # help dialog
        self.assertEqual(form.help_dialog_content_en, "help information")
        self.assertEqual(form.help_dialog_content_nl, "hulpinformatie")
        self.assertNotEqual(form.help_dialog_image, "")
        name = form.help_dialog_image.name
        self.assertTrue(name.endswith(".png"))
        self.assertTrue(form.help_dialog_image.storage.exists(name))

        # product
        self.assertEqual(form.product, product)

        # category
        category = form.category
        self.assertEqual(form.category, category)

        # theme
        theme = form.theme
        self.assertEqual(form.theme, theme)

        # form step
        form_step = form.formstep_set.get()
        self.assertEqual(form_step.order, 0)
        self.assertEqual(form_step.slug, "step-1")

        # step form definition
        form_definition = form_step.form_definition
        self.assertEqual(str(form_definition.uuid), form_definition_uuid)
        self.assertTrue(form_definition.is_reusable)
        self.assertTrue(form_definition.login_required)
        self.assertEqual(
            form_definition.configuration,
            {
                "components": [
                    {
                        "type": "textfield",
                        "key": "component1",
                        "label": "component1",
                        "hidden": False,
                        "clearOnHide": True,
                    },
                    {
                        "type": "textfield",
                        "key": "component2",
                        "label": "component2",
                        "hidden": False,
                        "clearOnHide": True,
                    },
                ],
            },
        )
        self.assertEqual(form_definition.name_nl, "Form configuratie 1")
        self.assertEqual(form_definition.name_en, "Form configuration 1")

        # variables
        variables = form.formvariable_set.order_by("source", "key")
        self.assertEqual(variables.count(), 4)

        ## Component variables
        self.assertEqual(variables[0].name, "component1")
        self.assertEqual(variables[0].key, "component1")
        self.assertEqual(variables[0].form_definition, form_definition)
        self.assertEqual(variables[0].data_type, FormVariableDataTypes.string)
        self.assertEqual(variables[0].source, FormVariableSources.component)
        self.assertEqual(variables[1].name, "component2")
        self.assertEqual(variables[1].key, "component2")
        self.assertEqual(variables[1].form_definition, form_definition)
        self.assertEqual(variables[1].data_type, FormVariableDataTypes.string)
        self.assertEqual(variables[1].source, FormVariableSources.component)

        ## User defined variables
        self.assertEqual(variables[2].name, "extra_var")
        self.assertEqual(variables[2].key, "extra_var")
        self.assertIsNone(variables[2].form_definition)
        self.assertEqual(variables[2].data_type, FormVariableDataTypes.string)
        self.assertEqual(variables[2].source, FormVariableSources.user_defined)
        self.assertEqual(variables[3].name, "extra_var_2")
        self.assertEqual(variables[3].key, "extra_var_2")
        self.assertIsNone(variables[3].form_definition)
        self.assertEqual(variables[3].data_type, FormVariableDataTypes.string)
        self.assertEqual(variables[3].source, FormVariableSources.user_defined)

        # authentication options
        self.assertEqual(form.auto_login_authentication_backend, "digid")
        authentication_backend = FormAuthenticationBackend.objects.get()
        self.assertEqual(authentication_backend.backend, "digid")
        self.assertEqual(
            authentication_backend.options, {"loa": DigiDAssuranceLevels.substantial}
        )

        # registration backends
        registration_backend = FormRegistrationBackend.objects.get()
        self.assertEqual(form.registration_backends.get(), registration_backend)
        self.assertEqual(registration_backend.name, "Email registration")
        self.assertEqual(registration_backend.key, "email-fu")
        self.assertEqual(registration_backend.backend, "email")
        self.assertEqual(
            registration_backend.options,
            {
                "to_emails": ["foo@example.com"],
                "attach_files_to_email": None,
            },
        )

        # payment options
        self.assertEqual(form.payment_required, True)
        self.assertEqual(form.payment_backend, "worldline")
        self.assertEqual(
            form.payment_backend_options,
            {
                "merchant": merchant.pspid,
                "variant": "Form v3 payments",
                "descriptor_template": "{{ foo }}",
            },
        )

        self.assertTrue(form.show_progress_indicator)
        self.assertTrue(form.show_summary_progress)
        self.assertTrue(form.maintenance_mode)
        self.assertTrue(form.active)
        self.assertEqual(form.activate_on, activate_on)
        self.assertEqual(form.deactivate_on, deactivate_on)
        self.assertFalse(form._is_deleted)
        self.assertEqual(form.submission_confirmation_template, "Neem een koekje")
        self.assertEqual(
            form.introduction_page_content, "Je kan hier voor koekjes vragen"
        )
        self.assertEqual(
            form.explanation_template, "Wees klaar om voor koekjes te vragen"
        )
        self.assertEqual(form.submission_allowed, SubmissionAllowedChoices.yes)
        self.assertEqual(form.submission_limit, 10)
        self.assertEqual(form.submission_counter, 0)
        self.assertTrue(form.suspension_allowed)
        self.assertEqual(form.ask_privacy_consent, StatementCheckboxChoices.required)
        self.assertEqual(form.ask_statement_of_truth, StatementCheckboxChoices.required)
        self.assertEqual(form.successful_submissions_removal_limit, 10)
        self.assertEqual(
            form.successful_submissions_removal_method,
            RemovalMethods.delete_permanently,
        )
        self.assertEqual(form.incomplete_submissions_removal_limit, 5)
        self.assertEqual(
            form.incomplete_submissions_removal_method,
            RemovalMethods.delete_permanently,
        )
        self.assertEqual(form.errored_submissions_removal_limit, 20)
        self.assertEqual(
            form.errored_submissions_removal_method, RemovalMethods.delete_permanently
        )
        self.assertEqual(form.all_submissions_removal_limit, 30)
        self.assertTrue(form.send_confirmation_email)
        self.assertTrue(form.display_main_website_link)
        self.assertTrue(form.include_confirmation_page_content_in_pdf)

        # confirmation email
        confirmation_email_template = form.confirmation_email_template
        assert confirmation_email_template, "No confirmation email coupled to form"
        self.assertEqual(confirmation_email_template.subject_en, "Submission received")
        self.assertEqual(
            confirmation_email_template.content_en,
            "{% confirmation_summary %} {% appointment_information %} {% payment_information %}",
        )
        self.assertEqual(
            confirmation_email_template.cosign_subject_en, "Cosign submission received"
        )
        self.assertEqual(
            confirmation_email_template.cosign_content_en,
            "{% confirmation_summary %} {% appointment_information %} {% payment_information %} {% cosign_information %}",
        )
        self.assertEqual(confirmation_email_template.subject_nl, "Inzending ontvangen")
        self.assertEqual(
            confirmation_email_template.content_nl,
            "{% confirmation_summary %} {% appointment_information %} {% payment_information %}",
        )
        self.assertEqual(
            confirmation_email_template.cosign_subject_nl, "Cosign inzending ontvangen"
        )
        self.assertEqual(
            confirmation_email_template.cosign_content_nl,
            "{% confirmation_summary %} {% appointment_information %} {% payment_information %} {% cosign_information %}",
        )

        # translations
        self.assertEqual(form.begin_text_en, "start")
        self.assertEqual(form.previous_text_en, "previous")
        self.assertEqual(form.change_text_en, "change")
        self.assertEqual(form.confirm_text_en, "confirm")
        self.assertEqual(form.submission_confirmation_template_en, "Have a cookie")
        self.assertEqual(
            form.introduction_page_content_en, "You can ask for cookies here"
        )
        self.assertEqual(
            form.explanation_template_en, "Get ready to ask for some cookies"
        )
        self.assertEqual(form.help_dialog_content_en, "help information")

        self.assertEqual(form.begin_text_nl, "start")
        self.assertEqual(form.previous_text_nl, "vorige")
        self.assertEqual(form.change_text_nl, "wijzigen")
        self.assertEqual(form.confirm_text_nl, "bevestigen")
        self.assertEqual(form.submission_confirmation_template_nl, "Neem een koekje")
        self.assertEqual(
            form.introduction_page_content_nl, "Je kan hier voor koekjes vragen"
        )
        self.assertEqual(
            form.explanation_template_nl, "Wees klaar om voor koekjes te vragen"
        )
        self.assertEqual(form.help_dialog_content_nl, "hulpinformatie")

        # logic rules
        self.assertEqual(form.formlogic_set.count(), 1)

    def test_create_reuse_existing_definition(self):
        form_definition = FormDefinitionFactory.create(
            name="Form definition",
            slug="form-definition",
            is_reusable=True,
            configuration={"components": [{"key": "textfield", "type": "textfield"}]},
        )

        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": "559812e7-9bff-4142-ab41-0cc8cf4e5e32"},
        )
        data = {
            "name": "Create form",
            "slug": "create-form",
            "steps": [
                {
                    "slug": "step-1",
                    "formDefinition": {
                        "uuid": str(form_definition.uuid),
                        "isReusable": True,
                        "loginRequired": True,
                        "configuration": {
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "component1",
                                    "label": "component1",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                                {
                                    "type": "textfield",
                                    "key": "component2",
                                    "label": "component2",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                            ],
                        },
                        "translations": {
                            "en": {
                                "name": "Form configuration 1",
                                "internalName": "Form configuration 1",
                            },
                            "nl": {
                                "name": "Form configuratie 1",
                                "internalName": "Form configuratie 1",
                            },
                        },
                    },
                }
            ],
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Form.objects.count(), 1)
        form = Form.objects.get()

        # form step
        form_step = form.formstep_set.get()
        self.assertEqual(form_step.order, 0)
        self.assertEqual(form_step.slug, "step-1")

        # step form definition
        self.assertEqual(form_step.form_definition, form_definition)
        form_definition.refresh_from_db()
        self.assertEqual(str(form_definition.uuid), str(form_definition.uuid))
        self.assertTrue(form_definition.is_reusable)
        self.assertTrue(form_definition.login_required)
        self.assertEqual(
            form_definition.configuration,
            {
                "components": [
                    {
                        "type": "textfield",
                        "key": "component1",
                        "label": "component1",
                        "hidden": False,
                        "clearOnHide": True,
                    },
                    {
                        "type": "textfield",
                        "key": "component2",
                        "label": "component2",
                        "hidden": False,
                        "clearOnHide": True,
                    },
                ],
            },
        )
        self.assertEqual(FormDefinition.objects.count(), 1)

    def test_update_clears_existing_registration_backends(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            registration_backend="zgw-create-zaak",
        )
        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": form.uuid},
        )
        data = {
            "name": "Update form",
            "slug": "update-form",
            "steps": [
                {
                    "slug": "step-1",
                    "formDefinition": {
                        "uuid": str(uuid4()),
                        "configuration": {
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "component1",
                                    "label": "component1",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                            ],
                        },
                        "translations": {
                            "en": {
                                "name": "Form configuration 1",
                                "internalName": "Form configuration 1",
                            },
                            "nl": {
                                "name": "Form configuratie 1",
                                "internalName": "Form configuratie 1",
                            },
                        },
                    },
                },
            ],
            "registrationBackends": [
                {
                    "key": "email-fu",
                    "name": "Email registration backend",
                    "backend": "email",
                    "options": {"toEmails": ["booboo@example.com", "yogi@example.com"]},
                },
            ],
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Form.objects.count(), 1)
        form.refresh_from_db()

        registration_backend = FormRegistrationBackend.objects.get()
        self.assertEqual(form.registration_backends.get(), registration_backend)
        self.assertEqual(registration_backend.name, "Email registration backend")
        self.assertEqual(registration_backend.key, "email-fu")
        self.assertEqual(registration_backend.backend, "email")
        self.assertEqual(
            registration_backend.options,
            {
                "attach_files_to_email": None,
                "to_emails": ["booboo@example.com", "yogi@example.com"],
            },
        )

    def test_update_clears_existing_auth_backends(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            authentication_backend="demo",
        )
        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": form.uuid},
        )
        data = {
            "name": "Update form",
            "slug": "update-form",
            "steps": [
                {
                    "slug": "step-1",
                    "formDefinition": {
                        "uuid": str(uuid4()),
                        "configuration": {
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "component1",
                                    "label": "component1",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                            ],
                        },
                        "translations": {
                            "en": {
                                "name": "Form configuration 1",
                                "internalName": "Form configuration 1",
                            },
                            "nl": {
                                "name": "Form configuratie 1",
                                "internalName": "Form configuratie 1",
                            },
                        },
                    },
                },
            ],
            "authBackends": [
                {
                    "backend": "digid",
                    "options": {"loa": DigiDAssuranceLevels.substantial},
                }
            ],
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Form.objects.count(), 1)
        form.refresh_from_db()

        authentication_backend = FormAuthenticationBackend.objects.get()
        self.assertEqual(authentication_backend.backend, "digid")
        self.assertEqual(
            authentication_backend.options, {"loa": DigiDAssuranceLevels.substantial}
        )

    def test_update_form_with_auto_login_backend_and_missing_from_auth_backend(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            authentication_backend="demo",
        )
        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": form.uuid},
        )
        data = {
            "name": "Update form",
            "slug": "update-form",
            "steps": [
                {
                    "slug": "step-1",
                    "formDefinition": {
                        "uuid": str(uuid4()),
                        "configuration": {
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "component1",
                                    "label": "component1",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                            ],
                        },
                    },
                },
            ],
            "autoLoginAuthenticationBackend": "digid",
            "authBackends": [],
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response_data = response.json()

        assert "invalidParams" in response_data and response_data["invalidParams"]
        self.assertEqual(len(response_data["invalidParams"]), 1)
        self.assertEqual(response_data["invalidParams"][0]["code"], "invalid")
        self.assertEqual(
            response_data["invalidParams"][0]["name"], "autoLoginAuthenticationBackend"
        )
        self.assertEqual(
            response_data["invalidParams"][0]["reason"],
            _(
                "The `auto_login_authentication_backend` must be one of the selected backends from `auth_backends`"
            ),
        )

    @enable_feature_flag("ENABLE_DEMO_PLUGINS")
    def test_create_form_without_configuration_options(self):
        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": "559812e7-9bff-4142-ab41-0cc8cf4e5e32"},
        )
        data = {
            "name": "Create form",
            "payment": {
                "backend": "demo",
                "options": {},
            },
            "slug": "create-form",
            "steps": [
                {
                    "slug": "step-1",
                    "formDefinition": {
                        "uuid": str(uuid4()),
                        "configuration": {
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "component1",
                                    "label": "component1",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                            ],
                        },
                        "translations": {
                            "en": {
                                "name": "Form configuration 1",
                                "internalName": "Form configuration 1",
                            },
                            "nl": {
                                "name": "Form configuratie 1",
                                "internalName": "Form configuratie 1",
                            },
                        },
                    },
                },
            ],
        }

        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Form.objects.count(), 1)
        form = Form.objects.get()

        self.assertEqual(form.payment_backend, "demo")

    def test_create_form_incorrect_request(self):
        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": "559812e7-9bff-4142-ab41-0cc8cf4e5e32"},
        )
        data = {
            "name": "Create form",
            "slug": "Create-form",
            "steps": [
                {
                    "slug": "step-1",
                    "formDefinition": {
                        "uuid": str(uuid4()),
                        "configuration": {
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "component1",
                                    "label": "component1",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                            ],
                        },
                        "translations": {
                            "en": {
                                "name": "Form configuration 1",
                                "internalName": "Form configuration 1",
                            },
                            "nl": {
                                "name": "Form configuratie 1",
                                "internalName": "Form configuratie 1",
                            },
                        },
                    },
                },
            ],
            "translations": "foobar",
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Form.objects.count(), 0)
        response_data = response.json()
        assert "invalidParams" in response_data
        self.assertEqual(len(response_data["invalidParams"]), 1)
        self.assertEqual(response_data["invalidParams"][0]["code"], "invalid")
        self.assertEqual(
            response_data["invalidParams"][0]["name"], "translations.nonFieldErrors"
        )

    def test_create_incorrect_form_configuration(self):
        form_definition_uuid = str(uuid4())
        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": "559812e7-9bff-4142-ab41-0cc8cf4e5e32"},
        )
        data = {
            "name": "Create form",
            "slug": "create-form",
            "steps": [
                {
                    "index": 1,
                    "slug": "step-1",
                    "formDefinition": {
                        "uuid": form_definition_uuid,
                        "isReusable": True,
                        "loginRequired": True,
                        "configuration": {
                            "components": [["bogus", "data"]],
                        },
                        "translations": {
                            "en": {
                                "name": "Form configuration 1",
                                "internalName": "Form configuration 1",
                            },
                            "nl": {
                                "name": "Form configuratie 1",
                                "internalName": "Form configuratie 1",
                            },
                        },
                    },
                }
            ],
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        assert "invalidParams" in response_data
        self.assertEqual(len(response_data["invalidParams"]), 1)
        self.assertEqual(response_data["invalidParams"][0]["code"], "not_a_dict")
        self.assertEqual(
            response_data["invalidParams"][0]["name"],
            "steps.0.formDefinition.configuration.components.0",
        )

    def test_create_regular_form_requires_at_least_one_step(self):
        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": "559812e7-9bff-4142-ab41-0cc8cf4e5e32"},
        )
        data = {
            "name": "Create form",
            "slug": "create-form",
            "type": FormTypeChoices.regular,
            "steps": [],
        }
        response = self.client.put(url, data=data)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        assert "invalidParams" in response_data and response_data["invalidParams"]
        self.assertEqual(len(response_data["invalidParams"]), 1)
        self.assertEqual(response_data["invalidParams"][0]["code"], "invalid")
        self.assertEqual(response_data["invalidParams"][0]["name"], "nonFieldErrors")
        self.assertEqual(
            response_data["invalidParams"][0]["reason"],
            _("At least one form step is required in a regular form."),
        )

    def test_create_appointment_form_requires_zero_steps(self):
        config = AppointmentsConfig.get_solo()
        config.plugin = "demo"
        config.save()

        self.addCleanup(AppointmentsConfig.clear_cache)

        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": "559812e7-9bff-4142-ab41-0cc8cf4e5e32"},
        )
        data = {
            "name": "Create form",
            "slug": "create-form",
            "type": FormTypeChoices.appointment,
            "steps": [
                {
                    "slug": "step-1",
                    "formDefinition": {
                        "uuid": uuid4(),
                        "isReusable": True,
                        "loginRequired": True,
                        "configuration": {
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "component1",
                                    "label": "component1",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                            ],
                        },
                        "translations": {
                            "en": {
                                "name": "Form configuration 1",
                                "internalName": "Form configuration 1",
                            },
                            "nl": {
                                "name": "Form configuratie 1",
                                "internalName": "Form configuratie 1",
                            },
                        },
                    },
                }
            ],
        }
        response = self.client.put(url, data=data)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert "invalidParams" in response_data and response_data["invalidParams"]
        self.assertEqual(len(response_data["invalidParams"]), 1)
        self.assertEqual(response_data["invalidParams"][0]["code"], "invalid")
        self.assertEqual(response_data["invalidParams"][0]["name"], "nonFieldErrors")
        self.assertEqual(
            response_data["invalidParams"][0]["reason"],
            _("Form steps are not allowed in an appointment form."),
        )

    def test_create_single_step_form_requires_exactly_one_step(self):
        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": "559812e7-9bff-4142-ab41-0cc8cf4e5e32"},
        )
        data = {
            "name": "Create form",
            "slug": "create-form",
            "type": FormTypeChoices.single_step,
            "steps": [],
        }
        response = self.client.put(url, data=data)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert "invalidParams" in response_data and response_data["invalidParams"]
        self.assertEqual(len(response_data["invalidParams"]), 1)
        self.assertEqual(response_data["invalidParams"][0]["code"], "invalid")
        self.assertEqual(response_data["invalidParams"][0]["name"], "nonFieldErrors")
        self.assertEqual(
            response_data["invalidParams"][0]["reason"],
            _("Exactly one form step is required in a single step form."),
        )

    def test_create_appointment_form_with_appointment_plugin(self):
        config = AppointmentsConfig.get_solo()
        config.plugin = "demo"
        config.save()

        self.addCleanup(AppointmentsConfig.clear_cache)

        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": "559812e7-9bff-4142-ab41-0cc8cf4e5e32"},
        )
        data = {
            "name": "Create form",
            "slug": "create-form",
            "type": FormTypeChoices.appointment,
            "steps": [],
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Form.objects.count(), 1)

        form = Form.objects.get()

        self.assertEqual(form.name, "Create form")
        self.assertEqual(form.slug, "create-form")
        self.assertEqual(form.type, FormTypeChoices.appointment)

    def test_create_appointment_form_with_appointment_plugin_disabled(self):
        AppointmentsConfig.clear_cache()
        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": "559812e7-9bff-4142-ab41-0cc8cf4e5e32"},
        )
        data = {
            "name": "Create form",
            "slug": "create-form",
            "type": FormTypeChoices.appointment,
            "steps": [],
        }
        response = self.client.put(url, data=data)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert "invalidParams" in response_data and response_data["invalidParams"]
        self.assertEqual(len(response_data["invalidParams"]), 1)
        self.assertEqual(response_data["invalidParams"][0]["code"], "invalid")
        self.assertEqual(response_data["invalidParams"][0]["name"], "type")
        self.assertEqual(
            response_data["invalidParams"][0]["reason"],
            _("Appointment forms require an appointment plugin to be configured."),
        )

    def test_incorrect_payment_backend_options(self):
        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": "559812e7-9bff-4142-ab41-0cc8cf4e5e32"},
        )
        data = {
            "name": "Create form",
            "payment": {
                "backend": "worldline",
                "options": {
                    "foo": "bar",
                },
            },
            "slug": "create-form",
            "steps": [
                {
                    "slug": "step-1",
                    "formDefinition": {
                        "uuid": str(uuid4()),
                        "configuration": {
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "component1",
                                    "label": "component1",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                            ],
                        },
                        "translations": {
                            "en": {
                                "name": "Form configuration 1",
                                "internalName": "Form configuration 1",
                            },
                            "nl": {
                                "name": "Form configuratie 1",
                                "internalName": "Form configuratie 1",
                            },
                        },
                    },
                },
            ],
        }

        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Form.objects.count(), 0)
        response_data = response.json()
        assert "invalidParams" in response_data
        self.assertEqual(len(response_data["invalidParams"]), 1)
        self.assertEqual(response_data["invalidParams"][0]["code"], "required")
        self.assertEqual(
            response_data["invalidParams"][0]["name"],
            "payment.options.merchant",
        )

    def test_update_existing_form(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            name="Create form",
            slug="create-form",
        )

        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": str(form.uuid)},
        )
        data = {
            "name": "Update form",
            "slug": "update-form",
            "steps": [
                {
                    "slug": "step-1",
                    "formDefinition": {
                        "uuid": str(uuid4()),
                        "configuration": {
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "component1",
                                    "label": "component1",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                            ],
                        },
                        "translations": {
                            "en": {
                                "name": "Form configuration 1",
                                "internalName": "Form configuration 1",
                            },
                            "nl": {
                                "name": "Form configuratie 1",
                                "internalName": "Form configuratie 1",
                            },
                        },
                    },
                },
            ],
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Form.objects.count(), 1)
        form.refresh_from_db()

        self.assertEqual(form.name, "Update form")
        self.assertEqual(form.slug, "update-form")

    def test_update_soft_deleted_form(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            name="Create form",
            slug="create-form",
            active=True,
            deleted_=True,
        )

        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": str(form.uuid)},
        )
        data = {
            "name": "Update form",
            "slug": "update-form",
            "steps": [
                {
                    "slug": "step-1",
                    "formDefinition": {
                        "uuid": str(uuid4()),
                        "configuration": {
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "component1",
                                    "label": "component1",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                            ],
                        },
                        "translations": {
                            "en": {
                                "name": "Form configuration 1",
                                "internalName": "Form configuration 1",
                            },
                            "nl": {
                                "name": "Form configuratie 1",
                                "internalName": "Form configuratie 1",
                            },
                        },
                    },
                },
            ],
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Form.objects.count(), 1)
        form.refresh_from_db()

        self.assertEqual(form.name, "Update form")
        self.assertEqual(form.slug, "update-form")
        self.assertTrue(form._is_deleted)

    def test_update_clears_existing_form_steps(self):
        form = FormFactory.create()
        FormStepFactory.create_batch(size=2, form=form)
        form_step_1_definition_uuid = uuid4()
        form_step_2_definition_uuid = uuid4()

        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": form.uuid},
        )
        data = {
            "name": "Update form",
            "slug": "update-form",
            "steps": [
                {
                    "slug": "step-2",
                    "formDefinition": {
                        "uuid": str(form_step_2_definition_uuid),
                        "isReusable": True,
                        "loginRequired": True,
                        "configuration": {
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "component1",
                                    "label": "component1",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                            ],
                        },
                        "translations": {
                            "en": {
                                "name": "Form configuration 2",
                                "internalName": "Form configuration 2",
                            },
                            "nl": {
                                "name": "Form configuratie 2",
                                "internalName": "Form configuratie 2",
                            },
                        },
                    },
                },
                {
                    "slug": "step-1",
                    "formDefinition": {
                        "uuid": str(form_step_1_definition_uuid),
                        "isReusable": False,
                        "loginRequired": False,
                        "configuration": {
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "component2",
                                    "label": "component2",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                                {
                                    "type": "textfield",
                                    "key": "component3",
                                    "label": "component3",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                            ],
                        },
                        "translations": {
                            "en": {
                                "name": "Form configuration 1",
                                "internalName": "Form configuration 1",
                            },
                            "nl": {
                                "name": "Form configuratie 1",
                                "internalName": "Form configuratie 1",
                            },
                        },
                    },
                },
            ],
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Form.objects.count(), 1)
        form.refresh_from_db()

        # form step
        form_steps = form.formstep_set.order_by("order")
        self.assertEqual(form_steps[0].order, 0)
        self.assertEqual(form_steps[0].slug, "step-2")
        self.assertEqual(form_steps[1].order, 1)
        self.assertEqual(form_steps[1].slug, "step-1")

        # step form definitions
        form_definition = form_steps[0].form_definition
        self.assertEqual(form_definition.uuid, form_step_2_definition_uuid)
        self.assertTrue(form_definition.is_reusable)
        self.assertTrue(form_definition.login_required)
        self.assertEqual(
            form_definition.configuration,
            {
                "components": [
                    {
                        "type": "textfield",
                        "key": "component1",
                        "label": "component1",
                        "hidden": False,
                        "clearOnHide": True,
                    },
                ],
            },
        )

        form_definition = form_steps[1].form_definition
        self.assertEqual(form_definition.uuid, form_step_1_definition_uuid)
        self.assertFalse(form_definition.is_reusable)
        self.assertFalse(form_definition.login_required)
        self.assertEqual(
            form_definition.configuration,
            {
                "components": [
                    {
                        "type": "textfield",
                        "key": "component2",
                        "label": "component2",
                        "hidden": False,
                        "clearOnHide": True,
                    },
                    {
                        "type": "textfield",
                        "key": "component3",
                        "label": "component3",
                        "hidden": False,
                        "clearOnHide": True,
                    },
                ],
            },
        )

    def test_update_reuse_existing_form_definition(self):
        # Generate an unrelated form with an existing form definition which will be reused
        existing_form_definition_uuid = uuid4()
        unrelated_form_step = FormStepFactory.create(
            form_definition__configuration={
                "components": [
                    {"key": "textfield", "type": "textfield", "label": "textfield"}
                ]
            },
            form_definition__is_reusable=True,
            form_definition__uuid=existing_form_definition_uuid,
        )

        existing_form_step = FormStepFactory.create()
        existing_form = existing_form_step.form

        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": existing_form.uuid},
        )
        data = {
            "name": "Update form",
            "slug": "update-form",
            "steps": [
                {
                    "slug": "step-1",
                    "formDefinition": {
                        "uuid": str(existing_form_definition_uuid),
                        "configuration": {
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "component1",
                                    "label": "component1",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                                {
                                    "type": "textfield",
                                    "key": "component2",
                                    "label": "component2",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                            ],
                        },
                        "translations": {
                            "en": {
                                "name": "Form configuration 1",
                            },
                            "nl": {
                                "name": "Form configuratie 1",
                            },
                        },
                    },
                },
            ],
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Form.objects.count(), 2)
        existing_form.refresh_from_db()

        # form step
        form_step = existing_form.formstep_set.get()
        self.assertEqual(form_step.order, 0)
        self.assertEqual(form_step.slug, "step-1")

        # step form definition
        self.assertEqual(form_step.form_definition, unrelated_form_step.form_definition)
        self.assertEqual(
            form_step.form_definition.configuration,
            {
                "components": [
                    {
                        "type": "textfield",
                        "key": "component1",
                        "label": "component1",
                        "hidden": False,
                        "clearOnHide": True,
                    },
                    {
                        "type": "textfield",
                        "key": "component2",
                        "label": "component2",
                        "hidden": False,
                        "clearOnHide": True,
                    },
                ],
            },
        )
        self.assertEqual(FormDefinition.objects.count(), 1)

    def test_update_unique_form_step_form_definition(self):
        form = FormFactory.create()
        FormStepFactory.create_batch(size=2, form=form)
        new_form_definition_uuid = uuid4()

        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": form.uuid},
        )
        data = {
            "name": "Update form",
            "slug": "update-form",
            "steps": [
                {
                    "index": 2,
                    "slug": "step-2",
                    "formDefinition": {
                        "uuid": str(new_form_definition_uuid),
                        "isReusable": True,
                        "loginRequired": True,
                        "configuration": {
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "component1",
                                    "label": "component1",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                                {
                                    "type": "textfield",
                                    "key": "component2",
                                    "label": "component2",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                            ],
                        },
                        "translations": {
                            "en": {
                                "name": "Form configuration 1",
                                "internalName": "Form configuration 1",
                            },
                            "nl": {
                                "name": "Form configuratie 1",
                                "internalName": "Form configuratie 1",
                            },
                        },
                    },
                },
                {
                    "index": 1,
                    "slug": "step-1",
                    "formDefinition": {
                        "uuid": str(new_form_definition_uuid),
                        "isReusable": True,
                        "loginRequired": True,
                        "configuration": {
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "component1",
                                    "label": "component1",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                                {
                                    "type": "textfield",
                                    "key": "component2",
                                    "label": "component2",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                            ],
                        },
                        "translations": {
                            "en": {
                                "name": "Form configuration 1",
                                "internalName": "Form configuration 1",
                            },
                            "nl": {
                                "name": "Form configuratie 1",
                                "internalName": "Form configuratie 1",
                            },
                        },
                    },
                },
            ],
        }
        response = self.client.put(url, data=data)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert "invalidParams" in response_data
        self.assertEqual(len(response_data["invalidParams"]), 1)
        self.assertEqual(response_data["invalidParams"][0]["code"], "invalid")
        self.assertEqual(response_data["invalidParams"][0]["name"], "steps")
        self.assertEqual(
            response_data["invalidParams"][0]["reason"],
            _("Non-unique form step - form definition duplicate(s) detected."),
        )

        self.assertEqual(Form.objects.count(), 1)

    def test_update_unique_form_definition_keys_across_steps(self):
        form = FormFactory.create()

        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": form.uuid},
        )
        data = {
            "name": "Update form",
            "slug": "update-form",
            "steps": [
                {
                    "index": 2,
                    "slug": "step-2",
                    "formDefinition": {
                        "uuid": str(uuid4()),
                        "isReusable": True,
                        "loginRequired": True,
                        "configuration": {
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "component1",
                                    "label": "component1",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                            ],
                        },
                        "translations": {
                            "en": {
                                "name": "Form configuration 2",
                                "internalName": "Form configuration 2",
                            },
                            "nl": {
                                "name": "Form configuratie 2",
                                "internalName": "Form configuratie 2",
                            },
                        },
                    },
                },
                {
                    "index": 1,
                    "slug": "step-1",
                    "formDefinition": {
                        "uuid": str(uuid4()),
                        "isReusable": False,
                        "loginRequired": False,
                        "configuration": {
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "component1",
                                    "label": "component1",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                                {
                                    "type": "textfield",
                                    "key": "component2",
                                    "label": "component2",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                            ],
                        },
                        "translations": {
                            "en": {
                                "name": "Form configuration 1",
                                "internalName": "Form configuration 1",
                            },
                            "nl": {
                                "name": "Form configuratie 1",
                                "internalName": "Form configuratie 1",
                            },
                        },
                    },
                },
            ],
        }
        response = self.client.put(url, data=data)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert "invalidParams" in response_data and response_data["invalidParams"]
        errors = response_data["invalidParams"]
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["code"], "invalid")
        self.assertEqual(errors[0]["name"], "steps")
        assert "reason" in errors[0]
        expected_error_message = _(
            "Detected duplicate keys in configuration: {errors}"
        ).format(
            errors=get_text_list(
                [
                    _('"{duplicate_key}" (in {paths})').format(
                        duplicate_key="component1",
                        paths="component1, component1",
                    )
                ],
                ", ",
            )
        )
        self.assertEqual(errors[0]["reason"], expected_error_message)

    def test_update_unique_form_definition_keys_one_step(self):
        form = FormFactory.create()
        form_definition_uuid = uuid4()
        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": form.uuid},
        )
        data = {
            "name": "Update form",
            "slug": "update-form",
            "steps": [
                {
                    "index": 1,
                    "slug": "step-1",
                    "formDefinition": {
                        "uuid": str(form_definition_uuid),
                        "isReusable": False,
                        "loginRequired": False,
                        "configuration": {
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "component1",
                                    "label": "component1",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                                {
                                    "type": "textfield",
                                    "key": "component2",
                                    "label": "component2",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                                {
                                    "type": "textfield",
                                    "key": "component1",
                                    "label": "component1",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                            ],
                        },
                        "translations": {
                            "en": {
                                "name": "Form configuration 1",
                                "internalName": "Form configuration 1",
                            },
                            "nl": {
                                "name": "Form configuratie 1",
                                "internalName": "Form configuratie 1",
                            },
                        },
                    },
                },
            ],
        }
        response = self.client.put(url, data=data)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert "invalidParams" in response_data and response_data["invalidParams"]
        errors = response_data["invalidParams"]
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["code"], "invalid")
        self.assertEqual(errors[0]["name"], "steps")
        assert "reason" in errors[0]
        expected_error_message = _(
            "Duplicate component key detected in form definition {form_definition}."
        ).format(form_definition=form_definition_uuid)
        self.assertEqual(errors[0]["reason"], expected_error_message)

    def test_update_unique_form_definition_keys_one_step_editgrid(self):
        form = FormFactory.create()
        form_definition_uuid = uuid4()
        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": form.uuid},
        )
        data = {
            "name": "Update form",
            "slug": "update-form",
            "steps": [
                {
                    "index": 1,
                    "slug": "step-1",
                    "formDefinition": {
                        "uuid": str(form_definition_uuid),
                        "isReusable": False,
                        "loginRequired": False,
                        "configuration": {
                            "components": [
                                {
                                    "key": "repeatingGroup",
                                    "type": "editgrid",
                                    "label": "repeatingGroup",
                                    "groupLabel": "Item",
                                    "components": [
                                        {
                                            "type": "file",
                                            "key": "fileInRepeatingGroup1",
                                            "label": "fileInRepeatingGroup1",
                                            "file": {"type": []},
                                            "filePattern": "",
                                        },
                                        {
                                            "type": "file",
                                            "key": "fileInRepeatingGroup1",
                                            "label": "fileInRepeatingGroup1",
                                            "file": {"type": []},
                                            "filePattern": "",
                                        },
                                    ],
                                },
                            ],
                        },
                        "translations": {
                            "en": {
                                "name": "Form configuration 1",
                                "internalName": "Form configuration 1",
                            },
                            "nl": {
                                "name": "Form configuratie 1",
                                "internalName": "Form configuratie 1",
                            },
                        },
                    },
                },
            ],
        }
        response = self.client.put(url, data=data)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert "invalidParams" in response_data and response_data["invalidParams"]
        errors = response_data["invalidParams"]
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["code"], "invalid")
        self.assertEqual(errors[0]["name"], "steps")
        assert "reason" in errors[0]
        expected_error_message = _(
            "Duplicate component key detected in form definition {form_definition}."
        ).format(form_definition=form_definition_uuid)

        self.assertEqual(errors[0]["reason"], expected_error_message)

    def test_update_form_incorrect_request(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            name="Create form",
        )

        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": str(form.uuid)},
        )
        data = {
            "name": "Update form",
            "slug": "update-form",
            "steps": [
                {
                    "slug": "step-1",
                    "formDefinition": {
                        "uuid": str(uuid4()),
                        "configuration": {
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "component1",
                                    "label": "component1",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                            ],
                        },
                        "translations": {
                            "en": {
                                "name": "Form configuration 1",
                                "internalName": "Form configuration 1",
                            },
                            "nl": {
                                "name": "Form configuratie 1",
                                "internalName": "Form configuratie 1",
                            },
                        },
                    },
                },
            ],
            "translations": "foobar",
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        assert "invalidParams" in response_data
        self.assertEqual(len(response_data["invalidParams"]), 1)
        self.assertEqual(response_data["invalidParams"][0]["code"], "invalid")
        self.assertEqual(
            response_data["invalidParams"][0]["name"], "translations.nonFieldErrors"
        )

        self.assertEqual(Form.objects.count(), 1)
        form.refresh_from_db()
        self.assertEqual(form.name, "Create form")
        self.assertIsNone(form.previous_text_nl)
        self.assertIsNone(form.previous_text_en)
        self.assertIsNone(form.begin_text_nl)
        self.assertIsNone(form.begin_text_en)
        self.assertIsNone(form.change_text_nl)
        self.assertIsNone(form.change_text_en)
        self.assertIsNone(form.confirm_text_nl)
        self.assertIsNone(form.confirm_text_en)

    def test_inactive_form(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            name="Create form",
            slug="create-form",
            active=False,
        )

        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": str(form.uuid)},
        )
        data = {
            "name": "Update form",
            "slug": "update-form",
            "steps": [
                {
                    "slug": "step-1",
                    "formDefinition": {
                        "uuid": str(uuid4()),
                        "configuration": {
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "component1",
                                    "label": "component1",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                            ],
                        },
                        "translations": {
                            "en": {
                                "name": "Form configuration 1",
                                "internalName": "Form configuration 1",
                            },
                            "nl": {
                                "name": "Form configuratie 1",
                                "internalName": "Form configuratie 1",
                            },
                        },
                    },
                },
            ],
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Form.objects.count(), 1)
        form.refresh_from_db()

        self.assertEqual(form.name, "Update form")
        self.assertEqual(form.slug, "update-form")
        self.assertFalse(form.active)

    def test_unsupported_patch(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            name="Create form",
            slug="create-form",
        )

        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": str(form.uuid)},
        )
        data = {
            "name": "Update form",
            "slug": "update-form",
            "steps": [],
        }
        response = self.client.patch(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(Form.objects.count(), 1)

    def test_unsupported_post(self):
        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": "559812e7-9bff-4142-ab41-0cc8cf4e5e32"},
        )
        data = {
            "name": "Create form",
            "slug": "create-form",
            "steps": [],
        }
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(Form.objects.count(), 0)


class FormEndpointVariableTests(APITestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        cls.admin_user = UserFactory.create(
            is_staff=True, user_permissions=("forms.change_form",)
        )

    def setUp(self) -> None:
        super().setUp()

        self.client.force_authenticate(user=self.admin_user)

    def test_user_defined_variables(self):
        form_definition_uuid = uuid4()
        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": "559812e7-9bff-4142-ab41-0cc8cf4e5e32"},
        )
        data = {
            "name": "Create form",
            "slug": "create-form",
            "steps": [
                {
                    "slug": "step-1",
                    "formDefinition": {
                        "uuid": form_definition_uuid,
                        "configuration": {
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "component1",
                                    "label": "component1",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                            ],
                        },
                        "translations": {
                            "en": {
                                "name": "Form configuration 1",
                                "internalName": "Form configuration 1",
                            },
                            "nl": {
                                "name": "Form configuratie 1",
                                "internalName": "Form configuratie 1",
                            },
                        },
                    },
                },
            ],
            "variables": [
                {
                    "name": "extra_var",
                    "key": "extra_var",
                    "source": FormVariableSources.user_defined,
                    "formDefinition": None,
                    "dataType": FormVariableDataTypes.string,
                },
            ],
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Form.objects.count(), 1)
        form = Form.objects.get()
        variables = form.formvariable_set.order_by("name")

        # component variable, generated for the form step (based on the form defintion)
        self.assertEqual(variables[0].name, "component1")
        self.assertEqual(variables[0].key, "component1")
        self.assertEqual(variables[0].source, FormVariableSources.component)
        self.assertEqual(variables[0].form_definition.uuid, form_definition_uuid)
        self.assertEqual(variables[0].data_type, FormVariableDataTypes.string)

        # user defined variable, from the request body
        self.assertEqual(variables[1].name, "extra_var")
        self.assertEqual(variables[1].key, "extra_var")
        self.assertEqual(variables[1].source, FormVariableSources.user_defined)
        self.assertIsNone(variables[1].form_definition)
        self.assertEqual(variables[1].data_type, FormVariableDataTypes.string)

    def test_user_defined_profile_form_variable(self):
        customer_interactions_api = CustomerInteractionsAPIGroupConfigFactory.create()
        form_definition_uuid = uuid4()
        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": "559812e7-9bff-4142-ab41-0cc8cf4e5e32"},
        )
        data = {
            "name": "Create form",
            "slug": "create-form",
            "steps": [
                {
                    "slug": "step-1",
                    "formDefinition": {
                        "uuid": form_definition_uuid,
                        "configuration": {
                            "components": [
                                {
                                    "type": "customerProfile",
                                    "key": "profile",
                                    "label": "Profile",
                                    "digitalAddressTypes": ["email"],
                                    "shouldUpdateCustomerData": True,
                                }
                            ],
                        },
                        "translations": {
                            "en": {
                                "name": "Form configuration 1",
                                "internalName": "Form configuration 1",
                            },
                            "nl": {
                                "name": "Form configuratie 1",
                                "internalName": "Form configuratie 1",
                            },
                        },
                    },
                },
            ],
            "variables": [
                {
                    "name": "profile-prefill",
                    "key": "profilePrefill",
                    "formDefinition": None,
                    "source": FormVariableSources.user_defined,
                    "prefillPlugin": COMMUNICATION_PREFERENCES_PLUGIN_IDENTIFIER,
                    "prefillAttribute": "",
                    "prefillIdentifierRole": "main",
                    "prefillOptions": {
                        "customerInteractionsApiGroup": customer_interactions_api.identifier,
                        "profileFormVariable": "profile",
                    },
                    "dataType": FormVariableDataTypes.string,
                },
            ],
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Form.objects.count(), 1)
        form = Form.objects.get()
        variables = form.formvariable_set.order_by("name")

        # component variable, generated for the form step (based on the form defintion)
        self.assertEqual(variables[0].name, "Profile")
        self.assertEqual(variables[0].key, "profile")
        self.assertEqual(variables[0].source, FormVariableSources.component)
        self.assertEqual(variables[0].form_definition.uuid, form_definition_uuid)
        self.assertEqual(variables[0].data_type, FormVariableDataTypes.array)

        # user defined variable, from the request body
        self.assertEqual(variables[1].name, "profile-prefill")
        self.assertEqual(variables[1].key, "profilePrefill")
        self.assertEqual(variables[1].source, FormVariableSources.user_defined)
        self.assertIsNone(variables[1].form_definition)
        self.assertEqual(variables[1].data_type, FormVariableDataTypes.string)

    def test_service_configuration(self):
        form_definition_uuid = uuid4()
        service = ServiceFactory.create()
        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": "559812e7-9bff-4142-ab41-0cc8cf4e5e32"},
        )

        with self.subTest("Create form"):
            data = {
                "name": "Create form",
                "slug": "create-form",
                "steps": [
                    {
                        "slug": "step-1",
                        "formDefinition": {
                            "uuid": form_definition_uuid,
                            "configuration": {
                                "components": [
                                    {
                                        "type": "textfield",
                                        "key": "component1",
                                        "label": "component1",
                                        "hidden": False,
                                        "clearOnHide": True,
                                    },
                                ],
                            },
                            "translations": {
                                "en": {
                                    "name": "Form configuration 1",
                                    "internalName": "Form configuration 1",
                                },
                                "nl": {
                                    "name": "Form configuratie 1",
                                    "internalName": "Form configuratie 1",
                                },
                            },
                        },
                    },
                ],
                "variables": [
                    {
                        "name": "extra_var",
                        "key": "extra_var",
                        "source": FormVariableSources.user_defined,
                        "formDefinition": None,
                        "dataType": FormVariableDataTypes.string,
                        "serviceFetchConfiguration": {
                            "name": "Service fetch configuration 1",
                            "service": service.uuid,
                            "path": "/foobar",
                            "method": ServiceFetchMethods.get,
                            "headers": {
                                "Foo": "Bar",
                            },
                            "queryParams": {
                                "Bar": ["Foo"],
                            },
                            "body": None,
                            "dataMappingType": "",
                            "mappingExpression": None,
                            "cacheTimeout": None,
                        },
                    },
                ],
            }
            response = self.client.put(url, data=data)

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(Form.objects.count(), 1)
            form = Form.objects.get()
            variables = form.formvariable_set.order_by("source", "name")
            assert len(variables) == 2

            service_fetch_configuration = variables[1].service_fetch_configuration
            assert service_fetch_configuration
            self.assertEqual(
                service_fetch_configuration.name, "Service fetch configuration 1"
            )
            self.assertEqual(service_fetch_configuration.service, service)
            self.assertEqual(service_fetch_configuration.path, "/foobar")
            self.assertEqual(
                service_fetch_configuration.method, ServiceFetchMethods.get
            )
            self.assertEqual(service_fetch_configuration.headers, {"_foo": "Bar"})
            self.assertEqual(
                service_fetch_configuration.query_params, {"_bar": ["Foo"]}
            )
            self.assertIsNone(service_fetch_configuration.body)
            self.assertEqual(service_fetch_configuration.data_mapping_type, "")
            self.assertIsNone(service_fetch_configuration.mapping_expression)
            self.assertIsNone(service_fetch_configuration.cache_timeout)

        with self.subTest("Update form"):
            data = {
                "name": "Update form",
                "slug": "update-form",
                "steps": [
                    {
                        "slug": "step-1",
                        "formDefinition": {
                            "uuid": form_definition_uuid,
                            "configuration": {
                                "components": [
                                    {
                                        "type": "textfield",
                                        "key": "component1",
                                        "label": "component1",
                                        "hidden": False,
                                        "clearOnHide": True,
                                    },
                                ],
                            },
                            "translations": {
                                "en": {
                                    "name": "Form configuration 1",
                                    "internalName": "Form configuration 1",
                                },
                                "nl": {
                                    "name": "Form configuratie 1",
                                    "internalName": "Form configuratie 1",
                                },
                            },
                        },
                    },
                ],
                "variables": [
                    {
                        "name": "extra_var",
                        "key": "extra_var",
                        "source": FormVariableSources.user_defined,
                        "formDefinition": None,
                        "dataType": FormVariableDataTypes.string,
                        "serviceFetchConfiguration": {
                            "name": "Service fetch configuration 1",
                            "service": service.uuid,
                            "path": "/foobar",
                            "method": ServiceFetchMethods.get,
                            "headers": {
                                "Foo": "Bar",
                            },
                            "queryParams": {
                                "Bar": ["Foo"],
                            },
                            "body": None,
                            "dataMappingType": "",
                            "mappingExpression": None,
                            "cacheTimeout": None,
                        },
                    },
                ],
            }
            response = self.client.put(url, data=data)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(Form.objects.count(), 1)
            form = Form.objects.get()
            variables = form.formvariable_set.order_by("source", "name")
            assert len(variables) == 2

            service_fetch_configuration = variables[1].service_fetch_configuration
            assert service_fetch_configuration
            self.assertEqual(
                service_fetch_configuration.name, "Service fetch configuration 1"
            )
            self.assertEqual(service_fetch_configuration.service, service)
            self.assertEqual(service_fetch_configuration.path, "/foobar")
            self.assertEqual(
                service_fetch_configuration.method, ServiceFetchMethods.get
            )
            self.assertEqual(service_fetch_configuration.headers, {"_foo": "Bar"})
            self.assertEqual(
                service_fetch_configuration.query_params, {"_bar": ["Foo"]}
            )
            self.assertIsNone(service_fetch_configuration.body)
            self.assertEqual(service_fetch_configuration.data_mapping_type, "")
            self.assertIsNone(service_fetch_configuration.mapping_expression)
            self.assertIsNone(service_fetch_configuration.cache_timeout)

    def test_reuse_service_fetch_configuration(self):
        service = ServiceFactory.create()
        initial_service_fetch_configuration = ServiceFetchConfigurationFactory.create(
            name="Service fetch configuration foo", service=service
        )
        form_definition_uuid = uuid4()
        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": "559812e7-9bff-4142-ab41-0cc8cf4e5e32"},
        )

        with self.subTest("Create form"):
            data = {
                "name": "Create form",
                "slug": "create-form",
                "steps": [
                    {
                        "slug": "step-1",
                        "formDefinition": {
                            "uuid": form_definition_uuid,
                            "configuration": {
                                "components": [
                                    {
                                        "type": "textfield",
                                        "key": "component1",
                                        "label": "component1",
                                        "hidden": False,
                                        "clearOnHide": True,
                                    },
                                ],
                            },
                            "translations": {
                                "en": {
                                    "name": "Form configuration 1",
                                    "internalName": "Form configuration 1",
                                },
                                "nl": {
                                    "name": "Form configuratie 1",
                                    "internalName": "Form configuratie 1",
                                },
                            },
                        },
                    },
                ],
                "variables": [
                    {
                        "name": "extra_var",
                        "key": "extra_var",
                        "source": FormVariableSources.user_defined,
                        "formDefinition": None,
                        "dataType": FormVariableDataTypes.string,
                        "serviceFetchConfiguration": {
                            "id": initial_service_fetch_configuration.pk,
                            "name": "Service fetch configuration 1",
                            "service": service.uuid,
                            "path": "/foobar",
                            "method": ServiceFetchMethods.get,
                            "headers": {
                                "Foo": "Bar",
                            },
                            "queryParams": {
                                "Bar": ["Foo"],
                            },
                            "body": None,
                            "dataMappingType": "",
                            "mappingExpression": None,
                            "cacheTimeout": None,
                        },
                    },
                ],
            }
            response = self.client.put(url, data=data)

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(Form.objects.count(), 1)
            form = Form.objects.get()
            variables = form.formvariable_set.order_by("source", "name")
            assert len(variables) == 2

            service_fetch_configuration = variables[1].service_fetch_configuration
            assert service_fetch_configuration
            self.assertEqual(
                initial_service_fetch_configuration, service_fetch_configuration
            )
            self.assertEqual(
                service_fetch_configuration.name, "Service fetch configuration 1"
            )

        with self.subTest("Update form"):
            data = {
                "name": "Update form",
                "slug": "update-form",
                "steps": [
                    {
                        "slug": "step-1",
                        "formDefinition": {
                            "uuid": form_definition_uuid,
                            "configuration": {
                                "components": [
                                    {
                                        "type": "textfield",
                                        "key": "component1",
                                        "label": "component1",
                                        "hidden": False,
                                        "clearOnHide": True,
                                    },
                                ],
                            },
                            "translations": {
                                "en": {
                                    "name": "Form configuration 1",
                                    "internalName": "Form configuration 1",
                                },
                                "nl": {
                                    "name": "Form configuratie 1",
                                    "internalName": "Form configuratie 1",
                                },
                            },
                        },
                    },
                ],
                "variables": [
                    {
                        "name": "extra_var",
                        "key": "extra_var",
                        "source": FormVariableSources.user_defined,
                        "formDefinition": None,
                        "dataType": FormVariableDataTypes.string,
                        "serviceFetchConfiguration": {
                            "id": initial_service_fetch_configuration.pk,
                            "name": "Service fetch configuration 2",
                            "service": service.uuid,
                            "path": "/foobar",
                            "method": ServiceFetchMethods.get,
                            "headers": {
                                "Foo": "Bar",
                            },
                            "queryParams": {
                                "Bar": ["Foo"],
                            },
                            "body": None,
                            "dataMappingType": "",
                            "mappingExpression": None,
                            "cacheTimeout": None,
                        },
                    },
                ],
            }
            response = self.client.put(url, data=data)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(Form.objects.count(), 1)
            form = Form.objects.get()
            variables = form.formvariable_set.order_by("source", "name")
            assert len(variables) == 2

            service_fetch_configuration = variables[1].service_fetch_configuration
            assert service_fetch_configuration
            self.assertEqual(
                initial_service_fetch_configuration, service_fetch_configuration
            )
            self.assertEqual(
                service_fetch_configuration.name, "Service fetch configuration 2"
            )

    def test_update_recreates_variables(self):
        form = FormFactory.create()
        form_step_1_definition_uuid = UUID("7284fcde-0cde-4cb4-b2e5-1e472fceccfb")
        FormStepFactory.create(
            form=form,
            form_definition__uuid=form_step_1_definition_uuid,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "name",
                        "label": "name",
                    },
                    {
                        "type": "number",
                        "key": "age",
                        "label": "age",
                    },
                ]
            },
        )
        form_step_2_definition_uuid = UUID("3ab6da26-7407-4a39-a77c-8fd846ab6d8d")
        FormStepFactory.create(
            form=form,
            form_definition__uuid=form_step_2_definition_uuid,
            form_definition__configuration={
                "components": [
                    {
                        "type": "number",
                        "key": "nLargeBoxes",
                        "label": "nLargeBoxes",
                    },
                    {
                        "type": "number",
                        "key": "nGiganticBoxes",
                        "label": "nGiganticBoxes",
                    },
                ]
            },
        )

        form_step_3_definition_uuid = UUID("0d4a67fb-1aa3-4568-a5b3-a374842c048d")

        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": form.uuid},
        )
        data = {
            "name": "Update form",
            "slug": "update-form",
            "steps": [
                {
                    "slug": "step-1",
                    "formDefinition": {
                        "uuid": form_step_1_definition_uuid,
                        "isReusable": False,
                        "loginRequired": False,
                        "configuration": {
                            "components": [
                                {
                                    "type": "number",
                                    "key": "age",
                                    "label": "age",
                                },
                                {
                                    "type": "textfield",
                                    "key": "email",
                                    "label": "email",
                                },
                            ],
                        },
                        "translations": {
                            "en": {
                                "name": "Form configuration 1",
                                "internalName": "Form configuration 1",
                            },
                            "nl": {
                                "name": "Form configuratie 1",
                                "internalName": "Form configuratie 1",
                            },
                        },
                    },
                },
                {
                    "slug": "step-2",
                    "formDefinition": {
                        "uuid": form_step_2_definition_uuid,
                        "isReusable": False,
                        "loginRequired": True,
                        "configuration": {
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "city",
                                    "label": "city",
                                },
                            ],
                        },
                        "translations": {
                            "en": {
                                "name": "Form configuration 2",
                                "internalName": "Form configuration 2",
                            },
                            "nl": {
                                "name": "Form configuratie 2",
                                "internalName": "Form configuratie 2",
                            },
                        },
                    },
                },
                {
                    "slug": "step-3",
                    "formDefinition": {
                        "uuid": form_step_3_definition_uuid,
                        "isReusable": False,
                        "loginRequired": True,
                        "configuration": {
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "streetname",
                                    "label": "streetname",
                                },
                            ],
                        },
                        "translations": {
                            "en": {
                                "name": "Form configuration 3",
                                "internalName": "Form configuration 3",
                            },
                            "nl": {
                                "name": "Form configuratie 3",
                                "internalName": "Form configuratie 3",
                            },
                        },
                    },
                },
            ],
            "variables": [
                {
                    "name": "extra_var",
                    "key": "extra_var",
                    "source": FormVariableSources.user_defined,
                    "formDefinition": None,
                    "dataType": FormVariableDataTypes.string,
                },
            ],
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Form.objects.count(), 1)
        form = Form.objects.get()
        variables = form.formvariable_set.order_by("source", "name")

        self.assertEqual(variables.count(), 5)

        # component variables, generated for the form step (based on the form defintion)
        self.assertEqual(variables[0].name, "age")
        self.assertEqual(variables[0].key, "age")
        self.assertEqual(variables[0].source, FormVariableSources.component)
        self.assertEqual(variables[0].form_definition.uuid, form_step_1_definition_uuid)
        self.assertEqual(variables[0].data_type, FormVariableDataTypes.float)
        self.assertEqual(variables[1].name, "city")
        self.assertEqual(variables[1].key, "city")
        self.assertEqual(variables[1].source, FormVariableSources.component)
        self.assertEqual(variables[1].form_definition.uuid, form_step_2_definition_uuid)
        self.assertEqual(variables[1].data_type, FormVariableDataTypes.string)
        self.assertEqual(variables[2].name, "email")
        self.assertEqual(variables[2].key, "email")
        self.assertEqual(variables[2].source, FormVariableSources.component)
        self.assertEqual(variables[2].form_definition.uuid, form_step_1_definition_uuid)
        self.assertEqual(variables[2].data_type, FormVariableDataTypes.string)
        self.assertEqual(variables[3].name, "streetname")
        self.assertEqual(variables[3].key, "streetname")
        self.assertEqual(variables[3].source, FormVariableSources.component)
        self.assertEqual(variables[3].form_definition.uuid, form_step_3_definition_uuid)
        self.assertEqual(variables[3].data_type, FormVariableDataTypes.string)

        # user defined variable, from the request body
        self.assertEqual(variables[4].name, "extra_var")
        self.assertEqual(variables[4].key, "extra_var")
        self.assertEqual(variables[4].source, FormVariableSources.user_defined)
        self.assertIsNone(variables[4].form_definition)
        self.assertEqual(variables[4].data_type, FormVariableDataTypes.string)

    def test_component_variables_ignored(self):
        form_definition_uuid = uuid4()
        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": "559812e7-9bff-4142-ab41-0cc8cf4e5e32"},
        )

        with self.subTest("Create form"):
            data = {
                "name": "Create form",
                "slug": "create-form",
                "steps": [
                    {
                        "slug": "step-1",
                        "formDefinition": {
                            "uuid": form_definition_uuid,
                            "configuration": {
                                "components": [
                                    {
                                        "type": "textfield",
                                        "key": "component1",
                                        "label": "component1",
                                        "hidden": False,
                                        "clearOnHide": True,
                                    },
                                ],
                            },
                            "translations": {
                                "en": {
                                    "name": "Form configuration 1",
                                    "internalName": "Form configuration 1",
                                },
                                "nl": {
                                    "name": "Form configuratie 1",
                                    "internalName": "Form configuratie 1",
                                },
                            },
                        },
                    },
                ],
                "variables": [
                    {
                        "name": "extra_var",
                        "key": "extra_var",
                        "source": FormVariableSources.user_defined,
                        "formDefinition": None,
                        "dataType": FormVariableDataTypes.string,
                    },
                    {
                        "name": "ignored",
                        "key": "textfield",
                        "source": FormVariableSources.component,
                        "formDefinition": form_definition_uuid,
                        "dataType": FormVariableDataTypes.string,
                    },
                ],
            }
            response = self.client.put(url, data=data)

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(Form.objects.count(), 1)
            form = Form.objects.get()
            variables = form.formvariable_set.order_by("name")
            self.assertEqual(variables.count(), 2)

            # component variable, generated for the form step (based on the form defintion)
            self.assertEqual(variables[0].name, "component1")
            self.assertEqual(variables[0].key, "component1")

            # user defined variable, from the request body
            self.assertEqual(variables[1].key, "extra_var")
            self.assertEqual(variables[1].source, FormVariableSources.user_defined)

        with self.subTest("Update form"):
            data = {
                "name": "Create form",
                "slug": "create-form",
                "steps": [
                    {
                        "slug": "step-1",
                        "formDefinition": {
                            "uuid": form_definition_uuid,
                            "configuration": {
                                "components": [
                                    {
                                        "type": "textfield",
                                        "key": "component1",
                                        "label": "component1",
                                        "hidden": False,
                                        "clearOnHide": True,
                                    },
                                ],
                            },
                            "translations": {
                                "en": {
                                    "name": "Form configuration 1",
                                    "internalName": "Form configuration 1",
                                },
                                "nl": {
                                    "name": "Form configuratie 1",
                                    "internalName": "Form configuratie 1",
                                },
                            },
                        },
                    },
                ],
                "variables": [
                    {
                        "name": "extra_var",
                        "key": "extra_var",
                        "source": FormVariableSources.user_defined,
                        "formDefinition": None,
                        "dataType": FormVariableDataTypes.string,
                    },
                    {
                        "name": "ignored",
                        "key": "textfield",
                        "source": FormVariableSources.component,
                        "formDefinition": form_definition_uuid,
                        "dataType": FormVariableDataTypes.string,
                    },
                ],
            }
            response = self.client.put(url, data=data)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(Form.objects.count(), 1)
            form = Form.objects.get()
            variables = form.formvariable_set.order_by("name")
            self.assertEqual(variables.count(), 2)

            # component variable, generated for the form step (based on the form defintion)
            self.assertEqual(variables[0].name, "component1")
            self.assertEqual(variables[0].key, "component1")

            # user defined variable, from the request body
            self.assertEqual(variables[1].key, "extra_var")
            self.assertEqual(variables[1].source, FormVariableSources.user_defined)

    def test_static_variable_collision(self):
        form_definition_uuid = uuid4()
        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": "559812e7-9bff-4142-ab41-0cc8cf4e5e32"},
        )
        data = {
            "name": "Create form",
            "slug": "create-form",
            "steps": [
                {
                    "slug": "step-1",
                    "formDefinition": {
                        "uuid": form_definition_uuid,
                        "configuration": {
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "component1",
                                    "label": "component1",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                            ],
                        },
                        "translations": {
                            "en": {
                                "name": "Form configuration 1",
                                "internalName": "Form configuration 1",
                            },
                            "nl": {
                                "name": "Form configuratie 1",
                                "internalName": "Form configuratie 1",
                            },
                        },
                    },
                },
            ],
            "variables": [
                {
                    "name": "extra_var",
                    "key": "extra_var",
                    "source": FormVariableSources.user_defined,
                    "formDefinition": None,
                    "dataType": FormVariableDataTypes.string,
                },
                {
                    "name": "Static variable collision",
                    "key": "form_name",
                    "source": FormVariableSources.user_defined,
                    "formDefinition": form_definition_uuid,
                    "dataType": FormVariableDataTypes.string,
                },
            ],
        }
        response = self.client.put(url, data=data)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Form.objects.count(), 0)
        self.assertEqual(len(response_data["invalidParams"]), 1)
        error_message = response_data["invalidParams"][0]
        self.assertEqual(error_message["code"], "unique")
        self.assertEqual(error_message["name"], "variables.1")
        self.assertTrue("static variable keys" in error_message["reason"])

    def test_component_variable_collision(self):
        form_definition_uuid = uuid4()
        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": "559812e7-9bff-4142-ab41-0cc8cf4e5e32"},
        )
        data = {
            "name": "Create form",
            "slug": "create-form",
            "steps": [
                {
                    "slug": "step-1",
                    "formDefinition": {
                        "uuid": form_definition_uuid,
                        "configuration": {
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "component1",
                                    "label": "component1",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                            ],
                        },
                        "translations": {
                            "en": {
                                "name": "Form configuration 1",
                                "internalName": "Form configuration 1",
                            },
                            "nl": {
                                "name": "Form configuratie 1",
                                "internalName": "Form configuratie 1",
                            },
                        },
                    },
                },
            ],
            "variables": [
                {
                    "name": "extra_var",
                    "key": "extra_var",
                    "source": FormVariableSources.user_defined,
                    "formDefinition": None,
                    "dataType": FormVariableDataTypes.string,
                },
                {
                    "name": "Component variable collision",
                    "key": "component1",
                    "source": FormVariableSources.user_defined,
                    "formDefinition": form_definition_uuid,
                    "dataType": FormVariableDataTypes.string,
                },
            ],
        }
        response = self.client.put(url, data=data)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Form.objects.count(), 0)
        self.assertEqual(len(response_data["invalidParams"]), 1)
        error_message = response_data["invalidParams"][0]
        self.assertEqual(error_message["code"], "unique")
        self.assertEqual(error_message["name"], "variables.1")
        self.assertTrue("component variable keys" in error_message["reason"])

    def test_user_defined_all_prefill_fields(self):
        customer_interactions_api = CustomerInteractionsAPIGroupConfigFactory.create()
        form_definition_uuid = uuid4()
        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": "559812e7-9bff-4142-ab41-0cc8cf4e5e32"},
        )
        data = {
            "name": "Create form",
            "slug": "create-form",
            "steps": [
                {
                    "slug": "step-1",
                    "formDefinition": {
                        "uuid": form_definition_uuid,
                        "configuration": {
                            "components": [
                                {
                                    "type": "customerProfile",
                                    "key": "profile",
                                    "label": "Profile",
                                    "digitalAddressTypes": ["email"],
                                    "shouldUpdateCustomerData": True,
                                }
                            ],
                        },
                        "translations": {
                            "en": {
                                "name": "Form configuration 1",
                                "internalName": "Form configuration 1",
                            },
                            "nl": {
                                "name": "Form configuratie 1",
                                "internalName": "Form configuratie 1",
                            },
                        },
                    },
                },
            ],
            "variables": [
                {
                    "name": "profile-prefill",
                    "key": "profilePrefill",
                    "formDefinition": None,
                    "source": FormVariableSources.user_defined,
                    "prefillPlugin": COMMUNICATION_PREFERENCES_PLUGIN_IDENTIFIER,
                    "prefillAttribute": "demo",
                    "prefillIdentifierRole": "main",
                    "dataType": FormVariableDataTypes.string,
                    "prefillOptions": {
                        "customerInteractionsApiGroup": customer_interactions_api.identifier,
                        "profileFormVariable": "profile",
                    },
                },
            ],
        }
        response = self.client.put(url, data=data)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Form.objects.count(), 0)
        self.assertEqual(len(response_data["invalidParams"]), 1)
        error_message = response_data["invalidParams"][0]
        self.assertEqual(error_message["code"], "invalid")
        self.assertEqual(error_message["name"], "variables.0")
        self.assertEqual(
            error_message["reason"],
            _(
                "Prefill plugin, attribute and options can not be specified at the same time."
            ),
        )

    def test_user_defined_missing_prefill_fields(self):
        customer_interactions_api = CustomerInteractionsAPIGroupConfigFactory.create()
        form_definition_uuid = uuid4()
        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": "559812e7-9bff-4142-ab41-0cc8cf4e5e32"},
        )

        with self.subTest("Missing required prefillOptions or prefillAttribute fields"):
            data = {
                "name": "Create form",
                "slug": "create-form",
                "steps": [
                    {
                        "slug": "step-1",
                        "formDefinition": {
                            "uuid": form_definition_uuid,
                            "configuration": {
                                "components": [
                                    {
                                        "type": "customerProfile",
                                        "key": "profile",
                                        "label": "Profile",
                                        "digitalAddressTypes": ["email"],
                                        "shouldUpdateCustomerData": True,
                                    }
                                ],
                            },
                            "translations": {
                                "en": {
                                    "name": "Form configuration 1",
                                    "internalName": "Form configuration 1",
                                },
                                "nl": {
                                    "name": "Form configuratie 1",
                                    "internalName": "Form configuratie 1",
                                },
                            },
                        },
                    },
                ],
                # Note the missing prefillAttribute or prefillOptions fields.
                "variables": [
                    {
                        "name": "profile-prefill",
                        "key": "profilePrefill",
                        "formDefinition": None,
                        "source": FormVariableSources.user_defined,
                        "prefillPlugin": COMMUNICATION_PREFERENCES_PLUGIN_IDENTIFIER,
                        "prefillIdentifierRole": "main",
                        "dataType": FormVariableDataTypes.string,
                    },
                ],
            }
            response = self.client.put(url, data=data)
            response_data = response.json()

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(Form.objects.count(), 0)
            self.assertEqual(len(response_data["invalidParams"]), 1)
            error_message = response_data["invalidParams"][0]
            self.assertEqual(error_message["code"], "invalid")
            self.assertEqual(error_message["name"], "variables.0")
            self.assertEqual(
                error_message["reason"],
                _(
                    "Prefill plugin must be specified with either prefill attribute or prefill options."
                ),
            )

        with self.subTest("Missing required prefillPlugin field"):
            data = {
                "name": "Create form",
                "slug": "create-form",
                "steps": [
                    {
                        "slug": "step-1",
                        "formDefinition": {
                            "uuid": form_definition_uuid,
                            "configuration": {
                                "components": [
                                    {
                                        "type": "customerProfile",
                                        "key": "profile",
                                        "label": "Profile",
                                        "digitalAddressTypes": ["email"],
                                        "shouldUpdateCustomerData": True,
                                    }
                                ],
                            },
                            "translations": {
                                "en": {
                                    "name": "Form configuration 1",
                                    "internalName": "Form configuration 1",
                                },
                                "nl": {
                                    "name": "Form configuratie 1",
                                    "internalName": "Form configuratie 1",
                                },
                            },
                        },
                    },
                ],
                # Note the missing prefillPlugin field.
                "variables": [
                    {
                        "name": "profile-prefill",
                        "key": "profilePrefill",
                        "formDefinition": None,
                        "source": FormVariableSources.user_defined,
                        "prefillAttribute": "",
                        "prefillIdentifierRole": "main",
                        "prefillOptions": {
                            "customerInteractionsApiGroup": customer_interactions_api.identifier,
                            "profileFormVariable": "profile",
                        },
                        "dataType": FormVariableDataTypes.string,
                    },
                ],
            }
            response = self.client.put(url, data=data)
            response_data = response.json()

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(Form.objects.count(), 0)
            self.assertEqual(len(response_data["invalidParams"]), 1)
            error_message = response_data["invalidParams"][0]
            self.assertEqual(error_message["code"], "invalid")
            self.assertEqual(error_message["name"], "variables.0")
            self.assertEqual(
                error_message["reason"],
                _(
                    "Prefill plugin must be specified with either prefill attribute or prefill options."
                ),
            )

    def test_user_defined_profile_form_variable_incorrect_component_type(self):
        customer_interactions_api = CustomerInteractionsAPIGroupConfigFactory.create()
        form_definition_uuid = uuid4()
        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": "559812e7-9bff-4142-ab41-0cc8cf4e5e32"},
        )
        data = {
            "name": "Create form",
            "slug": "create-form",
            "steps": [
                {
                    "slug": "step-1",
                    "formDefinition": {
                        "uuid": form_definition_uuid,
                        "configuration": {
                            "components": [
                                {
                                    "type": "customerProfile",
                                    "key": "profile",
                                    "label": "Profile",
                                    "digitalAddressTypes": ["email"],
                                    "shouldUpdateCustomerData": True,
                                },
                                {
                                    "type": "textfield",
                                    "key": "textfield",
                                    "name": "Text field",
                                },
                            ],
                        },
                        "translations": {
                            "en": {
                                "name": "Form configuration 1",
                                "internalName": "Form configuration 1",
                            },
                            "nl": {
                                "name": "Form configuratie 1",
                                "internalName": "Form configuratie 1",
                            },
                        },
                    },
                },
            ],
            "variables": [
                {
                    "name": "profile-prefill",
                    "key": "profilePrefill",
                    "formDefinition": None,
                    "source": FormVariableSources.user_defined,
                    "prefillPlugin": COMMUNICATION_PREFERENCES_PLUGIN_IDENTIFIER,
                    "prefillAttribute": "",
                    "prefillIdentifierRole": "main",
                    "prefillOptions": {
                        "customerInteractionsApiGroup": customer_interactions_api.identifier,
                        "profileFormVariable": "textfield",
                    },
                    "dataType": FormVariableDataTypes.string,
                },
            ],
        }
        response = self.client.put(url, data=data)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Form.objects.count(), 0)
        self.assertEqual(len(response_data["invalidParams"]), 1)
        error_message = response_data["invalidParams"][0]
        self.assertEqual(error_message["code"], "invalid")
        self.assertEqual(error_message["name"], "variables.0")
        self.assertEqual(
            error_message["reason"],
            _(
                "Only variables of 'profile' components are allowed as "
                "profile form variable."
            ),
        )

    def test_multiple_profile_variables_same_component(self):
        customer_interactions_api = CustomerInteractionsAPIGroupConfigFactory.create()
        form_definition_uuid = uuid4()
        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": "559812e7-9bff-4142-ab41-0cc8cf4e5e32"},
        )
        data = {
            "name": "Update form",
            "slug": "update-form",
            "steps": [
                {
                    "slug": "step-1",
                    "formDefinition": {
                        "uuid": form_definition_uuid,
                        "isReusable": False,
                        "loginRequired": False,
                        "configuration": {
                            "components": [
                                {
                                    "type": "customerProfile",
                                    "key": "profile",
                                    "label": "Profile",
                                    "digitalAddressTypes": ["email"],
                                    "shouldUpdateCustomerData": True,
                                }
                            ],
                        },
                        "translations": {
                            "en": {
                                "name": "Form configuration 1",
                                "internalName": "Form configuration 1",
                            },
                            "nl": {
                                "name": "Form configuratie 1",
                                "internalName": "Form configuratie 1",
                            },
                        },
                    },
                },
            ],
            "variables": [
                {
                    "name": "profile-prefill",
                    "key": "profilePrefill",
                    "formDefinition": None,
                    "source": FormVariableSources.user_defined,
                    "prefillPlugin": COMMUNICATION_PREFERENCES_PLUGIN_IDENTIFIER,
                    "prefillAttribute": "",
                    "prefillIdentifierRole": "main",
                    "prefillOptions": {
                        "customerInteractionsApiGroup": customer_interactions_api.identifier,
                        "profileFormVariable": "profile",
                    },
                    "dataType": FormVariableDataTypes.string,
                },
                {
                    "name": "profile-prefill",
                    "key": "profilePrefill2",
                    "formDefinition": None,
                    "source": FormVariableSources.user_defined,
                    "prefillPlugin": COMMUNICATION_PREFERENCES_PLUGIN_IDENTIFIER,
                    "prefillAttribute": "",
                    "prefillIdentifierRole": "main",
                    "prefillOptions": {
                        "customerInteractionsApiGroup": customer_interactions_api.identifier,
                        "profileFormVariable": "profile",
                    },
                    "dataType": FormVariableDataTypes.string,
                },
            ],
        }
        response = self.client.put(url, data=data)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Form.objects.count(), 0)
        self.assertEqual(len(response_data["invalidParams"]), 1)
        error_message = response_data["invalidParams"][0]
        self.assertEqual(error_message["code"], "unique")
        self.assertEqual(error_message["name"], "variables.1")
        self.assertEqual(
            error_message["reason"],
            _(
                "This profile form variable is already used in another "
                "communication preferences prefill plugin."
            ),
        )

    def test_profile_form_variable_unknown_key(self):
        customer_interactions_api = CustomerInteractionsAPIGroupConfigFactory.create()
        form_definition_uuid = uuid4()
        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": "559812e7-9bff-4142-ab41-0cc8cf4e5e32"},
        )
        data = {
            "name": "Create form",
            "slug": "create-form",
            "steps": [
                {
                    "slug": "step-1",
                    "formDefinition": {
                        "uuid": form_definition_uuid,
                        "configuration": {
                            "components": [
                                {
                                    "type": "customerProfile",
                                    "key": "profile",
                                    "label": "Profile",
                                    "digitalAddressTypes": ["email"],
                                    "shouldUpdateCustomerData": True,
                                }
                            ],
                        },
                        "translations": {
                            "en": {
                                "name": "Form configuration 1",
                                "internalName": "Form configuration 1",
                            },
                            "nl": {
                                "name": "Form configuratie 1",
                                "internalName": "Form configuratie 1",
                            },
                        },
                    },
                },
            ],
            "variables": [
                {
                    "name": "profile-prefill",
                    "key": "profilePrefill",
                    "formDefinition": None,
                    "source": FormVariableSources.user_defined,
                    "prefillPlugin": COMMUNICATION_PREFERENCES_PLUGIN_IDENTIFIER,
                    "prefillAttribute": "",
                    "prefillIdentifierRole": "main",
                    "prefillOptions": {
                        "customerInteractionsApiGroup": customer_interactions_api.identifier,
                        "profileFormVariable": "foobar",
                    },
                    "dataType": FormVariableDataTypes.string,
                },
            ],
        }
        response = self.client.put(url, data=data)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Form.objects.count(), 0)
        self.assertEqual(len(response_data["invalidParams"]), 1)
        error_message = response_data["invalidParams"][0]
        self.assertEqual(error_message["code"], "invalid")
        self.assertEqual(error_message["name"], "variables.0")
        self.assertEqual(
            error_message["reason"],
            "Unknown component key 'foobar' specified for profile form variable",
        )


@override_settings(LANGUAGE_CODE="en")
class FormEndpointLogicRulesTests(APITestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        cls.admin_user = UserFactory.create(
            is_staff=True, user_permissions=("forms.change_form",)
        )

    def setUp(self) -> None:
        super().setUp()

        self.client.force_authenticate(user=self.admin_user)

    def test_create_form_with_logic_rules(self):
        form_definition_uuid = uuid4()
        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": "559812e7-9bff-4142-ab41-0cc8cf4e5e32"},
        )
        data = {
            "name": "Create form",
            "slug": "create-form",
            "steps": [
                {
                    "slug": "step-1",
                    "formDefinition": {
                        "uuid": form_definition_uuid,
                        "configuration": {
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "textField",
                                    "label": "TextField",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                                {
                                    "type": "checkbox",
                                    "key": "checkbox",
                                    "label": "Checkbox",
                                    "hidden": False,
                                    "clearOnHide": False,
                                },
                            ],
                        },
                        "translations": {
                            "en": {
                                "name": "Form configuration",
                                "internalName": "Form configuration",
                            },
                            "nl": {
                                "name": "Form configuratie",
                                "internalName": "Form configuratie",
                            },
                        },
                    },
                },
            ],
            "variables": [
                {
                    "name": "Extra_var",
                    "key": "extra_var",
                    "source": FormVariableSources.user_defined,
                    "formDefinition": None,
                    "dataType": FormVariableDataTypes.string,
                },
            ],
            "registrationBackends": [
                {
                    "name": "Email registration",
                    "key": "email-fu",
                    "backend": "email",
                    "options": {
                        "to_emails": ["foo@example.com"],
                    },
                }
            ],
            "logic_rules": [
                {
                    "order": 0,
                    "jsonLogicTrigger": {"==": [{"var": "checkbox"}, True]},
                    "actions": [
                        {
                            "component": "textField",
                            "action": {
                                "type": "property",
                                "property": {"type": "bool", "value": "hidden"},
                                "value": "",
                                "state": True,
                            },
                        },
                        {
                            "action": {
                                "type": "set-registration-backend",
                                "value": "email-fu",
                            },
                        },
                    ],
                },
            ],
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Form.objects.count(), 1)
        form = Form.objects.get()

        self.assertEqual(form.formlogic_set.count(), 1)

    def test_update_form_with_logic_rules(self):
        form = FormFactory.create(generate_minimal_setup=True)
        form_definition = form.formstep_set.get().form_definition
        FormLogicFactory.create(form=form)

        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": form.uuid},
        )
        data = {
            "name": "Update form",
            "slug": "update-form",
            "steps": [
                {
                    "slug": "step-1",
                    "formDefinition": {
                        "uuid": form_definition.uuid,
                        "configuration": {
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "test-key",
                                    "label": "TextField",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                                {
                                    "type": "checkbox",
                                    "key": "checkbox",
                                    "label": "Checkbox",
                                    "hidden": False,
                                    "clearOnHide": False,
                                },
                            ],
                        },
                        "translations": {
                            "en": {
                                "name": "Form configuration",
                                "internalName": "Form configuration",
                            },
                            "nl": {
                                "name": "Form configuratie",
                                "internalName": "Form configuratie",
                            },
                        },
                    },
                },
            ],
            "logic_rules": [
                {
                    "order": 0,
                    "jsonLogicTrigger": {"==": [{"var": "checkbox"}, True]},
                    "actions": [
                        {
                            "component": "test-key",
                            "action": {
                                "type": "property",
                                "property": {"type": "bool", "value": "hidden"},
                                "value": "",
                                "state": True,
                            },
                        }
                    ],
                },
            ],
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Form.objects.count(), 1)
        form.refresh_from_db()

        logic_rule = FormLogic.objects.get()
        self.assertEqual(form.formlogic_set.get(), logic_rule)
        self.assertEqual(
            logic_rule.actions,
            [
                {
                    "action": {
                        "type": "property",
                        "state": True,
                        "property": {"type": "bool", "value": "hidden"},
                    },
                    "component": "test-key",
                }
            ],
        )

    def test_component_missing_from_action_and_present_in_form(self):
        form = FormFactory.create()
        form_step = FormStepFactory.create(form=form, slug="step-1")
        form_definition = form_step.form_definition
        FormLogicFactory.create(form=form)

        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": form.uuid},
        )
        data = {
            "name": "Update form",
            "slug": "update-form",
            "steps": [
                {
                    "slug": "step-1",
                    "formDefinition": {
                        "uuid": form_definition.uuid,
                        "configuration": {
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "textField",
                                    "label": "TextField",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                            ],
                        },
                    },
                },
            ],
            "logic_rules": [
                {
                    "order": 0,
                    "jsonLogicTrigger": False,
                    "is_advanced": True,
                    "actions": [
                        {
                            "formStepSlug": form_step.slug,
                            "action": {"type": "disable-next"},
                        }
                    ],
                },
                {
                    "order": 1,
                    "jsonLogicTrigger": True,
                    "is_advanced": True,
                    "actions": [
                        {
                            "component": "",
                            "action": {
                                "type": "property",
                                "property": {"type": "bool", "value": "hidden"},
                                "value": "",
                                "state": True,
                            },
                        }
                    ],
                },
            ],
        }
        response = self.client.put(url, data=data)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data["code"], "invalid")
        self.assertEqual(
            response_data["invalidParams"][0],
            {
                "name": "logicRules.1.actions.0.component",
                "code": "blank",
                "reason": "This field may not be blank.",
            },
        )

    def test_invalid_component_reference_is_caught_during_validation(self):
        url = reverse("api:v3:form-detail", kwargs={"uuid": uuid4()})
        data = {
            "name": "Create form",
            "slug": "create-form",
            "steps": [
                {
                    "slug": "step-1",
                    "formDefinition": {
                        "uuid": str(uuid4()),
                        "configuration": {
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "textField",
                                    "label": "TextField",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                            ],
                        },
                    },
                },
            ],
            "logic_rules": [
                {
                    "order": 0,
                    "jsonLogicTrigger": True,
                    "is_advanced": True,
                    "actions": [
                        {
                            "component": "badReference",
                            "action": {
                                "type": "property",
                                "property": {"type": "bool", "value": "hidden"},
                                "value": "",
                                "state": True,
                            },
                        }
                    ],
                },
            ],
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertEqual(response_data["code"], "invalid")
        self.assertEqual(
            response_data["invalidParams"][0],
            {
                "name": "logicRules.0.actions.0.component",
                "code": "invalid",
                "reason": "Could not find the component with key 'badReference'.",
            },
        )

    def test_variable_missing_from_action_and_present_in_form(self):
        form = FormFactory.create()
        form_step = FormStepFactory.create(form=form, slug="step-1")
        form_definition = form_step.form_definition
        FormLogicFactory.create(form=form)

        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": form.uuid},
        )
        data = {
            "name": "Update form",
            "slug": "update-form",
            "steps": [
                {
                    "slug": "step-1",
                    "formDefinition": {
                        "uuid": form_definition.uuid,
                        "configuration": {
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "textField",
                                    "label": "TextField",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                            ],
                        },
                    },
                },
            ],
            "logic_rules": [
                {
                    "order": 0,
                    "jsonLogicTrigger": True,
                    "is_advanced": True,
                    "actions": [
                        {
                            "action": {
                                "type": "variable",
                                "property": {"type": "", "value": ""},
                                "value": "foo",
                                "state": "",
                            },
                            "variable": "",
                        }
                    ],
                },
            ],
        }
        response = self.client.put(url, data=data)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data["code"], "invalid")
        self.assertEqual(
            response_data["invalidParams"][0],
            {
                "name": "logicRules.0.actions.0.variable",
                "code": "blank",
                "reason": "You must specify a variable.",
            },
        )

    def test_wrong_variable_provided_in_variable_action(self):
        form = FormFactory.create()
        form_step = FormStepFactory.create(form=form, slug="step-1")
        form_definition = form_step.form_definition
        FormLogicFactory.create(form=form)

        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": form.uuid},
        )
        data = {
            "name": "Update form",
            "slug": "update-form",
            "steps": [
                {
                    "slug": "step-1",
                    "formDefinition": {
                        "uuid": form_definition.uuid,
                        "configuration": {
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "textField",
                                    "label": "TextField",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                            ],
                        },
                    },
                },
            ],
            "logic_rules": [
                {
                    "order": 0,
                    "jsonLogicTrigger": True,
                    "is_advanced": True,
                    "actions": [
                        {
                            "action": {
                                "type": "variable",
                                "property": {"type": "", "value": ""},
                                "value": "foo",
                                "state": "",
                            },
                            "variable": "wrong",
                        }
                    ],
                },
            ],
        }
        response = self.client.put(url, data=data)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data["code"], "invalid")
        self.assertEqual(
            response_data["invalidParams"][0],
            {
                "name": "logicRules.0.actions.0.variable",
                "code": "invalid",
                "reason": "Could not find the variable with key 'wrong'.",
            },
        )

    def test_wrong_date_format_in_variable_action(self):
        form = FormFactory.create()
        form_step = FormStepFactory.create(form=form, slug="step-1")
        form_definition = form_step.form_definition
        FormLogicFactory.create(form=form)

        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": form.uuid},
        )
        data = {
            "name": "Update form",
            "slug": "update-form",
            "steps": [
                {
                    "slug": "step-1",
                    "formDefinition": {
                        "uuid": form_definition.uuid,
                        "configuration": {
                            "components": [
                                {
                                    "type": "date",
                                    "key": "date",
                                    "label": "Date",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                            ],
                        },
                    },
                },
            ],
            "logic_rules": [
                {
                    "order": 0,
                    "jsonLogicTrigger": True,
                    "is_advanced": True,
                    "actions": [
                        {
                            "action": {
                                "type": "variable",
                                "property": {"type": "", "value": ""},
                                "value": "foo",
                                "state": "",
                            },
                            "variable": "date",
                        }
                    ],
                },
            ],
        }
        response = self.client.put(url, data=data)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data["code"], "invalid")
        self.assertEqual(
            response_data["invalidParams"][0],
            {
                "name": "logicRules.0.actions.0.action.value",
                "code": "invalid",
                "reason": (
                    "The value for a date variable must be a string in the format "
                    "yyyy-mm-dd (e.g. 2023-07-03)"
                ),
            },
        )

    def test_layout_components_and_disabled(self):
        form = FormFactory.create()
        form_step = FormStepFactory.create(form=form, slug="step-1")
        form_definition = form_step.form_definition
        FormLogicFactory.create(form=form)

        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": form.uuid},
        )
        data = {
            "name": "Update form",
            "slug": "update-form",
            "steps": [
                {
                    "slug": "step-1",
                    "formDefinition": {
                        "uuid": form_definition.uuid,
                        "configuration": {
                            "components": [
                                {
                                    "type": "fieldset",
                                    "key": "fieldset",
                                    "label": "Fieldset",
                                },
                            ],
                        },
                    },
                },
            ],
            "logic_rules": [
                {
                    "order": 0,
                    "jsonLogicTrigger": True,
                    "is_advanced": True,
                    "actions": [
                        {
                            "component": "fieldset",
                            "action": {
                                "type": "property",
                                "property": {
                                    "type": "bool",
                                    "value": "disabled",
                                },
                                "value": "",
                                "state": True,
                            },
                        }
                    ],
                },
            ],
        }
        response = self.client.put(url, data=data)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data["code"], "invalid")
        self.assertEqual(
            response_data["invalidParams"][0],
            {
                "name": "logicRules.0.actions.0.component",
                "code": "invalid",
                "reason": "You cannot used the 'disabled' property on layout components'.",
            },
        )

    def test_missing_form_step_slug_from_action(self):
        form = FormFactory.create()
        form_step = FormStepFactory.create(form=form, slug="step-1")
        form_definition = form_step.form_definition
        FormLogicFactory.create(form=form)

        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": form.uuid},
        )
        data = {
            "name": "Update form",
            "slug": "update-form",
            "steps": [
                {
                    "slug": "step-1",
                    "formDefinition": {
                        "uuid": form_definition.uuid,
                        "configuration": {
                            "components": [
                                {
                                    "type": "fieldset",
                                    "key": "fieldset",
                                    "label": "Fieldset",
                                },
                            ],
                        },
                    },
                },
            ],
            "logic_rules": [
                {
                    "order": 0,
                    "jsonLogicTrigger": True,
                    "is_advanced": True,
                    "actions": [
                        {
                            "component": "",
                            "formStepSlug": None,
                            "action": {
                                "type": "disable-next",
                                "property": {"type": "", "value": ""},
                                "value": "",
                                "state": "",
                            },
                        },
                    ],
                },
            ],
        }
        response = self.client.put(url, data=data)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data["code"], "invalid")
        self.assertEqual(
            response_data["invalidParams"][0],
            {
                "name": "logicRules.0.actions.0.formStepSlug",
                "code": "null",
                "reason": "This field may not be null.",
            },
        )

    def test_invalid_form_step_slug_in_action(self):
        form = FormFactory.create()
        form_step = FormStepFactory.create(form=form, slug="step-1")
        form_definition = form_step.form_definition
        FormLogicFactory.create(form=form)

        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": form.uuid},
        )
        data = {
            "name": "Update form",
            "slug": "update-form",
            "steps": [
                {
                    "slug": "step-1",
                    "formDefinition": {
                        "uuid": form_definition.uuid,
                        "configuration": {
                            "components": [
                                {
                                    "type": "fieldset",
                                    "key": "fieldset",
                                    "label": "Fieldset",
                                },
                            ],
                        },
                    },
                },
            ],
            "logic_rules": [
                {
                    "order": 0,
                    "jsonLogicTrigger": True,
                    "is_advanced": True,
                    "actions": [
                        {
                            "component": "",
                            "formStepSlug": "wrong",
                            "action": {
                                "type": "disable-next",
                                "property": {"type": "", "value": ""},
                                "value": "",
                                "state": "",
                            },
                        },
                    ],
                },
            ],
        }
        response = self.client.put(url, data=data)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data["code"], "invalid")
        self.assertEqual(
            response_data["invalidParams"][0],
            {
                "name": "logicRules.0.actions.0.formStepSlug",
                "code": "invalid",
                "reason": "Could not find a step with the slug 'wrong'.",
            },
        )

    def test_logic_rules_with_cycles_detected(self):
        form = FormFactory.create(generate_minimal_setup=True)
        form_step = FormStepFactory.create(form=form, slug="step-1")
        form_definition = form_step.form_definition
        FormLogicFactory.create(form=form)

        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": form.uuid},
        )

        data = {
            "name": "Update form",
            "slug": "update-form",
            "steps": [
                {
                    "slug": "step-1",
                    "formDefinition": {
                        "uuid": form_definition.uuid,
                        "configuration": {
                            "components": [
                                {
                                    "key": "foo",
                                    "type": "textfield",
                                    "label": "Foo",
                                },
                                {
                                    "key": "bar",
                                    "type": "textfield",
                                    "label": "Bar",
                                },
                                {
                                    "key": "baz",
                                    "type": "textfield",
                                    "label": "Baz",
                                },
                                {
                                    "key": "self",
                                    "type": "textfield",
                                    "label": "Self",
                                },
                            ],
                        },
                    },
                },
            ],
            "logic_rules": [
                {
                    "jsonLogicTrigger": {"==": [{"var": "self"}, ""]},
                    "description": "Set self",
                    "order": 0,
                    "actions": [
                        {
                            "variable": "self",
                            "action": {"type": "variable", "value": "self"},
                        }
                    ],
                },
                {
                    "jsonLogicTrigger": {"==": [{"var": "foo"}, ""]},
                    "description": "Set bar",
                    "order": 1,
                    "actions": [
                        {
                            "variable": "bar",
                            "action": {"type": "variable", "value": "bar"},
                        }
                    ],
                },
                {
                    "jsonLogicTrigger": {"==": [{"var": "bar"}, ""]},
                    "description": "Set baz",
                    "order": 2,
                    "actions": [
                        {
                            "variable": "baz",
                            "action": {"type": "variable", "value": "baz"},
                        }
                    ],
                },
                {
                    "jsonLogicTrigger": {"==": [{"var": "baz"}, ""]},
                    "description": "Set foo",
                    "order": 3,
                    "actions": [
                        {
                            "variable": "foo",
                            "action": {"type": "variable", "value": "foo"},
                        }
                    ],
                },
            ],
        }

        response = self.client.put(url, data=data)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

        expected_error = [
            {
                "name": "0.jsonLogicTrigger",
                "code": "cycles-detected",
                "reason": _(
                    "Rule contains cycles through variable(s): {variables}."
                ).format(variables="self"),
            },
            {
                "name": "1.jsonLogicTrigger",
                "code": "cycles-detected",
                "reason": _(
                    "Rule contains cycles through variable(s): {variables}."
                ).format(variables="bar, baz, foo"),
            },
            {
                "name": "2.jsonLogicTrigger",
                "code": "cycles-detected",
                "reason": _(
                    "Rule contains cycles through variable(s): {variables}."
                ).format(variables="bar, baz, foo"),
            },
            {
                "name": "3.jsonLogicTrigger",
                "code": "cycles-detected",
                "reason": _(
                    "Rule contains cycles through variable(s): {variables}."
                ).format(variables="bar, baz, foo"),
            },
        ]
        self.assertEqual(response.json()["invalidParams"], expected_error)

    def test_validation_reports_multiple_errors(self):
        form = FormFactory.create()
        form_step = FormStepFactory.create(form=form, slug="step-1")
        form_definition = form_step.form_definition
        FormLogicFactory.create(form=form)

        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": form.uuid},
        )
        data = {
            "name": "Update form",
            "slug": "update-form",
            "steps": [
                {
                    "slug": "step-1",
                    "formDefinition": {
                        "uuid": form_definition.uuid,
                        "configuration": {
                            "components": [
                                {
                                    "type": "fieldset",
                                    "key": "fieldset",
                                    "label": "Fieldset",
                                },
                            ],
                        },
                    },
                },
            ],
            "logic_rules": [
                {
                    "order": 0,
                    "jsonLogicTrigger": True,
                    "is_advanced": True,
                    "actions": [
                        {
                            "component": "",
                            "formStepSlug": "",
                            "action": {
                                "type": "disable-next",
                                "property": {"type": "", "value": ""},
                                "value": "",
                                "state": "",
                            },
                        },
                        {
                            "variable": "",
                            "action": {
                                "type": "variable",
                                "value": 42,
                            },
                        },
                    ],
                },
            ],
        }
        response = self.client.put(url, data=data)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data["code"], "invalid")
        self.assertEqual(
            response_data["invalidParams"][0],
            {
                "name": "logicRules.0.actions.0.formStepSlug",
                "code": "blank",
                "reason": "This field may not be blank.",
            },
        )
        self.assertEqual(
            response_data["invalidParams"][1],
            {
                "name": "logicRules.0.actions.1.variable",
                "code": "blank",
                "reason": "You must specify a variable.",
            },
        )


class FormEndpointAccessTests(APITestCase):
    def test_non_staff_user(self):
        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": "559812e7-9bff-4142-ab41-0cc8cf4e5e32"},
        )
        data = {
            "name": "Create form",
            "slug": "create-form",
            "steps": [],
        }

        non_staff_user = UserFactory.create(is_staff=False, user_permissions=tuple())
        self.client.force_login(non_staff_user)
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Form.objects.count(), 0)

    def test_staff_missing_permission(self):
        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": "559812e7-9bff-4142-ab41-0cc8cf4e5e32"},
        )
        data = {
            "name": "Create form",
            "slug": "create-form",
            "steps": [],
        }

        non_staff_user = UserFactory.create(is_staff=True, user_permissions=tuple())
        self.client.force_login(non_staff_user)
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Form.objects.count(), 0)

    def test_anonymous_user(self):
        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": "559812e7-9bff-4142-ab41-0cc8cf4e5e32"},
        )
        data = {
            "name": "Create form",
            "slug": "create-form",
            "steps": [],
        }

        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Form.objects.count(), 0)


def create_or_update_form(
    user: User, form_uuid: UUID, form_data: JSONObject
) -> Response:
    url = reverse(
        "api:v3:form-detail",
        kwargs={"uuid": str(form_uuid)},
    )
    client = APIClient(raise_request_exception=False)
    client.force_authenticate(user=user)
    return client.put(url, data=form_data)  # pyright: ignore[reportReturnType]


def close_db_connections(future: Future) -> None:
    connections.close_all()


class FormEndpointConcurrentTests(APITransactionTestCase):
    def test_create_form_with_definitions_with_update(self):
        """
        Test that updating the same form definition, by creating two forms
        concurrently, is not possible.
        """
        form_definition = FormDefinitionFactory(is_reusable=True)

        user_1 = UserFactory.create(
            is_staff=True, user_permissions=("forms.change_form",)
        )
        user_2 = UserFactory.create(
            is_staff=True, user_permissions=("forms.change_form",)
        )

        test_data = (
            (
                user_1,
                uuid4(),
                {
                    "name": "Create form",
                    "slug": "create-form-1",
                    "steps": [
                        {
                            "slug": "step-1",
                            "formDefinition": {
                                "uuid": str(form_definition.uuid),
                                "isReusable": True,
                                "loginRequired": True,
                                "configuration": {
                                    "components": [
                                        {
                                            "type": "textfield",
                                            "key": "component1",
                                            "label": "component1",
                                            "hidden": False,
                                            "clearOnHide": True,
                                        },
                                    ],
                                },
                                "translations": {
                                    "en": {
                                        "name": "Form configuration 1",
                                        "internalName": "Form configuration 1",
                                    },
                                    "nl": {
                                        "name": "Form configuratie 1",
                                        "internalName": "Form configuratie 1",
                                    },
                                },
                            },
                        }
                    ],
                },
            ),
            (
                user_2,
                uuid4(),
                {
                    "name": "Create form",
                    "slug": "create-form-2",
                    "steps": [
                        {
                            "slug": "step-1",
                            "formDefinition": {
                                "uuid": str(form_definition.uuid),
                                "isReusable": True,
                                "loginRequired": True,
                                "configuration": {
                                    "components": [
                                        {
                                            "type": "textfield",
                                            "key": "component2",
                                            "label": "component2",
                                            "hidden": False,
                                            "clearOnHide": True,
                                        },
                                    ],
                                },
                                "translations": {
                                    "en": {
                                        "name": "Form configuration 1",
                                        "internalName": "Form configuration 1",
                                    },
                                    "nl": {
                                        "name": "Form configuratie 1",
                                        "internalName": "Form configuratie 1",
                                    },
                                },
                            },
                        }
                    ],
                },
            ),
        )

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = []
            for user, form_uuid, form_data in test_data:
                future = executor.submit(
                    create_or_update_form, user, form_uuid, form_data
                )
                future.add_done_callback(close_db_connections)
                futures.append(future)

            responses = [future.result() for future in as_completed(futures)]

        error_responses = [
            response
            for response in responses
            if response.status_code == status.HTTP_409_CONFLICT
        ]
        success_responses = [
            response
            for response in responses
            if response.status_code == status.HTTP_201_CREATED
        ]
        self.assertEqual(len(error_responses), 1)
        self.assertEqual(len(success_responses), 1)
        response_data = success_responses[0].json()
        expected_form_definition = response_data["steps"][0]["formDefinition"][
            "configuration"
        ]

        form = Form.objects.get()

        # form step
        form_step = form.formstep_set.get()
        self.assertEqual(form_step.order, 0)
        self.assertEqual(form_step.slug, "step-1")

        # step form definition
        step_form_definition = form_step.form_definition
        self.assertEqual(step_form_definition.uuid, form_definition.uuid)
        self.assertTrue(step_form_definition.login_required)
        self.assertEqual(step_form_definition.configuration, expected_form_definition)

    def test_update_form_definitions(self):
        """
        Test that updating the same form definition, by updating two forms
        concurrently, is not possible.
        """
        form_definition = FormDefinitionFactory(
            configuration={"components": [{"key": "textfield", "type": "textfield"}]},
            is_reusable=True,
            uuid=uuid4(),
        )
        form_1 = FormFactory(formstep__form_definition=form_definition)
        form_2 = FormFactory(formstep__form_definition=form_definition)
        user_1 = UserFactory.create(
            is_staff=True, user_permissions=("forms.change_form",)
        )
        user_2 = UserFactory.create(
            is_staff=True, user_permissions=("forms.change_form",)
        )

        test_data = (
            (
                user_1,
                form_1.uuid,
                {
                    "name": "Update form",
                    "slug": "update-form-1",
                    "steps": [
                        {
                            "slug": "step-1",
                            "formDefinition": {
                                "uuid": str(form_definition.uuid),
                                "isReusable": True,
                                "loginRequired": True,
                                "configuration": {
                                    "components": [
                                        {
                                            "type": "textfield",
                                            "key": "component1",
                                            "label": "component1",
                                            "hidden": False,
                                            "clearOnHide": True,
                                        },
                                    ],
                                },
                                "translations": {
                                    "en": {
                                        "name": "Form configuration 1",
                                        "internalName": "Form configuration 1",
                                    },
                                    "nl": {
                                        "name": "Form configuratie 1",
                                        "internalName": "Form configuratie 1",
                                    },
                                },
                            },
                        }
                    ],
                },
            ),
            (
                user_2,
                form_2.uuid,
                {
                    "name": "Update form",
                    "slug": "update-form-2",
                    "steps": [
                        {
                            "slug": "step-1",
                            "formDefinition": {
                                "uuid": str(form_definition.uuid),
                                "isReusable": True,
                                "loginRequired": True,
                                "configuration": {
                                    "components": [
                                        {
                                            "type": "textfield",
                                            "key": "component2",
                                            "label": "component2",
                                            "hidden": False,
                                            "clearOnHide": True,
                                        },
                                    ],
                                },
                                "translations": {
                                    "en": {
                                        "name": "Form configuration 1",
                                        "internalName": "Form configuration 1",
                                    },
                                    "nl": {
                                        "name": "Form configuratie 1",
                                        "internalName": "Form configuratie 1",
                                    },
                                },
                            },
                        }
                    ],
                },
            ),
        )

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = []
            for user, form_uuid, form_data in test_data:
                future = executor.submit(
                    create_or_update_form, user, form_uuid, form_data
                )
                future.add_done_callback(close_db_connections)
                futures.append(future)

            responses = [future.result() for future in as_completed(futures)]

        error_responses = [
            response
            for response in responses
            if response.status_code == status.HTTP_409_CONFLICT
        ]
        success_responses = [
            response
            for response in responses
            if response.status_code == status.HTTP_200_OK
        ]
        self.assertEqual(len(error_responses), 1)
        self.assertEqual(len(success_responses), 1)
        response_data = success_responses[0].json()
        expected_form_definition = response_data["steps"][0]["formDefinition"][
            "configuration"
        ]

        self.assertEqual(Form.objects.count(), 2)
        updated_form = next(
            (
                form
                for form in (form_1, form_2)
                if response_data["uuid"] == str(form.uuid)
            ),
            None,
        )
        assert updated_form, "Unknown form was updated"
        updated_form.refresh_from_db()

        # form step
        form_step = updated_form.formstep_set.get()
        self.assertEqual(form_step.order, 0)
        self.assertEqual(form_step.slug, "step-1")

        # step form definition
        self.assertEqual(form_step.form_definition, form_definition)
        self.assertEqual(
            form_step.form_definition.configuration, expected_form_definition
        )
        self.assertEqual(FormDefinition.objects.count(), 1)
