from django.urls import reverse

from furl import furl
from rest_framework import status
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.forms.models.form import FormLogic
from openforms.forms.tests.factories import FormFactory, FormStepFactory
from openforms.submissions.tests.form_logic.factories import FormLogicFactory


class FormLogicAPITests(APITestCase):
    def test_auth_required(self):
        url = reverse("api:form-logics-list")

        response = self.client.post(url)

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

    def test_list_and_filter_form_logic(self):
        user = SuperUserFactory.create(username="test", password="test")
        form1 = FormFactory.create()
        form2 = FormFactory.create()

        FormLogicFactory.create(
            form=form1,
        )
        FormLogicFactory.create(
            form=form2,
        )

        self.client.force_authenticate(user)
        url = reverse("api:form-logics-list")
        url = furl(url).set({"form": form1.uuid}).url
        response = self.client.get(url)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        response_data = response.json()

        self.assertEqual(1, len(response_data))

    def test_create_form_logic(self):
        user = SuperUserFactory.create(username="test", password="test")
        form = FormFactory.create()
        FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "step1_textfield1",
                    }
                ]
            },
        )

        form_logic_data = {
            "form": f"http://testserver{reverse('api:form-detail', kwargs={'uuid_or_slug': form.uuid})}",
            "json_logic_trigger": {
                "==": [
                    {"var": "step1_textfield1"},
                    "hide step 1",
                ]
            },
            "actions": [
                {
                    "component": "step1_textfield1",
                    "action": {
                        "name": "Hide element",
                        "type": "property",
                        "property": {"value": "hidden", "type": "bool"},
                        "state": True,
                    },
                }
            ],
        }

        self.client.force_authenticate(user=user)
        url = reverse("api:form-logics-list")
        response = self.client.post(url, data=form_logic_data)

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        form_logics_qs = FormLogic.objects.all()

        self.assertEqual(1, form_logics_qs.count())

        form_logic = form_logics_qs.get()

        self.assertEqual(form, form_logic.form)

    def test_create_logic_with_dates(self):
        user = SuperUserFactory.create(username="test", password="test")
        form = FormFactory.create()
        FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "datetime",
                        "key": "dateOfBirth",
                    }
                ]
            },
        )

        form_logic_data = {
            "form": f"http://testserver{reverse('api:form-detail', kwargs={'uuid_or_slug': form.uuid})}",
            "json_logic_trigger": {
                ">": [
                    {"date": {"var": "dateOfBirth"}},
                    {"-": [{"today": []}, {"rdelta": [18]}]},
                ]
            },
            "actions": [
                {
                    "component": "step1_textfield1",
                    "action": {
                        "name": "Hide element",
                        "type": "property",
                        "property": {"value": "hidden", "type": "bool"},
                        "state": True,
                    },
                }
            ],
        }

        self.client.force_authenticate(user=user)
        url = reverse("api:form-logics-list")
        response = self.client.post(url, data=form_logic_data)

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

    def test_create_logic_with_invalid_dates(self):
        user = SuperUserFactory.create(username="test", password="test")
        form = FormFactory.create()
        FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "datetime",
                        "key": "dateOfBirth",
                    },
                    {
                        "type": "textfield",
                        "key": "someValue",
                    },
                ]
            },
        )

        form_logic_data = {
            "form": f"http://testserver{reverse('api:form-detail', kwargs={'uuid_or_slug': form.uuid})}",
            "json_logic_trigger": {
                ">": [
                    {"date": {"var": "dateOfBirth"}},
                    {"var": ["someValue"]},
                ]
            },
            "actions": [
                {
                    "component": "step1_textfield1",
                    "action": {
                        "name": "Hide element",
                        "type": "property",
                        "property": {
                            "value": "hidden",
                        },
                        "state": True,
                    },
                }
            ],
        }

        self.client.force_authenticate(user=user)
        url = reverse("api:form-logics-list")
        response = self.client.post(url, data=form_logic_data)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_actions_is_a_list(self):
        user = SuperUserFactory.create(username="test", password="test")
        form = FormFactory.create()
        step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "step1_textfield1",
                    }
                ]
            },
        )

        form_logic_data = {
            "form_step": f"http://testserver{reverse('api:form-steps-detail', kwargs={'form_uuid_or_slug': form.uuid, 'uuid': step.uuid})}",
            "component": "step1_textfield1",
            "json_logic_trigger": {
                "==": [
                    {"var": "step1_textfield1"},
                    "hide step 1",
                ]
            },
            "actions": {
                "name": "Hide element",
                "type": "property",
                "property": {"value": "hidden", "type": "bool"},
                "state": True,
            },
        }

        self.client.force_authenticate(user=user)
        url = reverse("api:form-logics-list")
        response = self.client.post(url, data=form_logic_data)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_partial_update_form_logic(self):
        user = SuperUserFactory.create(username="test", password="test")
        form1, form2 = FormFactory.create_batch(2)

        for form in [form1, form2]:
            FormStepFactory.create(
                form=form,
                form_definition__configuration={
                    "components": [
                        {
                            "type": "textfield",
                            "key": "step1_textfield1",
                        }
                    ]
                },
            )

        logic = FormLogicFactory.create(
            form=form1,
            json_logic_trigger={
                "==": [
                    {"var": "step1_textfield1"},
                    "hide step 2",
                ]
            },
            actions=[
                {
                    "component": "step1_textfield1",
                    "action": {
                        "name": "Hide element",
                        "type": "property",
                        "property": {"value": "hidden", "type": "bool"},
                        "state": True,
                    },
                }
            ],
        )

        self.client.force_authenticate(user=user)
        url = reverse("api:form-logics-detail", kwargs={"uuid": logic.uuid})
        response = self.client.patch(
            url,
            data={
                "form": f"http://testserver{reverse('api:form-detail', kwargs={'uuid_or_slug': form2.uuid})}"
            },
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        logic.refresh_from_db()

        self.assertEqual(form2, logic.form)

    def test_delete_form_logic(self):
        user = SuperUserFactory.create(username="test", password="test")
        form = FormFactory.create()

        logic = FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "==": [
                    {"var": "step1_textfield1"},
                    "hide step 1",
                ]
            },
            actions=[
                {
                    "component": "step1_textfield1",
                    "action": {
                        "name": "Hide element",
                        "type": "property",
                        "property": {"value": "hidden", "type": "bool"},
                        "state": True,
                    },
                }
            ],
        )

        self.client.force_authenticate(user=user)
        url = reverse("api:form-logics-detail", kwargs={"uuid": logic.uuid})
        response = self.client.delete(url)

        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        self.assertEqual(0, FormLogic.objects.all().count())

    def test_invalid_logic_trigger(self):
        user = SuperUserFactory.create()
        form = FormFactory.create()
        FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "step1_textfield1",
                    }
                ]
            },
        )

        form_logic_data = {
            "form": f"http://testserver{reverse('api:form-detail', kwargs={'uuid_or_slug': form.uuid})}",
            "json_logic_trigger": {
                "invalid_op": [
                    {"var": "step1_textfield1"},
                    "hide step 1",
                ]
            },
            "actions": [
                {
                    "component": "step1_textfield1",
                    "action": {
                        "name": "Hide element",
                        "type": "property",
                        "property": {"value": "hidden", "type": "bool"},
                        "state": True,
                    },
                }
            ],
        }

        self.client.force_authenticate(user=user)
        url = reverse("api:form-logics-list")
        response = self.client.post(url, data=form_logic_data)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual(
            "jsonLogicTrigger", response.json()["invalidParams"][0]["name"]
        )

    def test_invalid_logic_trigger_not_component_reference(self):
        user = SuperUserFactory.create()
        self.client.force_authenticate(user=user)
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {"type": "textfield", "key": "step1_textfield1"},
                    {
                        "type": "date",
                        "key": "step1_date1",
                    },
                ]
            },
        )
        form_path = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        url = reverse("api:form-logics-list")
        invalid = [
            {"==": [1, 1]},
            {"==": [{"date": "2022-01-12"}, {"-": [{"today": []}, {"rdelta": [18]}]}]},
        ]

        for trigger in invalid:
            with self.subTest(trigger=trigger):
                form_logic_data = {
                    "form": f"http://testserver{form_path}",
                    "json_logic_trigger": trigger,
                    "actions": [
                        {
                            "component": "step1_textfield1",
                            "action": {
                                "name": "Hide element",
                                "type": "property",
                                "property": {"value": "hidden", "type": "bool"},
                                "state": True,
                            },
                        }
                    ],
                }

                response = self.client.post(url, data=form_logic_data)

                self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
                self.assertEqual(
                    "jsonLogicTrigger", response.json()["invalidParams"][0]["name"]
                )

    def test_create_rule_with_empty_formstep(self):
        user = SuperUserFactory.create(username="test", password="test")
        form = FormFactory.create()
        FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "name",
                    },
                    {
                        "type": "textfield",
                        "key": "surname",
                    },
                ]
            },
        )

        form_logic_data = {
            "form": f"http://testserver{reverse('api:form-detail', kwargs={'uuid_or_slug': form.uuid})}",
            "json_logic_trigger": {"==": [{"var": "name"}, "John"]},
            "actions": [
                {
                    "formStep": "",
                    "component": "surname",
                    "action": {
                        "type": "value",
                        "property": {},
                        "value": {"var": "name"},
                    },
                }
            ],
        }

        self.client.force_authenticate(user=user)
        url = reverse("api:form-logics-list")
        response = self.client.post(url, data=form_logic_data)

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

    def test_logic_with_selectboxes_and_components_with_dots_in_keyname(self):
        user = SuperUserFactory.create(username="test", password="test")
        form = FormFactory.create()
        FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "selectboxes",
                        "key": "foo.bar",
                        "values": [
                            {"label": "Option 1", "value": "option1"},
                            {"label": "Option 2", "value": "option2"},
                        ],
                    },
                    {"key": "fuu.ber", "type": "textfield"},
                    {"key": "normalComponent", "type": "textfield"},
                ]
            },
        )

        form_logic_1 = {
            "form": f"http://testserver{reverse('api:form-detail', kwargs={'uuid_or_slug': form.uuid})}",
            "json_logic_trigger": {
                "==": [
                    {"var": "foo.bar.option1"},
                    True,
                ]
            },
            "actions": [
                {
                    "component": "normalComponent",
                    "action": {
                        "name": "Hide element",
                        "type": "property",
                        "property": {"value": "hidden", "type": "bool"},
                        "state": True,
                    },
                }
            ],
        }

        form_logic_2 = {
            "form": f"http://testserver{reverse('api:form-detail', kwargs={'uuid_or_slug': form.uuid})}",
            "json_logic_trigger": {
                "==": [
                    {"var": "fuu.ber"},
                    "test-value",
                ]
            },
            "actions": [
                {
                    "component": "normalComponent",
                    "action": {
                        "name": "Hide element",
                        "type": "property",
                        "property": {"value": "hidden", "type": "bool"},
                        "state": True,
                    },
                }
            ],
        }

        self.client.force_authenticate(user=user)
        url = reverse("api:form-logics-list")

        response_1 = self.client.post(url, data=form_logic_1)
        response_2 = self.client.post(url, data=form_logic_2)

        self.assertEqual(status.HTTP_201_CREATED, response_1.status_code)
        self.assertEqual(status.HTTP_201_CREATED, response_2.status_code)

    def test_create_advanced_logic_rule(self):
        user = SuperUserFactory.create()
        self.client.force_authenticate(user=user)
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "text1",
                    },
                    {
                        "type": "textfield",
                        "key": "text2",
                    },
                ]
            },
        )
        form_url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        form_logic_data = {
            "form": f"http://testserver{form_url}",
            "json_logic_trigger": {
                "and": [
                    {"==": [{"var": "text1"}, "foo"]},
                    {"in": ["bar", {"var": "text2"}]},
                ]
            },
            "actions": [
                {
                    "component": "text2",
                    "action": {
                        "type": "property",
                        "property": {
                            "type": "bool",
                            "value": "hidden",
                        },
                        "state": True,
                    },
                }
            ],
            "is_advanced": True,
        }
        url = reverse("api:form-logics-list")

        response = self.client.post(url, data=form_logic_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_logic_rule_skip_trigger_validation(self):
        """
        Assert that the trigger validation is skipped if dependent data is missing.
        """
        user = SuperUserFactory.create()
        self.client.force_authenticate(user=user)
        form_logic_data = {
            "form": "invalid",
            "json_logic_trigger": {
                "invalid_op": [
                    {"==": [{"var": "text1"}, "foo"]},
                    {"in": ["bar", {"var": "text2"}]},
                ]
            },
            "actions": [
                {
                    "component": "text2",
                    "action": {
                        "type": "property",
                        "property": {
                            "type": "bool",
                            "value": "hidden",
                        },
                        "state": True,
                    },
                }
            ],
            "is_advanced": True,
        }
        url = reverse("api:form-logics-list")

        response = self.client.post(url, data=form_logic_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual("form", response.json()["invalidParams"][0]["name"])

    def test_create_logic_rule_trigger_invalid_reference(self):
        user = SuperUserFactory.create()
        self.client.force_authenticate(user=user)
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "text1",
                    },
                    {
                        "type": "textfield",
                        "key": "text2",
                    },
                ]
            },
        )
        form_url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        form_logic_data = {
            "form": f"http://testserver{form_url}",
            "json_logic_trigger": {
                "==": [{"var": "text42"}, "foo"],
            },
            "actions": [
                {
                    "component": "text2",
                    "action": {
                        "type": "property",
                        "property": {
                            "type": "bool",
                            "value": "hidden",
                        },
                        "state": True,
                    },
                }
            ],
            "is_advanced": False,
        }
        url = reverse("api:form-logics-list")

        response = self.client.post(url, data=form_logic_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            "jsonLogicTrigger", response.json()["invalidParams"][0]["name"]
        )

    def test_second_operand_in_trigger_cant_be_empty_var(self):
        user = SuperUserFactory.create()
        self.client.force_authenticate(user=user)
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "text1",
                    },
                    {
                        "type": "textfield",
                        "key": "text2",
                    },
                ]
            },
        )

        form_url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        form_logic_data = {
            "form": f"http://testserver{form_url}",
            "json_logic_trigger": {
                "==": [{"var": "text1"}, {"var": ""}]
            },  # Empty comparison component
            "actions": [
                {
                    "component": "text2",
                    "action": {
                        "type": "property",
                        "property": {
                            "type": "bool",
                            "value": "hidden",
                        },
                        "state": True,
                    },
                }
            ],
            "is_advanced": False,
        }
        url = reverse("api:form-logics-list")

        response = self.client.post(url, data=form_logic_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            "jsonLogicTrigger", response.json()["invalidParams"][0]["name"]
        )

    def test_first_operand_in_trigger_cant_be_empty_var(self):
        user = SuperUserFactory.create()
        self.client.force_authenticate(user=user)
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "text1",
                    },
                    {
                        "type": "textfield",
                        "key": "text2",
                    },
                ]
            },
        )

        form_url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        form_logic_data = {
            "form": f"http://testserver{form_url}",
            "json_logic_trigger": {
                "==": [{"var": ""}, {"var": "text1"}]
            },  # Empty comparison component
            "actions": [
                {
                    "component": "text2",
                    "action": {
                        "type": "property",
                        "property": {
                            "type": "bool",
                            "value": "hidden",
                        },
                        "state": True,
                    },
                }
            ],
            "is_advanced": False,
        }
        url = reverse("api:form-logics-list")

        response = self.client.post(url, data=form_logic_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            "jsonLogicTrigger", response.json()["invalidParams"][0]["name"]
        )

    def test_can_refer_to_literal_in_value_action(self):
        user = SuperUserFactory.create()
        self.client.force_authenticate(user=user)
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "text1",
                    },
                    {
                        "type": "textfield",
                        "key": "text2",
                    },
                ]
            },
        )

        form_url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        form_logic_data = {
            "form": f"http://testserver{form_url}",
            "json_logic_trigger": {"==": [{"var": "text1"}, {"var": "text2"}]},
            "actions": [
                {
                    "formStep": "",
                    "component": "text1",
                    "action": {
                        "type": "value",
                        "property": {"value": "", "type": ""},
                        "value": "A test value",  # A literal value
                        "state": "",
                    },
                }
            ],
            "is_advanced": False,
        }
        url = reverse("api:form-logics-list")

        response = self.client.post(url, data=form_logic_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_cant_have_empty_component_value_in_value_action(self):
        user = SuperUserFactory.create()
        self.client.force_authenticate(user=user)
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "text1",
                    },
                    {
                        "type": "textfield",
                        "key": "text2",
                    },
                ]
            },
        )

        form_url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        form_logic_data = {
            "form": f"http://testserver{form_url}",
            "json_logic_trigger": {"==": [{"var": "text1"}, {"var": "text2"}]},
            "actions": [
                {
                    "formStep": "",
                    "component": "text1",
                    "action": {
                        "type": "value",
                        "property": {"value": "", "type": ""},
                        "value": {"var": ""},  # Empty Component!
                        "state": "",
                    },
                }
            ],
            "is_advanced": False,
        }
        url = reverse("api:form-logics-list")

        response = self.client.post(url, data=form_logic_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            "actions.0.action.value", response.json()["invalidParams"][0]["name"]
        )

    def test_cant_have_empty_component_in_value_action(self):
        user = SuperUserFactory.create()
        self.client.force_authenticate(user=user)
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "text1",
                    },
                    {
                        "type": "textfield",
                        "key": "text2",
                    },
                ]
            },
        )

        form_url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        form_logic_data = {
            "form": f"http://testserver{form_url}",
            "json_logic_trigger": {"==": [{"var": "text1"}, {"var": "text2"}]},
            "actions": [
                {
                    "formStep": "",
                    "component": "",  # Empty Component!
                    "action": {
                        "type": "value",
                        "property": {"value": "", "type": ""},
                        "value": {"var": "text1"},
                        "state": "",
                    },
                }
            ],
            "is_advanced": False,
        }
        url = reverse("api:form-logics-list")

        response = self.client.post(url, data=form_logic_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            "actions.0.component", response.json()["invalidParams"][0]["name"]
        )
        self.assertEqual("blank", response.json()["invalidParams"][0]["code"])

    def test_cant_have_empty_component_in_property_action(self):
        user = SuperUserFactory.create()
        self.client.force_authenticate(user=user)
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "text1",
                    },
                    {
                        "type": "textfield",
                        "key": "text2",
                    },
                ]
            },
        )

        form_url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        form_logic_data = {
            "form": f"http://testserver{form_url}",
            "json_logic_trigger": {"==": [{"var": "text1"}, {"var": "text2"}]},
            "actions": [
                {
                    "component": "",  # Empty Component
                    "action": {
                        "name": "Hide element",
                        "type": "property",
                        "property": {"value": "hidden", "type": "bool"},
                        "state": True,
                    },
                }
            ],
            "is_advanced": False,
        }
        url = reverse("api:form-logics-list")

        response = self.client.post(url, data=form_logic_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            "actions.0.component", response.json()["invalidParams"][0]["name"]
        )
        self.assertEqual("blank", response.json()["invalidParams"][0]["code"])

    def test_cant_have_empty_state_in_property_action(self):
        user = SuperUserFactory.create()
        self.client.force_authenticate(user=user)
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "text1",
                    },
                    {
                        "type": "textfield",
                        "key": "text2",
                    },
                ]
            },
        )

        form_url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        form_logic_data = {
            "form": f"http://testserver{form_url}",
            "json_logic_trigger": {"==": [{"var": "text1"}, {"var": "text2"}]},
            "actions": [
                {
                    "component": "text1",
                    "action": {
                        "name": "Hide element",
                        "type": "property",
                        "property": {"value": "hidden", "type": "bool"},
                        "state": "",  # Empty state!
                    },
                }
            ],
            "is_advanced": False,
        }
        url = reverse("api:form-logics-list")

        response = self.client.post(url, data=form_logic_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            "actions.0.action.state", response.json()["invalidParams"][0]["name"]
        )
        self.assertEqual("blank", response.json()["invalidParams"][0]["code"])

    def test_cant_have_empty_component_in_mark_step_as_not_applicable(self):
        user = SuperUserFactory.create()
        self.client.force_authenticate(user=user)
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "text1",
                    },
                    {
                        "type": "textfield",
                        "key": "text2",
                    },
                ]
            },
        )

        form_url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        form_logic_data = {
            "form": f"http://testserver{form_url}",
            "json_logic_trigger": {"==": [{"var": "text1"}, {"var": "text2"}]},
            "actions": [
                {
                    "formStep": "",  # Empty form step
                    "action": {
                        "name": "Mark step as not applicable",
                        "type": "step-not-applicable",
                        "property": {"value": "", "type": ""},
                        "state": "",
                    },
                }
            ],
            "is_advanced": False,
        }
        url = reverse("api:form-logics-list")

        response = self.client.post(url, data=form_logic_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            "actions.0.formStep", response.json()["invalidParams"][0]["name"]
        )
        self.assertEqual("blank", response.json()["invalidParams"][0]["code"])
