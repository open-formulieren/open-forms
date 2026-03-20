from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from datetime import timedelta
from uuid import UUID, uuid4

from django.db.models.base import connections
from django.urls import reverse
from django.utils import timezone
from django.utils.text import get_text_list
from django.utils.translation import gettext as _

from djangorestframework_camel_case.util import underscoreize
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient, APITestCase, APITransactionTestCase

from openforms.accounts.models import User
from openforms.accounts.tests.factories import UserFactory
from openforms.config.tests.factories import ThemeFactory
from openforms.data_removal.constants import RemovalMethods
from openforms.payments.contrib.worldline.tests.factories import (
    WorldlineMerchantFactory,
)
from openforms.products.tests.factories import ProductFactory
from openforms.typing import JSONObject
from openforms.utils.tests.feature_flags import enable_feature_flag

from ...constants import (
    FormTypeChoices,
    StatementCheckboxChoices,
    SubmissionAllowedChoices,
)
from ...models import Form, FormDefinition, FormRegistrationBackend
from ...tests.factories import (
    CategoryFactory,
    FormDefinitionFactory,
    FormFactory,
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
                        "uuid": str(uuid4()),
                        "configuration": {
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "component1",
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
            "appointmentOptions": {
                "isAppointment": False,
            },
            "literals": {
                "beginText": {"value": "Different Begin Text"},
                "previousText": {"value": "Different Previous Text"},
                "changeText": {"value": "Different Change Text"},
                "confirmText": {"value": "Different Confirm Text"},
            },
            "product": product.uuid,
            "slug": "create-form",
            "type": FormTypeChoices.appointment,
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
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                                {
                                    "type": "textfield",
                                    "key": "component2",
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
                },
            },
            "newRendererEnabled": True,
            "newLogicEvaluationEnabled": True,
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Form.objects.count(), 1)
        form = Form.objects.get()

        self.assertEqual(form.name_en, "Create form")
        self.assertEqual(form.name_nl, "Create formulier")
        self.assertEqual(form.internal_name, "Create form internal")
        self.assertEqual(form.internal_remarks, "This form is used for xyz")
        self.assertTrue(form.login_required)
        self.assertTrue(form.translation_enabled)

        self.assertEqual(form.type, FormTypeChoices.appointment)
        self.assertEqual(form.slug, "create-form")

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
                        "hidden": False,
                        "clear_on_hide": True,
                    },
                    {
                        "type": "textfield",
                        "key": "component2",
                        "hidden": False,
                        "clear_on_hide": True,
                    },
                ],
            },
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

        self.assertTrue(form.new_renderer_enabled)

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
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                                {
                                    "type": "textfield",
                                    "key": "component2",
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
                        "hidden": False,
                        "clear_on_hide": True,
                    },
                    {
                        "type": "textfield",
                        "key": "component2",
                        "hidden": False,
                        "clear_on_hide": True,
                    },
                ],
            },
        )
        self.assertEqual(FormDefinition.objects.count(), 1)

    def test_update_clears_existing_registration_backends(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            registration_backend="camunda",
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
            "literals": "foobar",
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Form.objects.count(), 0)
        response_data = response.json()
        assert "invalidParams" in response_data
        self.assertEqual(len(response_data["invalidParams"]), 1)
        self.assertEqual(response_data["invalidParams"][0]["code"], "invalid")
        self.assertEqual(
            response_data["invalidParams"][0]["name"], "literals.nonFieldErrors"
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

    def test_create_regular_form_requires_one_step(self):
        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": "559812e7-9bff-4142-ab41-0cc8cf4e5e32"},
        )
        data = {
            "name": "Create form",
            "slug": "create-form",
            "appointmentOptions": {
                "isAppointment": False,
            },
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
        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": "559812e7-9bff-4142-ab41-0cc8cf4e5e32"},
        )
        data = {
            "name": "Create form",
            "slug": "create-form",
            "appointmentOptions": {
                "isAppointment": True,
            },
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
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                                {
                                    "type": "textfield",
                                    "key": "component3",
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
                        "hidden": False,
                        "clear_on_hide": True,
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
                        "hidden": False,
                        "clear_on_hide": True,
                    },
                    {
                        "type": "textfield",
                        "key": "component3",
                        "hidden": False,
                        "clear_on_hide": True,
                    },
                ],
            },
        )

    def test_update_reuse_existing_form_definition(self):
        # Generate an unrelated form with an existing form definition which will be reused
        existing_form_definition_uuid = uuid4()
        unrelated_form_step = FormStepFactory.create(
            form_definition__configuration={
                "components": [{"key": "textfield", "type": "textfield"}]
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
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                                {
                                    "type": "textfield",
                                    "key": "component2",
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
                        "hidden": False,
                        "clear_on_hide": True,
                    },
                    {
                        "type": "textfield",
                        "key": "component2",
                        "hidden": False,
                        "clear_on_hide": True,
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
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                                {
                                    "type": "textfield",
                                    "key": "component2",
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
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                                {
                                    "type": "textfield",
                                    "key": "component2",
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
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                                {
                                    "type": "textfield",
                                    "key": "component2",
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
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                                {
                                    "type": "textfield",
                                    "key": "component2",
                                    "hidden": False,
                                    "clearOnHide": True,
                                },
                                {
                                    "type": "textfield",
                                    "key": "component1",
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
                                    "components": [
                                        {
                                            "type": "file",
                                            "key": "fileInRepeatingGroup1",
                                        },
                                        {
                                            "type": "file",
                                            "key": "fileInRepeatingGroup1",
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
            "literals": "foobar",
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        assert "invalidParams" in response_data
        self.assertEqual(len(response_data["invalidParams"]), 1)
        self.assertEqual(response_data["invalidParams"][0]["code"], "invalid")
        self.assertEqual(
            response_data["invalidParams"][0]["name"], "literals.nonFieldErrors"
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
        response_data = underscoreize(success_responses[0].json())
        expected_form_definition = response_data["steps"][0]["form_definition"][  # pyright: ignore[reportArgumentType,reportCallIssue,reportIndexIssue]
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
        response_data = underscoreize(success_responses[0].json())
        expected_form_definition = response_data["steps"][0]["form_definition"][  # pyright: ignore[reportArgumentType,reportCallIssue,reportIndexIssue]
            "configuration"
        ]

        self.assertEqual(Form.objects.count(), 2)
        updated_form = next(
            (
                form
                for form in (form_1, form_2)
                if response_data["uuid"] == str(form.uuid)  # pyright: ignore[reportArgumentType,reportCallIssue,reportIndexIssue]
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
        self.assertEqual(FormDefinition.objects.count(), 1)  # pyright: ignore[reportAttributeAccessIssue]
