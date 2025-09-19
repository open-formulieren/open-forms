from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase

from hypothesis import given
from hypothesis.extra.django import TestCase as HypothesisTestCase

from openforms.accounts.tests.factories import UserFactory
from openforms.authentication.contrib.digid.constants import DIGID_DEFAULT_LOA
from openforms.config.models.config import GlobalConfiguration
from openforms.tests.search_strategies import json_primitives
from openforms.variables.constants import FormVariableDataTypes, FormVariableSources

from ..api.datastructures import FormVariableWrapper
from ..api.serializers import FormSerializer
from ..api.serializers.logic.action_serializers import (
    LogicComponentActionSerializer,
    SynchronizeVariablesActionConfigSerializer,
)
from .factories import (
    FormFactory,
    FormRegistrationBackendFactory,
    FormStepFactory,
    FormVariableFactory,
)


class LogicComponentActionSerializerPropertyTest(HypothesisTestCase):
    @given(json_primitives())
    def test_date_format_validation_against_primitive_json_values(self, json_value):
        """Assert that serializer is invalid for random Primitive json data types
        (str, int, etc.) as logic action values for date variables
        """
        form = FormFactory.create()
        FormVariableFactory.create(
            source=FormVariableSources.user_defined,
            key="date_var",
            form=form,
            data_type=FormVariableDataTypes.date,
        )
        form_vars = FormVariableWrapper(form=form)

        serializer = LogicComponentActionSerializer(
            data={
                "variable": "date_var",
                "action": {
                    "type": "variable",
                    "value": json_value,
                },
            },
            context={"request": None, "form_variables": form_vars},
        )
        self.assertFalse(serializer.is_valid())


class LogicComponentActionSerializerTest(TestCase):
    def test_date_variable_with_non_trivial_json_trigger(self):
        """Check that valid JSON expressions are not ruled out by date format validation"""
        form = FormFactory.create()
        FormVariableFactory.create(
            source=FormVariableSources.user_defined,
            key="someDate",
            form=form,
            data_type=FormVariableDataTypes.date,
        )
        FormVariableFactory.create(
            source=FormVariableSources.user_defined,
            key="anotherDate",
            form=form,
            data_type=FormVariableDataTypes.date,
        )
        form_vars = FormVariableWrapper(form=form)

        serializer = LogicComponentActionSerializer(
            data={
                "json_logic_trigger": {
                    "==": [
                        {"var": "someDate"},
                        {},
                    ]
                },
                "variable": "anotherDate",
                "action": {
                    "type": "variable",
                    "value": {"var": "anotherDate"},
                },
            },
            context={"request": None, "form_variables": form_vars},
        )

        self.assertTrue(serializer.is_valid())

    def test_registration_backend_action_errors_no_value(self):
        form = FormFactory.create()
        context = {"request": None, "form_variables": FormVariableWrapper(form=form)}

        serializer = LogicComponentActionSerializer(
            data={
                "json_logic_trigger": False,
                "action": {
                    "type": "set-registration-backend",
                },
            },
            context=context,
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors["action"]["value"][0].code, "required")

    def test_invalid_action(self):
        form = FormFactory.create()
        context = {"request": None, "form_variables": FormVariableWrapper(form=form)}

        serializer = LogicComponentActionSerializer(
            data={
                "json_logic_trigger": False,
                "action": {
                    "type": "does-not-exist",
                },
            },
            context=context,
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors["action"]["type"][0].code, "invalid_choice")


