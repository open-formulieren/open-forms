from unittest.mock import patch

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import (
    StaffUserFactory,
    SuperUserFactory,
    UserFactory,
)
from openforms.prefill.models import PrefillConfig
from openforms.translations.tests.utils import make_translated

from ..models import FormDefinition
from .factories import FormDefinitionFactory, FormStepFactory


class FormDefinitionsAPITests(APITestCase):
    def test_list_anon(self):
        FormDefinitionFactory.create_batch(2)

        url = reverse("api:formdefinition-list")
        response = self.client.get(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list(self):
        user = UserFactory.create()
        self.client.force_authenticate(user=user)

        FormDefinitionFactory.create_batch(2)

        url = reverse("api:formdefinition-list")
        response = self.client.get(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_without_permission_cant_update(self):
        user = UserFactory.create()
        self.client.force_authenticate(user=user)

        definition = FormDefinitionFactory.create(
            name="test form definition",
            slug="test-form-definition",
            configuration={
                "display": "form",
                "components": [{"label": "Existing field"}],
            },
        )

        url = reverse("api:formdefinition-detail", kwargs={"uuid": definition.uuid})
        data = {
            "name": "Updated name",
            "slug": "updated-slug",
            "configuration": {
                "display": "form",
                "components": [{"label": "Existing field"}, {"label": "New field"}],
            },
        }
        with self.subTest("user"):
            response = self.client.patch(url, data=data)
            self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        with self.subTest("staff"):
            user.is_staff = True
            user.save()
            response = self.client.patch(url, data=data)
            self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        with self.subTest("permissions"):
            user.is_staff = True
            user.save()
            response = self.client.patch(url, data=data)
            self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_user_without_permission_cant_create(self):
        user = UserFactory.create()
        self.client.force_authenticate(user=user)
        url = reverse("api:formdefinition-list")
        data = {
            "name": "Name",
            "slug": "a-slug",
            "configuration": {
                "display": "form",
                "components": [{"label": "New field"}],
            },
        }
        with self.subTest("user"):
            response = self.client.post(url, data=data)
            self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        with self.subTest("staff"):
            user.is_staff = True
            user.save()
            response = self.client.post(url, data=data)
            self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_user_without_permission_cant_delete(self):
        user = UserFactory.create()
        self.client.force_authenticate(user=user)
        definition = FormDefinitionFactory.create(
            name="test form definition",
            slug="test-form-definition",
            configuration={
                "display": "form",
                "components": [{"label": "Existing field"}],
            },
        )
        url = reverse("api:formdefinition-detail", kwargs={"uuid": definition.uuid})

        with self.subTest("user"):
            response = self.client.delete(url)
            self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        with self.subTest("staff"):
            user.is_staff = True
            user.save()
            response = self.client.delete(url)
            self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_update(self):
        user = StaffUserFactory.create(user_permissions=["change_form"])
        self.client.force_authenticate(user=user)

        definition = FormDefinitionFactory.create(
            name="test form definition",
            slug="test-form-definition",
            login_required=False,
            configuration={
                "display": "form",
                "components": [
                    {"key": "somekey", "type": "textfield", "label": "Existing field"}
                ],
            },
        )

        url = reverse("api:formdefinition-detail", kwargs={"uuid": definition.uuid})
        response = self.client.patch(
            url,
            data={
                "name": "Updated name",
                "slug": "updated-slug",
                "configuration": {
                    "display": "form",
                    "components": [
                        {
                            "key": "somekey",
                            "type": "textfield",
                            "label": "Existing field",
                        },
                        {"key": "somekey2", "type": "textfield", "label": "New field"},
                    ],
                },
                "login_required": True,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        definition.refresh_from_db()

        self.assertEqual("Updated name", definition.name)
        self.assertEqual("updated-slug", definition.slug)
        self.assertEqual(True, definition.login_required)
        self.assertIn(
            {"key": "somekey2", "type": "textfield", "label": "New field"},
            definition.configuration["components"],
        )

    def test_update_is_reusable_unsuccessful_with_multiple_forms(self):
        user = SuperUserFactory.create()
        self.client.force_authenticate(user=user)

        step = FormStepFactory.create(form_definition__is_reusable=True)
        FormStepFactory.create(form_definition=step.form_definition)

        url = reverse(
            "api:formdefinition-detail", kwargs={"uuid": step.form_definition.uuid}
        )
        response = self.client.patch(
            url,
            data={
                "isReusable": False,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["invalidParams"][0]["reason"],
            _(
                "This form definition cannot be marked as 'not-reusable' as it is used "
                "in multiple existing forms."
            ),
        )

    def test_create(self):
        user = StaffUserFactory.create(user_permissions=["change_form"])
        self.client.force_authenticate(user=user)

        url = reverse("api:formdefinition-list")
        response = self.client.post(
            url,
            data={
                "name": "Name",
                "slug": "a-slug",
                "configuration": {
                    "display": "form",
                    "components": [
                        {
                            "label": "New field",
                            "key": "newField",
                            "type": "textfield",
                        }
                    ],
                },
            },
        )

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        definition = FormDefinition.objects.get()

        self.assertEqual("Name", definition.name)
        self.assertEqual("a-slug", definition.slug)
        self.assertEqual(
            [
                {
                    "label": "New field",
                    "key": "newField",
                    "type": "textfield",
                }
            ],
            definition.configuration["components"],
        )

    def test_create_no_camelcase_snakecase_conversion(self):
        user = StaffUserFactory.create(user_permissions=["change_form"])
        self.client.force_authenticate(user=user)

        url = reverse("api:formdefinition-list")
        response = self.client.post(
            url,
            data={
                "name": "Name",
                "slug": "a-slug",
                "configuration": {
                    "someCamelCase": "field",
                    "key": "somekey",
                    "type": "textfield",
                },
            },
        )

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        config = FormDefinition.objects.get().configuration
        self.assertIn("someCamelCase", config)
        self.assertNotIn("some_amel_case", config)

    def test_get_no_snakecase_camelcase_conversion(self):
        user = StaffUserFactory.create(user_permissions=["change_form"])
        self.client.force_authenticate(user=user)

        definition = FormDefinitionFactory.create(
            name="test form definition",
            slug="test-form-definition",
            configuration={
                "display": "form",
                "components": [
                    {
                        "key": "somekey",
                        "type": "textfield",
                        "widget": {"time_24hr": True},
                    }
                ],
            },
        )

        url = reverse("api:formdefinition-detail", kwargs={"uuid": definition.uuid})
        response = self.client.get(url)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        date_component = response.json()["configuration"]["components"][0]

        self.assertIn("time_24hr", date_component["widget"])

    def test_delete(self):
        user = StaffUserFactory.create(user_permissions=["change_form"])
        self.client.force_authenticate(user=user)

        definition = FormDefinitionFactory.create(
            name="test form definition",
            slug="test-form-definition",
            configuration={
                "display": "form",
                "components": [{"label": "Existing field"}],
            },
        )

        url = reverse("api:formdefinition-detail", kwargs={"uuid": definition.uuid})
        response = self.client.delete(url)

        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)

        self.assertEqual(0, FormDefinition.objects.all().count())

    def test_used_in_forms_serializer_field(self):
        user = UserFactory.create()
        self.client.force_authenticate(user=user)
        form_step = FormStepFactory.create()
        url = reverse(
            "api:formdefinition-detail", args=(form_step.form_definition.uuid,)
        )
        form_url = reverse("api:form-detail", args=(form_step.form.uuid,))

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(len(response_data["usedIn"]), 1)
        self.assertEqual(
            response_data["usedIn"][0]["url"], f"http://testserver{form_url}"
        )

    def test_template_expressions_in_configuration_validation(self):
        """
        Assert that the supported formio component properties templates are validated.

        The API endpoint must validate templates that lead to syntax errors.
        """
        user = StaffUserFactory.create(user_permissions=["change_form"])
        self.client.force_authenticate(user=user)

        url = reverse("api:formdefinition-list")

        counter = 0

        def _do_create(components: list):
            nonlocal counter
            counter += 1
            return self.client.post(
                url,
                data={
                    "name": "Name",
                    "slug": f"fd-{counter}",
                    "configuration": {
                        "display": "form",
                        "components": components,
                    },
                },
            )

        with self.subTest("valid templates"):
            response = _do_create(
                [
                    {
                        "type": "textfield",
                        "key": "text1",
                        "description": "Simple {{ missingVariable }} print",
                        "placeholder": 'Placeholder with date filter {{ now|date:"d-m-Y" }}',
                    },
                    {
                        "label": "Field 1 value: {{ text1|default:'-' }}",
                        "type": "fieldset",
                        "key": "fieldset1",
                        "components": [
                            {
                                "type": "textfield",
                                "key": "text2",
                                "label": '{% now "jS F Y H:i" %}',
                            },
                            {
                                "type": "content",
                                "key": "content",
                                "html": "<p>{{ missingVariable }} hello</p>",
                                # syntax errors in non-supported properties should be accepted
                                "unvalidated": "{{ foo ",
                            },
                        ],
                    },
                ]
            )

            self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        with self.subTest("syntax error"):
            response = _do_create(
                [
                    {
                        "type": "textfield",
                        "key": "text1",
                        "description": "Broken {{ var {{ brokenNestedVar }} }}",
                    },
                    {
                        "label": "{% load i18n %}",  # only builtins are exposed
                        "type": "fieldset",
                        "key": "fieldset1",
                        "components": [
                            {
                                "type": "textfield",
                                "key": "text2",
                                "label": "{% bad_tag usage %}",
                            },
                        ],
                    },
                ]
            )

            self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

            errors = response.json()["invalidParams"]
            error_text1, error_fieldset, error_text2 = errors

            with self.subTest("text1 error"):
                self.assertEqual(error_text1["code"], "invalid-template-syntax")
                self.assertEqual(
                    error_text1["name"],
                    "configuration.components.0.description",
                )

            with self.subTest("fieldset error"):
                self.assertEqual(error_fieldset["code"], "invalid-template-syntax")
                self.assertEqual(
                    error_fieldset["name"],
                    "configuration.components.1.label",
                )

            with self.subTest("text2 error"):
                self.assertEqual(error_text2["code"], "invalid-template-syntax")
                self.assertEqual(
                    error_text2["name"],
                    "configuration.components.1.components.0.label",
                )


class FormioCoSignComponentValidationTests(APITestCase):
    """
    Test specific Formio component type validations for form definitions.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = SuperUserFactory.create()

    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.user)

    def test_configuration_with_co_sign_but_missing_auth_plugin(self):
        url = reverse("api:formdefinition-list")
        config = {
            "components": [
                {
                    "type": "coSign",
                    "key": "coSign",
                    "label": "Co-sign test",
                }
            ]
        }

        response = self.client.post(
            url,
            data={
                "name": "Some name",
                "slug": "some-slug",
                "configuration": config,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error = response.json()["invalidParams"][0]
        self.assertEqual(error["code"], "invalid")
        self.assertEqual(error["name"], "configuration")

    def test_configuration_with_co_sign_but_missing_global_config(self):
        prefill_config = PrefillConfig.get_solo()
        url = reverse("api:formdefinition-list")
        config = {
            "components": [
                {
                    "type": "coSign",
                    "key": "coSign",
                    "label": "Co-sign test",
                    "authPlugin": "digid",
                }
            ]
        }
        with self.subTest("assert test data as expected"):
            self.assertEqual(prefill_config.default_person_plugin, "")
            self.assertEqual(prefill_config.default_company_plugin, "")

        response = self.client.post(
            url,
            data={
                "name": "Some name",
                "slug": "some-slug",
                "configuration": config,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error = response.json()["invalidParams"][0]
        self.assertEqual(error["code"], "invalid")
        self.assertEqual(error["name"], "configuration")

    @patch("openforms.prefill.co_sign.PrefillConfig.get_solo")
    def test_configuration_with_co_sign_ok(self, mock_get_solo):
        mock_get_solo.return_value = PrefillConfig(default_person_plugin="stufbg")

        url = reverse("api:formdefinition-list")
        config = {
            "components": [
                {
                    "type": "coSign",
                    "key": "coSign",
                    "label": "Co-sign test",
                    "authPlugin": "digid",
                }
            ]
        }

        response = self.client.post(
            url,
            data={
                "name": "Some name",
                "slug": "some-slug",
                "configuration": config,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class FormDefinitionsAPITranslationTests(APITestCase):
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        TranslatedFormDefinitionFactory = make_translated(FormDefinitionFactory)
        cls.form_definition = TranslatedFormDefinitionFactory.create(
            _language="en",
            name="FormDefinition 1",
        )

        cls.user = StaffUserFactory.create(user_permissions=["change_form"])

    def test_detail_staff_show_translations(self):
        """
        Translations for all available languages should be returned for staff users,
        because they are relevant for the form design UI
        """
        self.client.force_authenticate(user=self.user)

        url = reverse(
            "api:formdefinition-detail", kwargs={"uuid": self.form_definition.uuid}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["translations"],
            {
                "en": {
                    "name": "FormDefinition 1",
                },
                "nl": {
                    "name": None,
                },
            },
        )

    def test_detail_non_staff_no_translations(self):
        """
        Translations for different languages than the active language should not be
        returned for non-staff users
        """
        url = reverse(
            "api:formdefinition-detail", kwargs={"uuid": self.form_definition.uuid}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("translations", response.data)

    def test_create_with_translations(self):
        self.client.force_authenticate(user=self.user)

        url = reverse("api:formdefinition-list")
        response = self.client.post(
            url,
            data={
                "name": "Name",
                "slug": "a-slug",
                "configuration": {
                    "display": "form",
                    "components": [
                        {
                            "label": "New field",
                            "key": "newField",
                            "type": "textfield",
                        }
                    ],
                },
                "translations": {
                    "en": {"name": "FormDefinition 1"},
                    "nl": {"name": "Formulierdefinitie 1"},
                },
            },
        )

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        definition = FormDefinition.objects.get(uuid=response.data["uuid"])

        self.assertEqual(definition.name_en, "FormDefinition 1")
        self.assertEqual(definition.name_nl, "Formulierdefinitie 1")

    def test_update_with_translations(self):
        self.client.force_authenticate(user=self.user)

        definition = FormDefinitionFactory.create(
            name_en="english name",
            name_nl="nederlandse naam",
        )

        url = reverse("api:formdefinition-detail", kwargs={"uuid": definition.uuid})
        response = self.client.patch(
            url,
            data={
                "translations": {
                    "en": {"name": "FormDefinition 1"},
                    "nl": {"name": "Formulierdefinitie 1"},
                }
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        definition.refresh_from_db()

        self.assertEqual(definition.name_en, "FormDefinition 1")
        self.assertEqual(definition.name_nl, "Formulierdefinitie 1")

    @patch(
        "openforms.api.exception_handling.uuid.uuid4",
        return_value="95a55a81-d316-44e8-b090-0519dd21be5f",
    )
    def test_update_with_translations_validate_name(self, _mock):
        self.client.force_authenticate(user=self.user)

        definition = FormDefinitionFactory.create(
            name_en="english name",
            name_nl="nederlandse naam",
        )

        url = reverse("api:formdefinition-detail", kwargs={"uuid": definition.uuid})
        response = self.client.patch(
            url,
            data={
                "translations": {
                    "en": {"name": "x" * 51},
                    "nl": {"name": "x" * 51},
                }
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {
                "type": "http://testserver/fouten/ValidationError/",
                "code": "invalid",
                "title": _("Invalid input."),
                "status": 400,
                "detail": "",
                "instance": "urn:uuid:95a55a81-d316-44e8-b090-0519dd21be5f",
                "invalidParams": [
                    {
                        "name": "translations.en.name",
                        "code": "max_length",
                        "reason": _(
                            "Ensure this field has no more than {max_length} characters."
                        ).format(max_length=50),
                    },
                    {
                        "name": "translations.nl.name",
                        "code": "max_length",
                        "reason": _(
                            "Ensure this field has no more than {max_length} characters."
                        ).format(max_length=50),
                    },
                ],
            },
        )
