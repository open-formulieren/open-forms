from django.test import SimpleTestCase, TestCase

from openforms.forms.tests.factories import FormFactory

from ..json_logic import add_data_type_information
from ..tests.factories import SubmissionFactory


class AddDataTypeInformation(TestCase):
    def test_date_and_datetime(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "textfield",
                        "type": "textfield",
                        "label": "Textfield",
                    },
                    {
                        "key": "date",
                        "type": "date",
                        "label": "Date",
                    },
                    {
                        "key": "datetime",
                        "type": "datetime",
                        "label": "Datetime",
                    },
                ],
            },
        )
        submission = SubmissionFactory.create(form=form)
        state = submission.load_submission_value_variables_state()

        expression = {
            "or": [
                {"==": [{"var": "date"}, {"date": "2026-03-06"}]},
                {"==": [{"datetime": "2026-03-06T15:37:00"}, {"var": "datetime"}]},
                {"==": [{"var": "textfield"}, "foo"]},
            ]
        }
        result = add_data_type_information(expression, state)

        self.assertEqual(
            {
                "or": [
                    {"==": [{"date": [{"var": ["date"]}]}, {"date": ["2026-03-06"]}]},
                    {
                        "==": [
                            {"datetime": ["2026-03-06T15:37:00"]},
                            {"datetime": [{"var": ["datetime"]}]},
                        ]
                    },
                    {"==": [{"var": ["textfield"]}, "foo"]},
                ]
            },
            result,
        )

    def test_date_and_datetime_multiple(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "textfield",
                        "type": "textfield",
                        "label": "Textfield",
                        "multiple": True,
                    },
                    {
                        "key": "date",
                        "type": "date",
                        "label": "Date",
                        "multiple": True,
                    },
                    {
                        "key": "datetime",
                        "type": "datetime",
                        "label": "Datetime",
                        "multiple": True,
                    },
                ],
            },
        )
        submission = SubmissionFactory.create(form=form)
        state = submission.load_submission_value_variables_state()

        expression = {
            "or": [
                {"==": [{"var": "date"}, {"date": "2026-03-06"}]},
                {"==": [{"datetime": "2026-03-06T15:37:00"}, {"var": "datetime"}]},
                {"==": [{"var": "textfield"}, "foo"]},
            ]
        }
        result = add_data_type_information(expression, state)

        self.assertEqual(
            {
                "or": [
                    {"==": [{"date": [{"var": ["date"]}]}, {"date": ["2026-03-06"]}]},
                    {
                        "==": [
                            {"datetime": ["2026-03-06T15:37:00"]},
                            {"datetime": [{"var": ["datetime"]}]},
                        ]
                    },
                    {"==": [{"var": ["textfield"]}, "foo"]},
                ]
            },
            result,
        )

    def test_children(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "children",
                        "type": "children",
                        "label": "Children",
                    },
                ],
            },
        )
        submission = SubmissionFactory.create(form=form)
        state = submission.load_submission_value_variables_state()

        expression = {
            "or": [
                {"==": [{"var": "children.0.dateOfBirth"}, {"date": "2026-03-06"}]},
                {"==": [{"date": "2026-03-06"}, {"var": "children.1.dateOfBirth"}]},
                {"==": [{"var": "children.2.lastName"}, "Maertens"]},  # string
                {
                    "==": [
                        {"var": "children.dateOfBirth"},
                        {"datetime": "2026-03-06T15:37:00"},
                    ]
                },  # incorrect data access
                {
                    "==": [{"var": "children.0.nonExisting"}, "foo"]
                },  # non-existing field
            ]
        }
        result = add_data_type_information(expression, state)

        self.assertEqual(
            {
                "or": [
                    {
                        "==": [
                            {"date": [{"var": ["children.0.dateOfBirth"]}]},
                            {"date": ["2026-03-06"]},
                        ]
                    },
                    {
                        "==": [
                            {"date": ["2026-03-06"]},
                            {"date": [{"var": ["children.1.dateOfBirth"]}]},
                        ]
                    },
                    {"==": [{"var": ["children.2.lastName"]}, "Maertens"]},
                    {
                        "==": [
                            {"var": ["children.dateOfBirth"]},
                            {"datetime": ["2026-03-06T15:37:00"]},
                        ]
                    },
                    {
                        "==": [{"var": ["children.0.nonExisting"]}, "foo"]
                    },
                ]
            },
            result,
        )


from datetime import date

from json_logic import jsonLogic


class JsonLogicTests(SimpleTestCase):
    def test_asdf(self):

        result = jsonLogic(
            {"map": [{"var": "foo"}, {"+": [{"var": "a"}, {"duration": "P1M"}]}]},
            {"foo": [{"a": date(2020, 1, 1)}, {"a": date(2020, 1, 2)}]},
        )
        print(result)

    def test_map_for_multiple(self):
        result = jsonLogic(
            {"map": [{"var": "foo"}, {"date": {"var": "a"}}]},
            {"foo": [{"a": "2025-01-01"}, {"a": "2025-01-03"}]},
        )
        print(result)

    def test_date_on_array(self):
        result = jsonLogic(
            {"date": {"var": "foo"}},
            {"foo": ["2025-01-01", "2025-01-03"]},
        )
        print(result)