class FormSerializerTest(TestCase):
    def setUp(self):
        super().setUp()
        self.addCleanup(GlobalConfiguration.clear_cache)

    def test_form_with_cosign(self):
        form_step = FormStepFactory.create(
            form__slug="form-with-cosign",
            form__authentication_backend="digid",
            form__authentication_backend_options={"loa": DIGID_DEFAULT_LOA},
            form_definition__configuration={
                "components": [
                    {
                        "key": "cosignField",
                        "label": "Cosign",
                        "type": "cosign",
                    }
                ]
            },
        )

        factory = RequestFactory()
        request = factory.get("/foo")
        request.user = UserFactory.create()

        serializer = FormSerializer(
            instance=form_step.form, context={"request": request}
        )
        cosign_login_options = serializer.data["cosign_login_options"]

        self.assertEqual(len(cosign_login_options), 1)
        self.assertEqual(cosign_login_options[0]["identifier"], "digid")

    @patch(
        "openforms.forms.api.serializers.form.GlobalConfiguration.get_solo",
        return_value=GlobalConfiguration(
            cosign_request_template="{{ form_name }} cosign request."
        ),
    )
    def test_form_without_cosign_link_used_in_email(self, mock_get_solo):
        form_step = FormStepFactory.create(
            form__slug="form-with-cosign",
            form__authentication_backend="digid",
            form__authentication_backend_options={"loa": DIGID_DEFAULT_LOA},
            form_definition__configuration={
                "components": [
                    {
                        "key": "cosignField",
                        "label": "Cosign",
                        "type": "cosign",
                    }
                ]
            },
        )
        factory = RequestFactory()
        request = factory.get("/foo")
        request.user = AnonymousUser()

        serializer = FormSerializer(
            instance=form_step.form, context={"request": request}
        )

        cosign_login_options = serializer.data["cosign_login_options"]
        self.assertEqual(len(cosign_login_options), 1)
        self.assertFalse(serializer.data["cosign_has_link_in_email"])

    @patch(
        "openforms.forms.api.serializers.form.GlobalConfiguration.get_solo",
        return_value=GlobalConfiguration(
            cosign_request_template="{{ form_url }} cosign request."
        ),
    )
    def test_form_with_cosign_link_used_in_email(self, mock_get_solo):
        form_step = FormStepFactory.create(
            form__slug="form-with-cosign",
            form__authentication_backend="digid",
            form__authentication_backend_options={"loa": DIGID_DEFAULT_LOA},
            form_definition__configuration={
                "components": [
                    {
                        "key": "cosignField",
                        "label": "Cosign",
                        "type": "cosign",
                    }
                ]
            },
        )
        factory = RequestFactory()
        request = factory.get("/foo")
        request.user = AnonymousUser()

        serializer = FormSerializer(
            instance=form_step.form, context={"request": request}
        )

        cosign_login_options = serializer.data["cosign_login_options"]
        self.assertEqual(len(cosign_login_options), 1)
        self.assertTrue(serializer.data["cosign_has_link_in_email"])

    def test_form_without_cosign(self):
        form_step = FormStepFactory.create(
            form__slug="form-without-cosign",
            form__authentication_backend="digid",
            form__authentication_backend_options={"loa": DIGID_DEFAULT_LOA},
            form_definition__configuration={
                "components": [
                    {
                        "key": "notCosign",
                        "label": "Not Cosign",
                        "type": "textfield",
                    }
                ]
            },
        )

        factory = RequestFactory()
        request = factory.get("/foo")
        request.user = UserFactory.create()

        serializer = FormSerializer(
            instance=form_step.form, context={"request": request}
        )
        cosign_login_options = serializer.data["cosign_login_options"]

        self.assertEqual(cosign_login_options, [])

    def test_patching_registrations_deleting_the_first(self):
        form = FormFactory.create()
        FormRegistrationBackendFactory.create(
            form=form,
            key="backend1",
            name="#1",
            backend="email",
            options={"to_emails": ["you@example.com"]},
        )
        FormRegistrationBackendFactory.create(
            form=form,
            key="backend2",
            name="#2",
            backend="email",
            options={"to_emails": ["me@example.com"]},
        )
        context = {"request": None}
        data = FormSerializer(context=context).to_representation(form)

        # delete the first line
        assert data["registration_backends"][0]["key"] == "backend1"
        del data["registration_backends"][0]

        serializer = FormSerializer(instance=form, context=context, data=data)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        form.refresh_from_db()

        self.assertEqual(form.registration_backends.count(), 1)
        backend = form.registration_backends.first()
        self.assertEqual(backend.key, "backend2")
        self.assertEqual(backend.name, "#2")
        self.assertEqual(backend.backend, "email")
        self.assertEqual(backend.options["to_emails"], ["me@example.com"])

    def test_patching_registrations_with_a_booboo(self):
        form = FormFactory.create()
        FormRegistrationBackendFactory.create(
            form=form,
            key="backend1",
            name="#1",
            backend="email",
            options={"to_emails": ["you@example.com"]},
        )
        FormRegistrationBackendFactory.create(
            form=form,
            key="backend2",
            name="#2",
            backend="email",
            options={"to_emails": ["me@example.com"]},
        )
        context = {"request": None}
        data = FormSerializer(context=context).to_representation(form)

        all_the_same = 3 * [
            {
                "key": "backend5",
                "name": "#5",
                "backend": "email",
                "options": {"to_emails": ["booboo@example.com", "yogi@example.com"]},
            }
        ]

        data["registration_backends"] = all_the_same

        serializer = FormSerializer(instance=form, context=context, data=data)
        with self.assertRaises(Exception):
            self.assertTrue(serializer.is_valid())
            serializer.save()

        form.refresh_from_db()

        # assert no changes made
        self.assertEqual(form.registration_backends.count(), 2)
        backend1, backend2 = form.registration_backends.all()
        self.assertEqual(backend1.key, "backend1")
        self.assertEqual(backend1.name, "#1")
        self.assertEqual(backend1.backend, "email")
        self.assertEqual(backend1.options["to_emails"], ["you@example.com"])
        self.assertEqual(backend2.key, "backend2")
        self.assertEqual(backend2.name, "#2")
        self.assertEqual(backend2.backend, "email")
        self.assertEqual(backend2.options["to_emails"], ["me@example.com"])

    def test_submission_limit_method_field(self):
        context = {"request": None}

        with self.subTest("submission_limit equal to submission_counter"):
            form = FormFactory.create(submission_limit=2, submission_counter=2)
            data = FormSerializer(instance=form, context=context).data

            self.assertTrue(data["submission_limit_reached"])
        with self.subTest("submission_max_allowed bigger than submission_counter"):
            form = FormFactory.create(submission_limit=2, submission_counter=1)
            data = FormSerializer(instance=form, context=context).data

            self.assertFalse(data["submission_limit_reached"])
        with self.subTest("submission_max_allowed smaller than submission_counter"):
            form = FormFactory.create(submission_limit=1, submission_counter=2)
            data = FormSerializer(instance=form, context=context).data

            self.assertTrue(data["submission_limit_reached"])


