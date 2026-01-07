import uuid

from django.test import override_settings
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import SuperUserFactory, UserFactory
from openforms.variables.constants import FormVariableDataTypes, FormVariableSources

from ..constants import LogicActionTypes
from ..models import FormLogic
from .factories import (
    FormFactory,
    FormLogicFactory,
    FormStepFactory,
    FormVariableFactory,
)


class FormLogicAPITests(APITestCase):
    def test_auth_required(self):
        form = FormFactory.create()
        url = reverse("api:form-logic-rules", kwargs={"uuid_or_slug": form.uuid})

        response = self.client.post(url)

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

    def test_staff_required(self):
        # add the permissions to verify we specifically check is_staff
        user = UserFactory.create(
            is_staff=False, user_permissions=["change_form", "view_form"]
        )
        form = FormFactory.create()
        url = reverse("api:form-logic-rules", kwargs={"uuid_or_slug": form.uuid})

        self.client.force_authenticate(user=user)
        response = self.client.put(url)

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_list_form_logic(self):
        user = SuperUserFactory.create(username="test", password="test")
        form1 = FormFactory.create()
        form2 = FormFactory.create()

        FormLogicFactory.create(form=form1)
        FormLogicFactory.create(form=form2)

        self.client.force_authenticate(user)

        url = reverse("api:form-logic-rules", kwargs={"uuid_or_slug": form1.uuid})
        response = self.client.get(url)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        response_data = response.json()

        self.assertEqual(1, len(response_data))

    def test_list_form_logic_with_soft_deleted_form(self):
        user = SuperUserFactory.create(username="test", password="test")
        form1 = FormFactory.create(deleted_=True)

        FormLogicFactory.create(form=form1)

        self.client.force_authenticate(user)

        url = reverse("api:form-logic-rules", kwargs={"uuid_or_slug": form1.uuid})
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
        FormLogicFactory.create(form=form)  # existing rule will be replaced

        form_logic_data = [
            {
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
        ]

        self.client.force_authenticate(user=user)
        url = reverse("api:form-logic-rules", kwargs={"uuid_or_slug": form.uuid})
        response = self.client.put(url, data=form_logic_data)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

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

        form_logic_data = [
            {
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
        ]

        self.client.force_authenticate(user=user)
        url = reverse("api:form-logic-rules", kwargs={"uuid_or_slug": form.uuid})
        response = self.client.put(url, data=form_logic_data)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

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

        form_logic_data = [
            {
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
        ]

        self.client.force_authenticate(user=user)
        url = reverse("api:form-logic-rules", kwargs={"uuid_or_slug": form.uuid})
        response = self.client.put(url, data=form_logic_data)

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

        form_logic_data = [
            {
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
        ]

        self.client.force_authenticate(user=user)
        url = reverse("api:form-logic-rules", kwargs={"uuid_or_slug": form.uuid})
        response = self.client.put(url, data=form_logic_data)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_delete_form_logic(self):
        user = SuperUserFactory.create(username="test", password="test")
        form = FormFactory.create()

        FormLogicFactory.create(
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
        url = reverse("api:form-logic-rules", kwargs={"uuid_or_slug": form.uuid})
        response = self.client.put(url, data=[])

        self.assertEqual(status.HTTP_200_OK, response.status_code)
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

        form_logic_data = [
            {
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
        ]

        self.client.force_authenticate(user=user)
        url = reverse("api:form-logic-rules", kwargs={"uuid_or_slug": form.uuid})
        response = self.client.put(url, data=form_logic_data)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual(
            "0.jsonLogicTrigger", response.json()["invalidParams"][0]["name"]
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
        url = reverse("api:form-logic-rules", kwargs={"uuid_or_slug": form.uuid})
        invalid = [
            {"==": [1, 1]},
            {"==": [{"date": "2022-01-12"}, {"-": [{"today": []}, {"rdelta": [18]}]}]},
        ]

        for trigger in invalid:
            with self.subTest(trigger=trigger):
                form_logic_data = [
                    {
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
                ]

                response = self.client.put(url, data=form_logic_data)

                self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
                self.assertEqual(
                    "0.jsonLogicTrigger", response.json()["invalidParams"][0]["name"]
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

        form_logic_data = [
            {
                "form": f"http://testserver{reverse('api:form-detail', kwargs={'uuid_or_slug': form.uuid})}",
                "order": 0,
                "json_logic_trigger": {"==": [{"var": "name"}, "John"]},
                "actions": [
                    {
                        "formStep": "",
                        "variable": "surname",
                        "action": {
                            "type": "variable",
                            "value": "foo",
                        },
                    }
                ],
            }
        ]

        self.client.force_authenticate(user=user)
        url = reverse("api:form-logic-rules", kwargs={"uuid_or_slug": form.uuid})
        response = self.client.put(url, data=form_logic_data)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

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

        form_logic_data = [
            {
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
            },
            {
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
            },
        ]

        self.client.force_authenticate(user=user)
        url = reverse("api:form-logic-rules", kwargs={"uuid_or_slug": form.uuid})

        response = self.client.put(url, data=form_logic_data)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(2, FormLogic.objects.filter(form=form).count())

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
        form_logic_data = [
            {
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
        ]
        url = reverse("api:form-logic-rules", kwargs={"uuid_or_slug": form.uuid})

        response = self.client.put(url, data=form_logic_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_logic_rule_skip_trigger_validation(self):
        """
        Assert that the trigger validation is skipped if dependent data is missing.
        """
        user = SuperUserFactory.create()
        self.client.force_authenticate(user=user)
        form_logic_data = [
            {
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
        ]
        form = FormFactory.create()
        url = reverse("api:form-logic-rules", kwargs={"uuid_or_slug": form.uuid})

        response = self.client.put(url, data=form_logic_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual("0.form", response.json()["invalidParams"][0]["name"])

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
        form_logic_data = [
            {
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
        ]
        url = reverse("api:form-logic-rules", kwargs={"uuid_or_slug": form.uuid})

        response = self.client.put(url, data=form_logic_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            "0.jsonLogicTrigger", response.json()["invalidParams"][0]["name"]
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
        form_logic_data = [
            {
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
        ]
        url = reverse("api:form-logic-rules", kwargs={"uuid_or_slug": form.uuid})

        response = self.client.put(url, data=form_logic_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            "0.jsonLogicTrigger", response.json()["invalidParams"][0]["name"]
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
        form_logic_data = [
            {
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
        ]
        url = reverse("api:form-logic-rules", kwargs={"uuid_or_slug": form.uuid})

        response = self.client.put(url, data=form_logic_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            "0.jsonLogicTrigger", response.json()["invalidParams"][0]["name"]
        )

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
        form_logic_data = [
            {
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
        ]
        url = reverse("api:form-logic-rules", kwargs={"uuid_or_slug": form.uuid})

        response = self.client.put(url, data=form_logic_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            "0.actions.0.component", response.json()["invalidParams"][0]["name"]
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
        form_logic_data = [
            {
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
        ]
        url = reverse("api:form-logic-rules", kwargs={"uuid_or_slug": form.uuid})

        response = self.client.put(url, data=form_logic_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            "0.actions.0.variable", response.json()["invalidParams"][0]["name"]
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
        form_logic_data = [
            {
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
        ]
        url = reverse("api:form-logic-rules", kwargs={"uuid_or_slug": form.uuid})

        response = self.client.put(url, data=form_logic_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            "0.actions.0.action.state", response.json()["invalidParams"][0]["name"]
        )
        self.assertEqual("blank", response.json()["invalidParams"][0]["code"])

    def test_empty_form_step_uuid_in_relevant_actions(self):
        """
        Ensure a validation error is raised when the "step applicable", "step not
        applicable", and "disable next" actions have an empty form step uuid.
        """
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
        form_logic_data = [
            {
                "form": f"http://testserver{form_url}",
                "order": 0,
                "json_logic_trigger": {"==": [{"var": "text1"}, {"var": "text2"}]},
                "actions": [
                    {
                        "formStepUuid": "",  # Empty form step uuid
                        "action": {"type": "step-not-applicable"},
                    },
                    {
                        "formStepUuid": "",  # Empty form step uuid
                        "action": {"type": "step-applicable"},
                    },
                    {
                        "formStepUuid": "",  # Empty form step uuid
                        "action": {"type": "disable-next"},
                    },
                ],
                "is_advanced": False,
            }
        ]
        url = reverse("api:form-logic-rules", kwargs={"uuid_or_slug": form.uuid})

        response = self.client.put(url, data=form_logic_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        invalid_params = response.json()["invalidParams"]
        for i, action_type in enumerate(
            ("step-not-applicable", "step-applicable", "disable-next")
        ):
            with self.subTest(action_type=action_type):
                self.assertEqual(
                    f"0.actions.{i}.formStepUuid", invalid_params[i]["name"]
                )
                self.assertEqual("blank", invalid_params[i]["code"])

    def test_can_null_form_step_uuid(self):
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
        form_logic_data = [
            {
                "form": f"http://testserver{form_url}",
                "order": 0,
                "json_logic_trigger": {"==": [{"var": "text1"}, "test"]},
                "actions": [
                    {
                        "formStepUuid": None,
                        "variable": "text2",
                        "action": {
                            "type": "variable",
                            "value": "test2",
                        },
                    }
                ],
                "is_advanced": False,
            }
        ]
        url = reverse("api:form-logic-rules", kwargs={"uuid_or_slug": form.uuid})

        response = self.client.put(url, data=form_logic_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_mark_step_as_not_applicable_action_works_with_uuid(self):
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
        form_step = form.formstep_set.first()

        form_url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        form_logic_data = [
            {
                "form": f"http://testserver{form_url}",
                "order": 0,
                "json_logic_trigger": {"==": [{"var": "text1"}, {"var": "text2"}]},
                "actions": [
                    {
                        "formStepUuid": f"{form_step.uuid}",
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
        ]
        url = reverse("api:form-logic-rules", kwargs={"uuid_or_slug": form.uuid})

        response = self.client.put(url, data=form_logic_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

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
        _form_logic_rule_data = {
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
            data = [
                {
                    **_form_logic_rule_data,
                    "triggerFromStep": f"http://testserver{step1_path}",
                }
            ]

            url = reverse("api:form-logic-rules", kwargs={"uuid_or_slug": form1.uuid})
            response = self.client.put(url, data=data)

            self.assertEqual(response.status_code, status.HTTP_200_OK)

        with self.subTest(
            "Reject logic rule with trigger_from_step belonging to another form"
        ):
            step2_path = reverse(
                "api:form-steps-detail",
                kwargs={"form_uuid_or_slug": form2.uuid, "uuid": unrelated_step.uuid},
            )
            data = [
                {
                    **_form_logic_rule_data,
                    "triggerFromStep": f"http://testserver{step2_path}",
                }
            ]

            url = reverse("api:form-logic-rules", kwargs={"uuid_or_slug": form1.uuid})
            response = self.client.put(url, data=data)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(
                response.data["invalid_params"][0]["name"], "0.triggerFromStep"
            )
            self.assertEqual(response.data["invalid_params"][0]["code"], "invalid")

    def test_create_form_logic_doesnt_crash(self):
        user = SuperUserFactory.create(username="test", password="test")
        form = FormFactory.create()
        FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "testFieldA",
                    }
                ]
            },
        )
        FormLogicFactory.create(form=form)

        form_logic_data = [
            {
                "form": f"http://testserver{reverse('api:form-detail', kwargs={'uuid_or_slug': form.uuid})}",
                "order": 0,
                "json_logic_trigger": {
                    "==": [
                        {"var": "testFieldA"},
                        "value",
                        "invalid",  # Invalid trigger
                    ]
                },
                "actions": [
                    {
                        "action": {
                            "type": "disable-next",
                        },
                    }
                ],
            }
        ]

        self.client.force_authenticate(user=user)
        url = reverse("api:form-logic-rules", kwargs={"uuid_or_slug": form.uuid})
        response = self.client.put(url, data=form_logic_data)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual(
            "0.jsonLogicTrigger", response.json()["invalidParams"][0]["name"]
        )
        self.assertEqual("invalid", response.json()["invalidParams"][0]["code"])

    def test_create_form_logic_with_bad_variable_reference(self):
        user = SuperUserFactory.create(username="test", password="test")
        self.client.force_authenticate(user=user)
        form = FormFactory.create(generate_minimal_setup=True)

        url = reverse("api:form-logic-rules", kwargs={"uuid_or_slug": form.uuid})
        varname = str(uuid.uuid4())  # this will never match a variable
        form_logic_data = [
            {
                "form": f"http://testserver{reverse('api:form-detail', kwargs={'uuid_or_slug': form.uuid})}",
                "order": 0,
                "is_advanced": True,
                "json_logic_trigger": True,
                "actions": [
                    {
                        "formStep": "",
                        "variable": varname,
                        "action": {
                            "type": "variable",
                            "value": 3,
                        },
                    }
                ],
            }
        ]

        response = self.client.put(url, data=form_logic_data)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        errors = response.json()["invalidParams"][0]
        self.assertEqual(errors["name"], "0.actions.0.variable")

    def test_create_form_logic_with_primitive_in_action(self):
        user = SuperUserFactory.create(username="test", password="test")
        form = FormFactory.create()
        FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "number",
                        "key": "testNumber",
                    }
                ]
            },
        )
        FormLogicFactory.create(form=form)

        form_logic_data = [
            {
                "form": f"http://testserver{reverse('api:form-detail', kwargs={'uuid_or_slug': form.uuid})}",
                "order": 0,
                "is_advanced": True,
                "json_logic_trigger": {"!!": [True]},
                "actions": [
                    {
                        "formStep": "",
                        "variable": "testNumber",
                        "action": {
                            "type": "variable",
                            "value": 3,
                        },
                    }
                ],
            }
        ]

        self.client.force_authenticate(user=user)
        url = reverse("api:form-logic-rules", kwargs={"uuid_or_slug": form.uuid})
        response = self.client.put(url, data=form_logic_data)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

    @override_settings(MIDDLEWARE=[])  # cut out some irrelevant queries
    def test_performance_validation_bulk_create_data(self):
        """
        Assert that a constant number of queries are performed on logic bulk create.

        Instead of individually re-validating the same data over and over again, or
        querying every individual form variable, caches must be used so that the form
        data is only retrieved once. This enables scaling the amount of data inside
        the bulk create without running into O(n) or worse complexity.
        """
        user = SuperUserFactory.create()
        self.client.force_authenticate(user=user)
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {"type": "textfield", "key": "variable1"},
                    {"type": "textfield", "key": "variable2"},
                    {"type": "textfield", "key": "variable3"},
                ]
            },
        )
        FormVariableFactory.create(form=form, key="variable4", user_defined=True)
        FormVariableFactory.create(form=form, key="variable5", user_defined=True)
        form_path = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        url = reverse("api:form-logic-rules", kwargs={"uuid_or_slug": form.uuid})
        form_logic_data = [
            {
                "form": f"http://testserver{form_path}",
                "order": 0,
                "json_logic_trigger": {
                    "and": [
                        {"var": "variable1"},
                        {"var": "variable2"},
                        {"var": "variable3"},
                    ]
                },
                "actions": [],
            },
            {
                "form": f"http://testserver{form_path}",
                "order": 1,
                "json_logic_trigger": {
                    "and": [
                        {"var": "variable4"},
                        {"var": "variable5"},
                    ]
                },
                "actions": [],
            },
        ]

        # 1. transaction SAVEPOINT
        # 2. Fetch the form (from UUID param in endpoint)
        # 3. Delete all the existing logic rules (to be replaced)
        # 4. Look up all the form steps for the form (once)
        # 5. Look up all the form variables for the form (once)
        # 6. Get max order within form (from ordered_model.models.OrderedModelQuerySet.bulk_create)
        # 7. Bulk insert logic rules
        # 8. transaction RELEASE SAVEPOINT
        with self.assertNumQueries(8):
            response = self.client.put(url, data=form_logic_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(FormLogic.objects.count(), 2)

    def test_create_rule_with_evaluate_dmn_action(self):
        user = SuperUserFactory.create(username="test", password="test")
        form = FormFactory.create()
        FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "number",
                        "key": "age",
                    },
                    {
                        "type": "number",
                        "key": "income",
                    },
                ]
            },
        )
        FormVariableFactory.create(
            form=form,
            source=FormVariableSources.user_defined,
            key="canApply",
            data_type=FormVariableDataTypes.boolean,
        )

        form_logic_data = [
            {
                "form": f"http://testserver{reverse('api:form-detail', kwargs={'uuid_or_slug': form.uuid})}",
                "order": 0,
                "is_advanced": True,
                "json_logic_trigger": True,
                "actions": [
                    {
                        "action": {
                            "type": LogicActionTypes.evaluate_dmn,
                            "config": {
                                "plugin_id": "camunda7",
                                "decision_definition_id": "some-id",
                                "decision_definition_version": "1",
                                "input_mapping": [
                                    {"form_variable": "age", "dmn_variable": "ageDMN"},
                                    {
                                        "form_variable": "income",
                                        "dmn_variable": "incomeDMN",
                                    },
                                ],
                                "output_mapping": [
                                    {
                                        "form_variable": "canApply",
                                        "dmn_variable": "canApplyDMN",
                                    }
                                ],
                            },
                        },
                    }
                ],
            }
        ]

        self.client.force_authenticate(user=user)
        url = reverse("api:form-logic-rules", kwargs={"uuid_or_slug": form.uuid})
        response = self.client.put(url, data=form_logic_data)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        new_rule = FormLogic.objects.get(form=form, order=0)

        self.assertEqual(
            new_rule.actions[0]["action"]["type"], LogicActionTypes.evaluate_dmn
        )
        self.assertEqual(
            new_rule.actions[0]["action"]["config"],
            {
                "plugin_id": "camunda7",
                "decision_definition_id": "some-id",
                "decision_definition_version": "1",
                "input_mapping": [
                    {"form_variable": "age", "dmn_variable": "ageDMN"},
                    {
                        "form_variable": "income",
                        "dmn_variable": "incomeDMN",
                    },
                ],
                "output_mapping": [
                    {"form_variable": "canApply", "dmn_variable": "canApplyDMN"}
                ],
            },
        )

    def test_create_rule_with_evaluate_dmn_action_empty_config(self):
        user = SuperUserFactory.create(username="test", password="test")
        form = FormFactory.create()
        FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "number",
                        "key": "age",
                    },
                    {
                        "type": "number",
                        "key": "income",
                    },
                ]
            },
        )
        FormVariableFactory.create(
            form=form,
            source=FormVariableSources.user_defined,
            key="canApply",
            data_type=FormVariableDataTypes.boolean,
        )

        form_logic_data = [
            {
                "form": f"http://testserver{reverse('api:form-detail', kwargs={'uuid_or_slug': form.uuid})}",
                "order": 0,
                "is_advanced": True,
                "json_logic_trigger": True,
                "actions": [
                    {
                        "action": {
                            "type": LogicActionTypes.evaluate_dmn,
                            "config": {},
                        },
                    },
                    {
                        "action": {
                            "type": LogicActionTypes.evaluate_dmn,
                            "config": {
                                "plugin_id": "",
                                "decision_definition_id": "",
                                "decision_definition_version": "",
                                "input_mapping": [],
                                "output_mapping": [],
                            },
                        },
                    },
                    {
                        "action": {
                            "type": LogicActionTypes.evaluate_dmn,
                        },
                    },
                ],
            }
        ]

        self.client.force_authenticate(user=user)
        url = reverse("api:form-logic-rules", kwargs={"uuid_or_slug": form.uuid})
        response = self.client.put(url, data=form_logic_data)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

        data = response.json()

        self.assertEqual(data["invalidParams"][0]["code"], "required")
        self.assertEqual(
            data["invalidParams"][0]["name"], "0.actions.0.action.config.pluginId"
        )
        self.assertEqual(data["invalidParams"][1]["code"], "required")
        self.assertEqual(
            data["invalidParams"][1]["name"],
            "0.actions.0.action.config.decisionDefinitionId",
        )
        self.assertEqual(data["invalidParams"][2]["code"], "required")
        self.assertEqual(
            data["invalidParams"][2]["name"],
            "0.actions.0.action.config.inputMapping",
        )
        self.assertEqual(data["invalidParams"][3]["code"], "required")
        self.assertEqual(
            data["invalidParams"][3]["name"],
            "0.actions.0.action.config.outputMapping",
        )

        self.assertEqual(data["invalidParams"][4]["code"], "blank")
        self.assertEqual(
            data["invalidParams"][4]["name"], "0.actions.1.action.config.pluginId"
        )

        self.assertEqual(data["invalidParams"][5]["code"], "blank")
        self.assertEqual(
            data["invalidParams"][5]["name"],
            "0.actions.1.action.config.decisionDefinitionId",
        )

        self.assertEqual(data["invalidParams"][6]["code"], "required")
        self.assertEqual(data["invalidParams"][6]["name"], "0.actions.2.action.config")
