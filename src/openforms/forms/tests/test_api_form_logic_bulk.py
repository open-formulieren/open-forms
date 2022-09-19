from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import SuperUserFactory, UserFactory

from ..models import FormLogic
from .factories import FormFactory, FormLogicFactory, FormStepFactory


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

    def test_cant_have_empty_form_step_in_mark_step_as_not_applicable(self):
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
        ]
        url = reverse("api:form-logic-rules", kwargs={"uuid_or_slug": form.uuid})

        response = self.client.put(url, data=form_logic_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            "0.actions.0.formStep", response.json()["invalidParams"][0]["name"]
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
