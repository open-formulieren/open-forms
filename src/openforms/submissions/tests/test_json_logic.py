from django.test import TestCase

from openforms.forms.tests.factories import FormFactory

from ..json_logic import add_data_type_information
from .factories import SubmissionFactory


class AddDataTypeInformationTests(TestCase):
    maxDiff = None

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

        expressions = [
            {"==": [{"var": "date"}, {"var": "today"}]},  # today is static variable
            {
                ">": [
                    {"date": "2010-04-26"},
                    {"date": {"-": [{"var": "today"}, {"duration": "P24Y"}]}},
                ]
            },
            {"==": [{"datetime": "2026-03-06T15:37:00"}, {"var": "datetime"}]},
            {"==": [{"var": "textfield"}, "foo"]},
        ]
        expected_results = [
            {
                "==": [
                    {"date": [{"var": ["date"]}]},
                    {"date": [{"var": ["today"]}]},
                ]
            },
            {
                ">": [
                    {"date": ["2010-04-26"]},
                    {
                        "date": [
                            {
                                "-": [
                                    {"date": [{"var": ["today"]}]},
                                    {"duration": ["P24Y"]},
                                ]
                            }
                        ]
                    },
                ]
            },
            {
                "==": [
                    {"datetime": ["2026-03-06T15:37:00"]},
                    {"datetime": [{"var": ["datetime"]}]},
                ]
            },
            {"==": [{"var": ["textfield"]}, "foo"]},
        ]

        for expression, expected_result in zip(
            expressions, expected_results, strict=True
        ):
            result = add_data_type_information(expression, state)
            with self.subTest(expression):
                self.assertEqual(expected_result, result)

    def test_components_with_multiple_true(self):
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

        expressions = [
            {"==": [{"var": "date.0"}, {"date": "2026-03-06"}]},
            {"==": [{"datetime": "2026-03-06T15:37:00"}, {"var": "datetime.1"}]},
            {"==": [{"var": "textfield.2"}, "foo"]},
            {"map": [{"var": "date"}, {">": [{"var": ""}, {"date": "2026-01-01"}]}]},
        ]
        expected_results = [
            {"==": [{"date": [{"var": ["date.0"]}]}, {"date": ["2026-03-06"]}]},
            {
                "==": [
                    {"datetime": ["2026-03-06T15:37:00"]},
                    {"datetime": [{"var": ["datetime.1"]}]},
                ]
            },
            {"==": [{"var": ["textfield.2"]}, "foo"]},
            {
                "map": [
                    {"var": ["date"]},
                    {">": [{"date": [{"var": [""]}]}, {"date": ["2026-01-01"]}]},
                ]
            },
        ]

        for expression, expected_result in zip(
            expressions, expected_results, strict=True
        ):
            result = add_data_type_information(expression, state)
            with self.subTest(expression):
                self.assertEqual(expected_result, result)

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

        expressions = [
            {"==": [{"var": "children.0.dateOfBirth"}, {"date": "2026-03-06"}]},
            {"==": [{"date": "2026-03-06"}, {"var": "children.1.dateOfBirth"}]},
            {"==": [{"var": "children.2.lastName"}, "Bekker"]},  # string
            {
                "==": [
                    {"var": "children.dateOfBirth"},
                    {"datetime": "2026-03-06T15:37:00"},
                ]
            },  # incorrect data access
            {"==": [{"var": "children.0.nonExisting"}, "foo"]},  # non-existing field
        ]
        expected_results = [
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
            {"==": [{"var": ["children.2.lastName"]}, "Bekker"]},
            {
                "==": [
                    {"var": ["children.dateOfBirth"]},
                    {"datetime": ["2026-03-06T15:37:00"]},
                ]
            },
            {"==": [{"var": ["children.0.nonExisting"]}, "foo"]},
        ]

        for expression, expected_result in zip(
            expressions, expected_results, strict=True
        ):
            result = add_data_type_information(expression, state)
            with self.subTest(expression):
                self.assertEqual(expected_result, result)

    def test_children_with_array_operations(self):
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

        expressions = [
            {
                "map": [
                    {"var": "children"},
                    {">": [{"var": "dateOfBirth"}, {"date": "2026-03-06"}]},
                ]
            },
            {
                "map": [
                    {"var": {"var": "foo"}},
                    {">": [{"var": "dateOfBirth"}, {"date": "2026-03-06"}]},
                ]
            },
            {
                "reduce": [
                    {"var": "children"},
                    {">": [{"var": "current.dateOfBirth"}, {"date": "2026-03-06"}]},
                    0,
                ]
            },
            {
                "reduce": [
                    {"var": {"var": "foo"}},
                    {">": [{"var": "current.dateOfBirth"}, {"date": "2026-03-06"}]},
                    0,
                ]
            },
            # A cursed expression:
            {
                "reduce": [
                    {
                        "map": [
                            {"var": "children"},
                            {">": [{"var": "dateOfBirth"}, {"date": "2026-03-06"}]},
                        ]
                    },
                    {"+": [{"var": "current"}, {"var": "accumulator"}]},
                    0,
                ]
            },
        ]
        expected_results = [
            {
                "map": [
                    {"var": ["children"]},
                    {
                        ">": [
                            {"date": [{"var": ["dateOfBirth"]}]},
                            {"date": ["2026-03-06"]},
                        ]
                    },
                ],
            },
            {
                "map": [
                    {"var": [{"var": "foo"}]},
                    {">": [{"var": ["dateOfBirth"]}, {"date": ["2026-03-06"]}]},
                ]
            },
            {
                "reduce": [
                    {"var": ["children"]},
                    {
                        ">": [
                            {"date": [{"var": ["current.dateOfBirth"]}]},
                            {"date": ["2026-03-06"]},
                        ]
                    },
                    0,
                ]
            },
            {
                "reduce": [
                    {"var": [{"var": "foo"}]},
                    {">": [{"var": ["current.dateOfBirth"]}, {"date": ["2026-03-06"]}]},
                    0,
                ]
            },
            {
                "reduce": [
                    {
                        "map": [
                            {"var": ["children"]},
                            {
                                ">": [
                                    {"date": [{"var": ["dateOfBirth"]}]},
                                    {"date": ["2026-03-06"]},
                                ]
                            },
                        ]
                    },
                    {"+": [{"var": ["current"]}, {"var": ["accumulator"]}]},
                    0,
                ]
            },
        ]

        for expected, expression in zip(expected_results, expressions, strict=True):
            result = add_data_type_information(expression, state)
            with self.subTest(expression):
                self.assertEqual(expected, result)

    def test_array_operations_without_component(self):
        form = FormFactory.create(generate_minimal_setup=True)
        submission = SubmissionFactory.create(form=form)
        state = submission.load_submission_value_variables_state()

        expressions = [
            {"map": [[1, 2, 3, 4], {">": [{"var": ""}, 3]}]},
            {
                "reduce": [
                    [1, 2, 3, 4],
                    {"+": [{"var": "current"}, {"var": "accumulator"}]},
                    0,
                ]
            },
            # A cursed expression:
            {
                "reduce": [
                    {"map": [[1, 2, 3, 4], {">": [{"var": ""}, 3]}]},
                    {"+": [{"var": "current"}, {"var": "accumulator"}]},
                    0,
                ]
            },
        ]
        expected_results = [
            {"map": [[1, 2, 3, 4], {">": [{"var": [""]}, 3]}]},
            {
                "reduce": [
                    [1, 2, 3, 4],
                    {"+": [{"var": ["current"]}, {"var": ["accumulator"]}]},
                    0,
                ]
            },
            # A cursed expression:
            {
                "reduce": [
                    {"map": [[1, 2, 3, 4], {">": [{"var": [""]}, 3]}]},
                    {"+": [{"var": ["current"]}, {"var": ["accumulator"]}]},
                    0,
                ]
            },
        ]

        for expected, expression in zip(expected_results, expressions, strict=True):
            result = add_data_type_information(expression, state)
            with self.subTest(expression):
                self.assertEqual(expected, result)

    def test_editgrid(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "editgrid",
                        "type": "editgrid",
                        "label": "Editgrid",
                        "components": [
                            {
                                "type": "textfield",
                                "key": "textfield",
                                "label": "Textfield",
                            },
                            {
                                "type": "date",
                                "key": "date",
                                "label": "Date",
                            },
                            {
                                "type": "datetime",
                                "key": "datetime",
                                "label": "Datetime",
                            },
                        ],
                    },
                ],
            },
        )
        submission = SubmissionFactory.create(form=form)
        state = submission.load_submission_value_variables_state()

        expressions = [
            {
                "==": [
                    {"var": "editgrid.0.date"},
                    {"date": "2026-03-06"},
                ]
            },
            {
                "==": [
                    {"datetime": "2026-03-06T11:22:33"},
                    {"var": "editgrid.1.datetime"},
                ]
            },
            {"==": [{"var": "editgrid.2.textfield"}, "Bekker"]},
            {
                "==": [
                    {"var": "editgrid.date"},
                    {"date": "2026-03-06"},
                ]
            },
            {"==": [{"var": "editgrid.0.nonExisting"}, "foo"]},
        ]
        expected_results = [
            {
                "==": [
                    {"date": [{"var": ["editgrid.0.date"]}]},
                    {"date": ["2026-03-06"]},
                ]
            },
            {
                "==": [
                    {"datetime": ["2026-03-06T11:22:33"]},
                    {"datetime": [{"var": ["editgrid.1.datetime"]}]},
                ]
            },
            {"==": [{"var": ["editgrid.2.textfield"]}, "Bekker"]},
            {
                "==": [
                    {"var": ["editgrid.date"]},
                    {"date": ["2026-03-06"]},
                ]
            },
            {"==": [{"var": ["editgrid.0.nonExisting"]}, "foo"]},
        ]

        for expression, expected_result in zip(
            expressions, expected_results, strict=True
        ):
            result = add_data_type_information(expression, state)
            with self.subTest(expression):
                self.assertEqual(expected_result, result)
