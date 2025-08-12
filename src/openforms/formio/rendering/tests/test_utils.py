from django.test import TestCase

from openforms.formio.rendering.structured import (
    reshape_submission_data_for_json_summary,
)
from openforms.forms.tests.factories import FormFactory, FormStepFactory
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionStepFactory,
)


class TestReshapeSubmissionDataForJsonSummary(TestCase):
    def test_multiple_steps(self):
        form = FormFactory.create()
        form_step0 = FormStepFactory.create(
            form=form,
            form_definition__slug="fd0",
            form_definition__configuration={
                "components": [
                    {
                        "key": "input1",
                        "type": "textfield",
                    },
                    {
                        "key": "input2",
                        "type": "textfield",
                    },
                ]
            },
        )
        form_step1 = FormStepFactory.create(
            form=form,
            form_definition__slug="fd1",
            form_definition__configuration={
                "components": [
                    {
                        "key": "input3",
                        "type": "textfield",
                    },
                    {
                        "key": "input4",
                        "type": "textfield",
                    },
                ]
            },
        )

        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            form_step=form_step0,
            submission=submission,
            data={
                "input1": "Foo",
                "input2": "Bar",
            },
        )
        SubmissionStepFactory.create(
            form_step=form_step1,
            submission=submission,
            data={
                "input3": "Fuu",
                "input4": "Ber",
            },
        )

        data = reshape_submission_data_for_json_summary(submission)

        self.assertEqual(
            data,
            {
                "fd0": {
                    "input1": "Foo",
                    "input2": "Bar",
                },
                "fd1": {
                    "input3": "Fuu",
                    "input4": "Ber",
                },
            },
        )

    def test_fieldset(self):
        form = FormFactory.create()
        form_step = FormStepFactory.create(
            form=form,
            form_definition__slug="fd0",
            form_definition__configuration={
                "components": [
                    {
                        "key": "fieldset1",
                        "type": "fieldset",
                        "components": [
                            {
                                "key": "input1",
                                "type": "textfield",
                            },
                            {
                                "key": "input2",
                                "type": "textfield",
                            },
                            {
                                "key": "fieldset2",
                                "type": "fieldset",
                                "components": [
                                    {
                                        "key": "input3",
                                        "type": "textfield",
                                    },
                                    {
                                        "key": "input4",
                                        "type": "textfield",
                                    },
                                ],
                            },
                        ],
                    },
                    {
                        "key": "input5",
                        "type": "textfield",
                    },
                ]
            },
        )

        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            form_step=form_step,
            submission=submission,
            data={
                "input1": "Foo",
                "input2": "Bar",
                "input3": "Fuu",
                "input4": "Ber",
                "input5": "Faa",
            },
        )

        data = reshape_submission_data_for_json_summary(submission)

        self.assertEqual(
            data,
            {
                "fd0": {
                    "fieldset1": {
                        "input1": "Foo",
                        "input2": "Bar",
                        "fieldset2": {
                            "input3": "Fuu",
                            "input4": "Ber",
                        },
                    },
                    "input5": "Faa",
                },
            },
        )

    def test_columns(self):
        form = FormFactory.create()
        form_step = FormStepFactory.create(
            form=form,
            form_definition__slug="fd0",
            form_definition__configuration={
                "components": [
                    {
                        "key": "column1",
                        "type": "columns",
                        "columns": [
                            {
                                "size": 6,
                                "components": [
                                    {
                                        "key": "input1",
                                        "type": "textfield",
                                    }
                                ],
                            },
                            {
                                "size": 6,
                                "components": [
                                    {
                                        "key": "fieldset1",
                                        "type": "fieldset",
                                        "components": [
                                            {
                                                "key": "input2",
                                                "type": "textfield",
                                            },
                                        ],
                                    },
                                    {
                                        "key": "input3",
                                        "type": "textfield",
                                    },
                                ],
                            },
                        ],
                    },
                ]
            },
        )

        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            form_step=form_step,
            submission=submission,
            data={
                "input1": "Foo",
                "input2": "Bar",
                "input3": "Fuu",
            },
        )

        data = reshape_submission_data_for_json_summary(submission)

        self.assertEqual(
            data,
            {
                "fd0": {
                    "column1": {
                        "0": {"input1": "Foo"},
                        "1": {
                            "fieldset1": {
                                "input2": "Bar",
                            },
                            "input3": "Fuu",
                        },
                    }
                },
            },
        )

    def test_editgrid(self):
        form = FormFactory.create()
        form_step = FormStepFactory.create(
            form=form,
            form_definition__slug="fd0",
            form_definition__configuration={
                "components": [
                    {
                        "type": "editgrid",
                        "key": "editgrid1",
                        "components": [
                            {
                                "type": "textfield",
                                "key": "input1",
                            }
                        ],
                    },
                ]
            },
        )

        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            form_step=form_step,
            submission=submission,
            data={"editgrid1": [{"input1": "Foo"}, {"input1": "Bar"}]},
        )

        data = reshape_submission_data_for_json_summary(submission)

        self.assertEqual(
            data,
            {
                "fd0": {"editgrid1": [{"input1": "Foo"}, {"input1": "Bar"}]},
            },
        )
