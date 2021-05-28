from uuid import UUID

from django.urls import reverse, reverse_lazy

from rest_framework import status
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import UserFactory
from openforms.forms.models import Form, FormDefinition, FormStep
from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
)


class FormCreationViewTests(APITestCase):
    url_list = reverse_lazy("api:manage-forms-list")

    def test_needs_authentication(self):
        response = self.client.get(self.url_list)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_needs_to_be_staff(self):
        normal_user = UserFactory.create(is_staff=False)
        self.client.force_authenticate(user=normal_user)

        response = self.client.get(self.url_list)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_nested_form_data(self):
        form = FormFactory.create()
        form_def_1 = FormDefinitionFactory.create(
            configuration={
                "type": "form",
                "components": [
                    {"label": "First Name", "key": "first-name", "type": "textfield"},
                    {
                        "label": "Last name Name",
                        "key": "last-name",
                        "type": "textfield",
                    },
                ],
                "title": "Form def 1",
                "display": "Form def 1",
                "name": "form-def-1",
                "path": "form-def-1",
            }
        )
        form_def_2 = FormDefinitionFactory.create(
            configuration={
                "type": "form",
                "components": [
                    {
                        "label": "Place of birth",
                        "key": "place-of-birth",
                        "type": "textfield",
                    },
                ],
                "title": "Form def 2",
                "display": "Form def 2",
                "name": "form-def-2",
                "path": "form-def-2",
            }
        )
        FormStepFactory.create(form=form, form_definition=form_def_1, order=0)
        FormStepFactory.create(form=form, form_definition=form_def_2, order=1)

        staff_user = UserFactory.create(is_staff=True)
        self.client.force_authenticate(user=staff_user)

        response = self.client.get(self.url_list, {"uuid": form.uuid})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        retrieved_form = response.data[0]

        # Check the form fields
        self.assertIn("name", retrieved_form)
        self.assertIn("uuid", retrieved_form)
        self.assertIn("slug", retrieved_form)
        self.assertIn("form_steps", retrieved_form)

        # Check the form steps
        form_steps = retrieved_form["form_steps"]

        self.assertEqual(2, len(form_steps))

        for step in form_steps:
            self.assertIn("order", step)
            self.assertIn("form_definition", step)
            self.assertIn("uuid", step["form_definition"])
            self.assertIn("name", step["form_definition"])
            self.assertIn("slug", step["form_definition"])
            self.assertIn("configuration", step["form_definition"])

        # Check that the form definition contains the JSON configuration
        form_def_1_config = form_steps[0]["form_definition"]["configuration"]
        form_def_2_config = form_steps[1]["form_definition"]["configuration"]

        self.assertEqual(form_def_1.configuration, form_def_1_config)
        self.assertEqual(form_def_2.configuration, form_def_2_config)

    def test_create_new_form_with_new_definitions(self):
        new_form_data = {
            "uuid": "600f4032-1571-443f-86b5-7a173d7dc30e",
            "name": "Test Form",
            "slug": "test-form",
            "formSteps": [
                {
                    "order": 0,
                    "formDefinition": {
                        "uuid": "b00b5069-a013-4d92-bc3d-37180996ea14",
                        "name": "Test Def 1",
                        "slug": "test-def-1",
                        "configuration": {
                            "type": "form",
                            "components": [
                                {
                                    "label": "First Name",
                                    "key": "first-name",
                                    "type": "textfield",
                                },
                                {
                                    "label": "Last name Name",
                                    "key": "last-name",
                                    "type": "textfield",
                                },
                            ],
                            "title": "Form def 1",
                            "display": "Form def 1",
                            "name": "form-def-1",
                            "path": "form-def-1",
                        },
                    },
                },
                {
                    "order": 1,
                    "formDefinition": {
                        "uuid": "4336d0b1-ee72-4079-b3f9-908de23ae7d6",
                        "name": "Test Def 2",
                        "slug": "test-def-2",
                        "configuration": {
                            "type": "form",
                            "components": [
                                {
                                    "label": "Place of birth",
                                    "key": "place-of-birth",
                                    "type": "textfield",
                                },
                            ],
                            "title": "Form def 2",
                            "display": "Form def 2",
                            "name": "form-def-2",
                            "path": "form-def-2",
                        },
                    },
                },
            ],
        }

        staff_user = UserFactory.create(is_staff=True)
        self.client.force_authenticate(user=staff_user)

        response = self.client.post(self.url_list, new_form_data)

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        new_form = Form.objects.get()

        self.assertEqual("600f4032-1571-443f-86b5-7a173d7dc30e", new_form.uuid)
        self.assertEqual("Test Form", new_form.name)
        self.assertEqual("test-form", new_form.slug)

        form_steps = FormStep.objects.all()

        self.assertEqual(2, len(form_steps))

        for form_step in form_steps:
            self.assertEqual(form_step.form, new_form)

        form_definitions = FormDefinition.objects.all()

        self.assertEqual(2, form_definitions.count())

        form_definition_1 = form_definitions.get(
            uuid="b00b5069-a013-4d92-bc3d-37180996ea14"
        )
        self.assertEqual("Test Def 1", form_definition_1.name)

        form_definition_2 = form_definitions.get(
            uuid="4336d0b1-ee72-4079-b3f9-908de23ae7d6"
        )
        self.assertEqual("Test Def 2", form_definition_2.name)

    def test_create_new_form_with_existing_definitions(self):
        form_def_1 = FormDefinitionFactory.create(
            name="Test Def 1",
            slug="test-def-1",
            configuration={
                "type": "form",
                "components": [
                    {"label": "First Name", "key": "first-name", "type": "textfield"},
                    {
                        "label": "Last name Name",
                        "key": "last-name",
                        "type": "textfield",
                    },
                ],
                "title": "Form def 1",
                "display": "Form def 1",
                "name": "form-def-1",
                "path": "form-def-1",
            },
        )
        form_def_2 = FormDefinitionFactory.create(
            name="Test Def 2",
            slug="test-def-2",
            configuration={
                "type": "form",
                "components": [
                    {
                        "label": "Place of birth",
                        "key": "place-of-birth",
                        "type": "textfield",
                    },
                ],
                "title": "Form def 2",
                "display": "Form def 2",
                "name": "form-def-2",
                "path": "form-def-2",
            },
        )

        new_form_data = {
            "uuid": "600f4032-1571-443f-86b5-7a173d7dc30e",
            "name": "Test Form",
            "slug": "test-form",
            "formSteps": [
                {
                    "order": 0,
                    "formDefinition": {
                        "uuid": form_def_1.uuid,
                        "name": "Test Def 1",
                        "slug": "test-def-1",
                        "configuration": {
                            "type": "form",
                            "components": [
                                {
                                    "label": "First Name",
                                    "key": "first-name",
                                    "type": "textfield",
                                },
                                {
                                    "label": "Last name Name",
                                    "key": "last-name",
                                    "type": "textfield",
                                },
                            ],
                            "title": "Form def 1",
                            "display": "Form def 1",
                            "name": "form-def-1",
                            "path": "form-def-1",
                        },
                    },
                },
                {
                    "order": 1,
                    "formDefinition": {
                        "uuid": form_def_2.uuid,
                        "name": "Test Def 2",
                        "slug": "test-def-2",
                        "configuration": {
                            "type": "form",
                            "components": [
                                {
                                    "label": "Place of birth",
                                    "key": "place-of-birth",
                                    "type": "textfield",
                                },
                            ],
                            "title": "Form def 2",
                            "display": "Form def 2",
                            "name": "form-def-2",
                            "path": "form-def-2",
                        },
                    },
                },
            ],
        }

        staff_user = UserFactory.create(is_staff=True)
        self.client.force_authenticate(user=staff_user)

        response = self.client.post(self.url_list, new_form_data)

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        new_form = Form.objects.get()

        self.assertEqual("600f4032-1571-443f-86b5-7a173d7dc30e", new_form.uuid)
        self.assertEqual("Test Form", new_form.name)
        self.assertEqual("test-form", new_form.slug)

        form_steps = FormStep.objects.all()

        self.assertEqual(2, len(form_steps))

        expected_form_defs_uuids = [form_def_1.uuid, form_def_2.uuid]
        for form_step in form_steps:
            self.assertEqual(form_step.form, new_form)
            self.assertIn(
                UUID(form_step.form_definition.uuid), expected_form_defs_uuids
            )

        form_definitions = FormDefinition.objects.all()

        self.assertEqual(2, form_definitions.count())

    def test_update_form_and_definitions(self):
        form = FormFactory.create(name="Form Name")
        form_def_1 = FormDefinitionFactory.create(
            name="Test Def 1",
            slug="test-def-1",
            configuration={
                "type": "form",
                "components": [
                    {"label": "First Name", "key": "first-name", "type": "textfield"},
                    {
                        "label": "Last name Name",
                        "key": "last-name",
                        "type": "textfield",
                    },
                ],
                "title": "Form def 1",
                "display": "Form def 1",
                "name": "form-def-1",
                "path": "form-def-1",
            },
        )
        form_def_2 = FormDefinitionFactory.create(
            name="Test Def 2",
            slug="test-def-2",
            configuration={
                "type": "form",
                "components": [
                    {
                        "label": "Place of birth",
                        "key": "place-of-birth",
                        "type": "textfield",
                    },
                ],
                "title": "Form def 2",
                "display": "Form def 2",
                "name": "form-def-2",
                "path": "form-def-2",
            },
        )
        FormStepFactory.create(form=form, form_definition=form_def_1, order=0)
        FormStepFactory.create(form=form, form_definition=form_def_2, order=1)

        staff_user = UserFactory.create(is_staff=True)
        self.client.force_authenticate(user=staff_user)

        updated_form_data = {
            "uuid": form.uuid,
            "name": "Updated Form Name",
            "slug": "test-form",
            "formSteps": [
                {
                    "order": 0,
                    "formDefinition": {
                        "uuid": form_def_1.uuid,
                        "name": "Updated Test Def 1",
                        "slug": "test-def-1",
                        "configuration": {
                            "type": "form",
                            "components": [
                                {
                                    "label": "First Name",
                                    "key": "first-name",
                                    "type": "textfield",
                                },
                                {
                                    "label": "Last name Name",
                                    "key": "last-name",
                                    "type": "textfield",
                                },
                            ],
                            "title": "Form def 1",
                            "display": "Form def 1",
                            "name": "form-def-1",
                            "path": "form-def-1",
                        },
                    },
                },
                {
                    "order": 1,
                    "formDefinition": {
                        "uuid": "f49a2c2b-4299-4d15-a80c-abdc029edd38",
                        "name": "Test Def 3",
                        "slug": "test-def-3",
                        "configuration": {
                            "type": "form",
                            "components": [
                                {
                                    "label": "Favourite word",
                                    "key": "favourite-word",
                                    "type": "textfield",
                                },
                            ],
                            "title": "Form def 3",
                            "display": "Form def 3",
                            "name": "form-def-3",
                            "path": "form-def-3",
                        },
                    },
                },
            ],
        }

        url_detail = reverse("api:manage-forms-detail", args=[form.uuid])
        response = self.client.put(url_detail, updated_form_data)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        self.assertEqual(1, Form.objects.all().count())
        self.assertEqual(3, FormDefinition.objects.all().count())
        self.assertEqual(2, FormStep.objects.all().count())

        form.refresh_from_db()

        self.assertEqual("Updated Form Name", form.name)
        self.assertIsNotNone(
            FormStep.objects.filter(
                form=form, form_definition__uuid="f49a2c2b-4299-4d15-a80c-abdc029edd38"
            ).first()
        )

        form_def_1.refresh_from_db()

        self.assertEqual("Updated Test Def 1", form_def_1.name)