class SynchronizeVariablesActionConfigSerializerTest(TestCase):
    def test_valid_mappings(self):
        data = {
            "source_variable": "source",
            "destination_variable": "destination",
            "identifier_variable": "bsn",
            "data_mappings": [
                {"component_key": "bsn", "property": "value1"},
                {"component_key": "key2", "property": "value2"},
            ],
        }
        serializer = SynchronizeVariablesActionConfigSerializer(data=data)

        self.assertTrue(serializer.is_valid())

    def test_no_mappings_defined(self):
        data = {
            "source_variable": "source",
            "destination_variable": "destination",
            "identifier_variable": "bsn",
            "data_mappings": [],
        }
        serializer = SynchronizeVariablesActionConfigSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("data_mappings", serializer.errors)

    def test_duplicate_mappings(self):
        data = {
            "source_variable": "source",
            "destination_variable": "destination",
            "identifier_variable": "bsn",
            "data_mappings": [
                {"component_key": "bsn", "property": "value1"},
                {"component_key": "bsn", "property": "value2"},
            ],
        }
        serializer = SynchronizeVariablesActionConfigSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("data_mappings", serializer.errors)

    def test_no_mapping_for_the_identifier(self):
        data = {
            "source_variable": "source",
            "destination_variable": "destination",
            "source_component_type": "children",
            "identifier_variable": "bsn",
            "data_mappings": [
                {"component_key": "key1", "property": "value2"},
            ],
        }
        serializer = SynchronizeVariablesActionConfigSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("data_mappings", serializer.errors)
