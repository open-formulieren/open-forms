import functools
import types
from threading import Thread
from time import sleep
from unittest import skip
from unittest.mock import patch

from django.db import close_old_connections
from django.urls import reverse

from furl import furl
from rest_framework import status
from rest_framework.test import APITestCase, APITransactionTestCase

from openforms.accounts.tests.factories import SuperUserFactory

from ..models import FormLogic
from .factories import FormFactory, FormLogicFactory, FormStepFactory


class FormLogicAPITests(APITestCase):
    def test_auth_required(self):
        url = reverse("api:form-logics-list")

        response = self.client.post(url)

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

    def test_list_and_filter_form_logic(self):
        user = SuperUserFactory.create(username="test", password="test")
        form1 = FormFactory.create()
        form2 = FormFactory.create()

        FormLogicFactory.create(form=form1)
        FormLogicFactory.create(form=form2)

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
            "order": 0,
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
            "order": 0,
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
            "order": 0,
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
            "order": 0,
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
            "order": 0,
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
                    "order": 0,
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
            "order": 0,
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
            "order": 0,
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
            "order": 1,
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
            "order": 0,
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
            "order": 0,
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
            "order": 0,
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
            "order": 0,
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
            "order": 0,
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
            "order": 0,
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
            "order": 0,
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
            "order": 0,
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
            "order": 0,
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

    def test_cant_have_empty_variable_in_variable_action(self):
        user = SuperUserFactory.create()
        self.client.force_authenticate(user=user)
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "number",
                        "key": "nLargeBoxes",
                    },
                    {
                        "type": "number",
                        "key": "nGiganticBoxes",
                    },
                ]
            },
        )

        form_url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        form_logic_data = {
            "form": f"http://testserver{form_url}",
            "order": 0,
            "json_logic_trigger": {
                "and": [
                    {
                        "!=": [
                            {"var": "nLargeBoxes"},
                            None,
                        ]
                    },
                    {
                        "!=": [
                            {"var": "nGiganticBoxes"},
                            None,
                        ]
                    },
                ]
            },
            "actions": [
                {
                    "variable": "",  # Empty Variable
                    "action": {
                        "name": "Sum boxes",
                        "type": "variable",
                        "value": {
                            "+": [{"var": "nLargeBoxes"}, {"var": "nGiganticBoxes"}]
                        },
                    },
                }
            ],
            "is_advanced": False,
        }
        url = reverse("api:form-logics-list")

        response = self.client.post(url, data=form_logic_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            "actions.0.variable", response.json()["invalidParams"][0]["name"]
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
            "order": 0,
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
            "order": 0,
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

    def test_create_form_logic_with_trigger_from_step(self):
        user = SuperUserFactory.create(username="test", password="test")
        self.client.force_authenticate(user=user)
        form1, form2 = FormFactory.create_batch(2)
        step1 = FormStepFactory.create(
            form=form1,
            form_definition__configuration={
                "components": [{"type": "textfield", "key": "c1"}]
            },
        )
        unrelated_step = FormStepFactory.create(
            form=form2,
            form_definition__configuration={
                "components": [{"type": "textfield", "key": "c2"}]
            },
        )
        _form_logic_data = {
            "form": f"http://testserver{reverse('api:form-detail', kwargs={'uuid_or_slug': form1.uuid})}",
            "order": 0,
            "json_logic_trigger": {
                "==": [
                    {"var": "c1"},
                    "hide step 1",
                ]
            },
            "actions": [],
        }

        with self.subTest("Create logic rule with trigger_from_step set"):
            step1_path = reverse(
                "api:form-steps-detail",
                kwargs={"form_uuid_or_slug": form1.uuid, "uuid": step1.uuid},
            )
            data = {
                **_form_logic_data,
                "triggerFromStep": f"http://testserver{step1_path}",
            }

            response = self.client.post(reverse("api:form-logics-list"), data=data)

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        with self.subTest(
            "Reject logic rule with trigger_from_step belonging to another form"
        ):
            step2_path = reverse(
                "api:form-steps-detail",
                kwargs={"form_uuid_or_slug": form2.uuid, "uuid": unrelated_step.uuid},
            )
            data = {
                **_form_logic_data,
                "triggerFromStep": f"http://testserver{step2_path}",
            }

            response = self.client.post(reverse("api:form-logics-list"), data=data)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(
                response.data["invalid_params"][0]["name"], "triggerFromStep"
            )
            self.assertEqual(response.data["invalid_params"][0]["code"], "invalid")


def copy_func(f):
    """From https://stackoverflow.com/a/13503277"""
    g = types.FunctionType(
        f.__code__,
        f.__globals__,
        name=f.__name__,
        argdefs=f.__defaults__,
        closure=f.__closure__,
    )
    g = functools.update_wrapper(g, f)
    g.__kwdefaults__ = f.__kwdefaults__
    return g


class FormLogicTransactionTests(APITransactionTestCase):
    @skip(
        "This test cannot complete/pass when row-level locking is used which is the solution for the problem."
    )
    def test_reorder_logic_rules(self):
        user = SuperUserFactory.create()
        self.client.force_authenticate(user=user)
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "component",
                    }
                ]
            },
        )
        # create some existing rules, we'll use patch requests to only modify the order
        common_kwargs = {
            "json_logic_trigger": {"==": [{"var": "component"}, "1"]},
            "form": form,
        }
        fl1 = FormLogicFactory.create(order=0, **common_kwargs)
        fl2 = FormLogicFactory.create(order=1, **common_kwargs)
        fl3 = FormLogicFactory.create(order=2, **common_kwargs)

        # make a couple of requests in parallel, simulating the UI firing multiple
        # API calls shortly after each other.
        #
        # django-ordered-model works by:
        #
        # 1. first update all the records in an UPDATE query that would be moved around
        #    by setting the order of a particular record
        # 2. then set the new order value of the record and save.
        #
        # Without transactions:
        #
        # There is a race condition here that multiple threads/requests can arrive at
        # the same time before any UPDATE queries are finished. This causes them to
        # build update queries based on record.order which is no longer up to date with
        # the actual state in the database because of one of the updates going through.
        #
        # This is not guaranteed - very often it goes right by coincidence, but
        # sometimes the python code acts on stale data.
        #
        # The setup here reproduces that - we have 3 calls to set the order, but we mimick
        # the following order of database operations (all start with the same view of
        # data!):
        #
        # 1. FL2 -> 0: update other records. This results in FL1: 1, FL2: 1, FL3: 2
        # 2. FL3 -> 1: update other records. This results in FL1: 2, FL2: 2, FL3: 2
        # 3. FL2 -> 0: set FL1.order = 0. This results in FL1: 2, FL2: 0, FL3: 2
        # 4. FL3 -> 1: set FL3.order = 1. This results in FL1: 2, FL2: 0, FL3: 1
        # 5. FL1 -> 2: update other records: This results in FL1: 1, FL2: 0, FL3: 0
        # 6. FL1 -> 2: set FL1.order = 2. This results in FL1: 2, FL2: 0, FL3: 0
        #
        # Where the expected outcomde would be FL1: 2, FL2: 0, FL3: 1 instead.
        # Note that 2. and 3. can be interchanged, the end result is the same.
        #
        # NOTE: Uncomment the print debugging to see the what happens in which order
        # because # of the thread orchestration, as this is hard to grasp.

        print(fl1, fl2, fl3)

        # thread-unsafe dict to coordinate thread mock delays
        shared_state = {}

        # create a real copy of the existing implementation because we'll mock it later
        # to add delays.
        real_update = copy_func(FormLogic.objects.all().update)

        def queryset_update(self, **kwargs):
            """
            Introduce delays to simulate the race conditions.
            """
            # figure out which form_logic we are updating for from the queryset itself
            if list(self) == [fl2, fl3]:
                form_logic = fl1
            elif list(self) == [fl1]:
                form_logic = fl2
            elif list(self) == [fl2]:
                form_logic = fl3
            else:
                raise Exception("Unexpected filter query")

            # add a delay so that all threads are definitely looking at the initial
            # ordering before any update queries are allowed
            sleep(0.1)

            # FL2 update goes first, this is 1. described above
            if form_logic == fl2:
                pass
            # other updates must wait
            elif form_logic == fl3:
                while "FL2_UPDATE_QUERY" not in shared_state:
                    sleep(0.1)
            elif form_logic == fl1:
                # FL1 update query may only run after FL3 record was saved. This is
                # 4. and 5. above.
                while "FL3_RECORD_SAVE" not in shared_state:
                    sleep(0.1)

                # allow some time for the FL3 record save to actually persist
                sleep(0.1)

            print(shared_state)

            result = real_update(self, **kwargs)

            # track the state
            if form_logic == fl1:
                shared_state["FL1_UPDATE_QUERY"] = True
            elif form_logic == fl2:
                shared_state["FL2_UPDATE_QUERY"] = True
            elif form_logic == fl3:
                shared_state["FL3_UPDATE_QUERY"] = True

            # process wait events AFTER the update
            if form_logic == fl1:
                shared_state["FL1_RECORD_SAVE"] = True
            elif form_logic == fl2:
                # NOTE: when using select_for_update, a thread needs to complete
                # before others can run and this while look blocks that, leading
                # to deadlocks (which don't happen in the application!)
                # This doesn't make any difference for our test since FL2 from step
                # 3 onwards always ends up with order 0.
                # # FL2 may progress once FL3 update is completed, this is 2. above.
                # # it then continues to the instance save.
                # while "FL3_UPDATE_QUERY" not in shared_state:
                #     sleep(0.1)
                shared_state["FL2_RECORD_SAVE"] = True
            elif form_logic == fl3:
                shared_state["FL3_RECORD_SAVE"] = True

            print(shared_state)

            return result

        def _thread(form_logic, new_order):
            endpoint = reverse(
                "api:form-logics-detail", kwargs={"uuid": form_logic.uuid}
            )
            with patch(
                "ordered_model.models.OrderedModelQuerySet.update", queryset_update
            ):
                response = self.client.patch(endpoint, {"order": new_order})

            close_old_connections()
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        threads = [
            Thread(target=_thread, args=(fl2, 0)),
            Thread(target=_thread, args=(fl3, 1)),
            Thread(target=_thread, args=(fl1, 2)),
        ]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # check that the race conditions are not a problem and the API endpoints
        # are idempotent
        fl1.refresh_from_db()
        fl2.refresh_from_db()
        fl3.refresh_from_db()

        self.assertEqual(fl1.order, 2)
        self.assertEqual(fl2.order, 0)
        self.assertEqual(fl3.order, 1)

    def test_reorder_logic_rules_without_mocking(self):
        user = SuperUserFactory.create()
        self.client.force_authenticate(user=user)
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "component",
                    }
                ]
            },
        )
        # create some existing rules, we'll use patch requests to only modify the order
        common_kwargs = {
            "json_logic_trigger": {"==": [{"var": "component"}, "1"]},
            "form": form,
        }
        fl1 = FormLogicFactory.create(order=0, **common_kwargs)
        fl2 = FormLogicFactory.create(order=1, **common_kwargs)
        fl3 = FormLogicFactory.create(order=2, **common_kwargs)

        def _thread(form_logic, new_order):
            endpoint = reverse(
                "api:form-logics-detail", kwargs={"uuid": form_logic.uuid}
            )
            response = self.client.patch(endpoint, {"order": new_order})

            close_old_connections()
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        threads = [
            Thread(target=_thread, args=(fl2, 0)),
            Thread(target=_thread, args=(fl3, 1)),
            Thread(target=_thread, args=(fl1, 2)),
        ]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # check that the race conditions are not a problem and the API endpoints
        # are idempotent
        fl1.refresh_from_db()
        fl2.refresh_from_db()
        fl3.refresh_from_db()

        self.assertEqual(fl1.order, 2)
        self.assertEqual(fl2.order, 0)
        self.assertEqual(fl3.order, 1)
