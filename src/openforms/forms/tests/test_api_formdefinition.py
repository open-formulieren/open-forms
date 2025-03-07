from unittest.mock import patch

from django.test import override_settings
from django.urls import reverse
from django.utils import translation
from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import (
    StaffUserFactory,
    SuperUserFactory,
    UserFactory,
)
from openforms.prefill.models import PrefillConfig

from ..models import FormDefinition
from .factories import FormDefinitionFactory, FormFactory, FormStepFactory


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
                "translations": {
                    "en": {"name": "Updated name"},
                    "nl": {"name": "Bijgewerkte naam"},
                },
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        definition.refresh_from_db()

        self.assertEqual("Bijgewerkte naam", definition.name)
        self.assertEqual("Updated name", definition.name_en)
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

    def test_update_html_sanitizing_allowed_content_remains(self):
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

        allowed_content = (
            "Naked text",
            "Naked text with cool stuff {% if true %}{{ variable }}{% endif %}",
            "<p>Regular</p>",
            "<b>Bold</b>",
            "<strong>Strong</strong>",
            "<u>Underlined</u>",
            "<i>Italic</i>",
            "<sup>Superscript</sup>",
            "<s>Strike through</s>",
            "<em>Emphasis</em>",
            "<br>",
            '<a href="mailto:example@mail.com" data-fr-linked="true">Hello</a>',
            '<a href="https://www.example.com" target="_blank" rel="noopener noreferrer">hello</a>',
            "<ul><li>Un-ordered list</li></ul>",
            "<ol><li>Ordered list</li></ol>",
            "<h1>H1</h1>",
            "<h2>H2</h2>",
            "<h3>H3</h3>",
            "<h4>H4</h4>",
            "<h5>H5</h5>",
            "<h6>H6</h6>",
            "<p><i><b>Nested</b></i><br><u>stuff</u></p>",
            "<p><i><b>Nested variables {% if variable %}{{ variable }}{% endif %}</b></i><br></p>",
        )

        for content in allowed_content:
            with self.subTest(label=content):
                url = reverse(
                    "api:formdefinition-detail", kwargs={"uuid": definition.uuid}
                )
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
                                    "label": content,
                                    "description": content,
                                    "tooltip": content,
                                },
                            ],
                        },
                    },
                )

                self.assertEqual(response.status_code, status.HTTP_200_OK)

                definition.refresh_from_db()

                config = definition.configuration
                textfield = config["components"][0]

                self.assertIn("label", textfield)
                self.assertIn("description", textfield)
                self.assertIn("tooltip", textfield)
                self.assertEqual(textfield["label"], content)
                self.assertEqual(textfield["description"], content)
                self.assertEqual(textfield["tooltip"], content)

    def test_update_html_sanitizing_disallowed_content_sanitized(self):
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

        disallowed_content_expected_map = (
            ("<img src=x onerror=alert('123') />", ""),
            ("<a href=x onerror=alert('123')>foo</a>", '<a href="x">foo</a>'),
            ("<div>foo bar</div>", "foo bar"),
        )

        for disallowed_content, expected in disallowed_content_expected_map:
            with self.subTest(label=disallowed_content):
                url = reverse(
                    "api:formdefinition-detail", kwargs={"uuid": definition.uuid}
                )
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
                                    "label": disallowed_content,
                                    "description": disallowed_content,
                                    "tooltip": disallowed_content,
                                },
                            ],
                        },
                    },
                )

                self.assertEqual(response.status_code, status.HTTP_200_OK)

                definition.refresh_from_db()

                config = definition.configuration
                textfield = config["components"][0]

                self.assertIn("label", textfield)
                self.assertIn("description", textfield)
                self.assertIn("tooltip", textfield)
                self.assertEqual(textfield["label"], expected)
                self.assertEqual(textfield["description"], expected)
                self.assertEqual(textfield["tooltip"], expected)

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
                "translations": {
                    "en": {"name": "Name"},
                    "nl": {"name": "Naam"},
                },
            },
        )

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        definition = FormDefinition.objects.get()

        self.assertEqual("Naam", definition.name)
        self.assertEqual("Name", definition.name_en)
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
                    "display": "form",
                    "components": [
                        {
                            "someCamelCase": "field",
                            "key": "somekey",
                            "type": "textfield",
                        }
                    ],
                },
            },
        )

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        config = FormDefinition.objects.get().configuration
        self.assertIn("someCamelCase", config["components"][0])
        self.assertNotIn("some_amel_case", config["components"][0])

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

    def test_create_html_sanitizing_allowed_content_remains(self):
        user = StaffUserFactory.create(user_permissions=["change_form"])
        self.client.force_authenticate(user=user)

        allowed_content = (
            "Naked text",
            "Naked text with cool stuff {% if true %}{{ variable }}{% endif %}",
            "<p>Regular</p>",
            "<b>Bold</b>",
            "<strong>Strong</strong>",
            "<u>Underlined</u>",
            "<i>Italic</i>",
            "<sup>Superscript</sup>",
            "<s>Strike through</s>",
            "<em>Emphasis</em>",
            "<br>",
            '<a href="mailto:example@mail.com" data-fr-linked="true">Hello</a>',
            '<a href="https://www.example.com" target="_blank" rel="noopener noreferrer">hello</a>',
            "<ul><li>Un-ordered list</li></ul>",
            "<ol><li>Ordered list</li></ol>",
            "<h1>H1</h1>",
            "<h2>H2</h2>",
            "<h3>H3</h3>",
            "<h4>H4</h4>",
            "<h5>H5</h5>",
            "<h6>H6</h6>",
            "<p><i><b>Nested</b></i><br><u>stuff</u></p>",
            "<p><i><b>Nested variables {% if variable %}{{ variable }}{% endif %}</b></i><br></p>",
        )

        for content in allowed_content:
            with self.subTest(label=content):
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
                                    "key": "somekey",
                                    "type": "textfield",
                                    "label": content,
                                    "description": content,
                                    "tooltip": content,
                                }
                            ],
                        },
                    },
                )

                self.assertEqual(status.HTTP_201_CREATED, response.status_code)
                config = FormDefinition.objects.get().configuration

                textfield = config["components"][0]
                self.assertIn("label", textfield)
                self.assertIn("description", textfield)
                self.assertIn("tooltip", textfield)
                self.assertEqual(textfield["label"], content)
                self.assertEqual(textfield["description"], content)
                self.assertEqual(textfield["tooltip"], content)

                # Remove form definition, to create a clean instance for the next content to test
                FormDefinition.objects.get().delete()

    def test_create_html_sanitizing_disallowed_content_sanitized(self):
        user = StaffUserFactory.create(user_permissions=["change_form"])
        self.client.force_authenticate(user=user)

        disallowed_content_expected_map = (
            ("<img src=x onerror=alert('123') />", ""),
            ("<a href=x onerror=alert('123')>foo</a>", '<a href="x">foo</a>'),
            ("<div>foo bar</div>", "foo bar"),
        )

        for disallowed_content, expected in disallowed_content_expected_map:
            with self.subTest(label=disallowed_content):
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
                                    "key": "somekey",
                                    "type": "textfield",
                                    "label": disallowed_content,
                                    "description": disallowed_content,
                                    "tooltip": disallowed_content,
                                }
                            ],
                        },
                    },
                )

                self.assertEqual(status.HTTP_201_CREATED, response.status_code)
                config = FormDefinition.objects.get().configuration

                textfield = config["components"][0]

                self.assertIn("label", textfield)
                self.assertIn("description", textfield)
                self.assertIn("tooltip", textfield)
                self.assertEqual(textfield["label"], expected)
                self.assertEqual(textfield["description"], expected)
                self.assertEqual(textfield["tooltip"], expected)

                # Remove form definition, to create a clean instance for the next content to test
                FormDefinition.objects.get().delete()

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

    def test_filter_by_reusable(self):
        user = StaffUserFactory.create(user_permissions=["change_form"])
        self.client.force_authenticate(user=user)
        FormDefinitionFactory.create(is_reusable=False)
        fd2 = FormDefinitionFactory.create(is_reusable=True)
        url = reverse("api:formdefinition-list")

        response = self.client.get(url, {"is_reusable": "1"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(response_data["count"], 1)
        fd = response_data["results"][0]
        self.assertEqual(fd["uuid"], str(fd2.uuid))

    def test_filter_by_used_in(self):
        user = StaffUserFactory.create(user_permissions=["change_form"])
        self.client.force_authenticate(user=user)
        form_1 = FormFactory.create(generate_minimal_setup=True)
        FormFactory.create(generate_minimal_setup=True)
        url = reverse("api:formdefinition-list")

        response = self.client.get(url, {"used_in": form_1.uuid})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(response_data["count"], 1)
        fd = response_data["results"][0]
        self.assertEqual(
            fd["uuid"], str(form_1.formstep_set.get().form_definition.uuid)
        )

    @override_settings(LANGUAGE_CODE="en")
    def test_duplicate_components(self):
        user = StaffUserFactory.create(user_permissions=["change_form"])
        self.client.force_authenticate(user=user)

        url = reverse("api:formdefinition-list")
        response = self.client.post(
            url,
            data={
                "name": "Name",
                "slug": "a-slug",
                "configuration": {
                    "components": [
                        {"key": "duplicate", "label": "Duplicate", "type": "textfield"},
                        {
                            "key": "repeatingGroup",
                            "label": "Repeating Group",
                            "type": "editgrid",
                            "components": [
                                {
                                    "key": "duplicate",
                                    "label": "Duplicate",
                                    "type": "textfield",
                                },
                                {
                                    "key": "notDuplicate",
                                    "label": "Not Duplicate",
                                    "type": "textfield",
                                },
                            ],
                        },
                        {
                            "key": "anotherDuplicate",
                            "label": "Another Duplicate",
                            "type": "textfield",
                        },
                        {
                            "key": "anotherDuplicate",
                            "label": "Accidental Duplicate",
                            "type": "textfield",
                        },
                    ]
                },
            },
        )

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

        data = response.json()

        self.assertEqual(
            data["invalidParams"][0]["reason"],
            'Detected duplicate keys in configuration: "duplicate" (in Duplicate, '
            'Repeating Group > Duplicate) ,  "anotherDuplicate" (in Another Duplicate, Accidental Duplicate)',
        )

    def test_templatetag_expression_is_valid(self):
        user = StaffUserFactory.create(user_permissions=["change_form"])
        self.client.force_authenticate(user=user)

        url = reverse("api:formdefinition-list")

        response = self.client.post(
            url,
            data={
                "name": "Name",
                "slug": "form-definition-with-content",
                "configuration": {
                    "display": "form",
                    "components": [
                        {
                            "key": "htmlContent",
                            "type": "content",
                            "html": """Here is a value: {% get_value someVariable 'someKey' %}""",
                        }
                    ],
                },
            },
        )

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)


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
        self.assertEqual(error["name"], "configuration.nonFieldErrors")

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
        self.assertEqual(error["name"], "configuration.nonFieldErrors")

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

        with translation.override("en"):
            cls.form_definition = FormDefinitionFactory.create(name="FormDefinition 1")

        cls.user = StaffUserFactory.create(user_permissions=["change_form"])

    def test_detail_staff_show_translations(self):
        """
        Translations for all available languages should be returned for staff users, because they are relevant for the form design UI
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
                    "name": "",
                },
            },
        )

    def test_detail_non_staff_no_translations(self):
        """
        Translations for different languages than the active language should not be returned for non-staff users
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
                        "name": "translations.nl.name",
                        "code": "max_length",
                        "reason": _(
                            "Ensure this field has no more than {max_length} characters."
                        ).format(max_length=50),
                    },
                    {
                        "name": "translations.en.name",
                        "code": "max_length",
                        "reason": _(
                            "Ensure this field has no more than {max_length} characters."
                        ).format(max_length=50),
                    },
                ],
            },
        )

    def test_default_language_name_required(self):
        self.client.force_authenticate(user=self.user)
        definition = FormDefinitionFactory.create(
            name_en="english name",
            name_nl="nederlandse naam",
        )
        url = reverse("api:formdefinition-detail", kwargs={"uuid": definition.uuid})

        response = self.client.patch(
            url,
            data={"translations": {"nl": {"name": ""}}},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        invalid_params = response.json()["invalidParams"]
        self.assertEqual(len(invalid_params), 1)
        self.assertEqual(invalid_params[0]["code"], "blank")
