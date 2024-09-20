from unittest.mock import patch

from django.test import tag

from privates.test import temp_private_root
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.formio.tests.factories import (
    SubmittedFileFactory,
    TemporaryFileUploadFactory,
)
from openforms.forms.tests.factories import (
    FormFactory,
    FormStepFactory,
    FormVariableFactory,
)
from openforms.prefill import prefill_variables
from openforms.variables.constants import FormVariableDataTypes

from ..models import SubmissionValueVariable
from .factories import SubmissionFactory
from .mixins import SubmissionsMixin


@temp_private_root()
class SubmissionStepValidationTests(SubmissionsMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # ensure there is a form definition
        cls.form = FormFactory.create()
        cls.step1 = FormStepFactory.create(
            form=cls.form,
            form_definition__configuration={
                "components": [
                    {
                        "key": "test-key",
                        "type": "textfield",
                    },
                    {
                        "key": "my_file",
                        "type": "file",
                    },
                ]
            },
        )

        cls.form_url = reverse(
            "api:form-detail", kwargs={"uuid_or_slug": cls.form.uuid}
        )

        # ensure there is a submission
        cls.submission = SubmissionFactory.create(form=cls.form)

    def test_prefilled_data_updated(self):
        form = FormFactory.create()
        step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "surname",
                        "label": "Surname",
                        "prefill": {"plugin": "test-prefill", "attribute": "surname"},
                        "disabled": True,
                    }
                ]
            },
        )
        submission = SubmissionFactory.create(
            form=form, prefill_data={"surname": "Doe"}
        )
        self._add_submission_to_session(submission)
        endpoint = reverse(
            "api:submission-steps-validate",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": step.uuid,
            },
        )

        response = self.client.post(endpoint, {"data": {"surname": "Doe-MODIFIED"}})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        invalid_params = response.json()["invalidParams"]
        error_fields = [param["name"] for param in invalid_params]
        self.assertEqual(error_fields, ["data.surname"])
        self.assertEqual(invalid_params[0]["code"], "invalidPrefilledField")

    def test_prefilled_data_updated_not_disabled(self):
        form = FormFactory.create()
        step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "surname",
                        "label": "Surname",
                        "prefill": {"plugin": "test-prefill", "attribute": "surname"},
                        "disabled": False,
                    }
                ]
            },
        )
        submission = SubmissionFactory.create(
            form=form, prefill_data={"surname": "Doe"}
        )
        self._add_submission_to_session(submission)
        endpoint = reverse(
            "api:submission-steps-validate",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": step.uuid,
            },
        )

        response = self.client.post(endpoint, {"data": {"surname": "Doe-MODIFIED"}})

        # Since the prefilled field was not disabled, it is possible to modify it and the submission is valid
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_null_prefilled_data(self):
        form = FormFactory.create()
        step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "display": "form",
                "components": [
                    {
                        "type": "textfield",
                        "key": "surname",
                        "label": "Surname",
                        "prefill": {"plugin": "test-prefill", "attribute": "surname"},
                        "disabled": True,
                        "defaultValue": "",
                    }
                ],
            },
        )
        submission = SubmissionFactory.create(form=form, prefill_data={"surname": None})
        self._add_submission_to_session(submission)
        endpoint = reverse(
            "api:submission-steps-validate",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": step.uuid,
            },
        )

        response = self.client.post(endpoint, {"data": {"surname": ""}})

        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)

    def test_prefilled_data_normalised(self):
        form = FormFactory.create()
        step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "display": "form",
                "components": [
                    {
                        "key": "postcode",
                        "type": "postcode",
                        "prefill": {"plugin": "test-prefill", "attribute": "postcode"},
                        "disabled": True,
                        "label": "Postcode",
                        "inputMask": "9999 AA",
                    },
                    {
                        "key": "birthdate",
                        "type": "date",
                        "prefill": {"plugin": "test-prefill", "attribute": "birthdate"},
                        "disabled": True,
                        "label": "Birthdate",
                    },
                ],
            },
        )

        submission = SubmissionFactory.create(
            form=form,
            prefill_data={"postcode": "4505XY", "birthdate": "19990101"},
        )

        self._add_submission_to_session(submission)
        response = self.client.put(
            reverse(
                "api:submission-steps-detail",
                kwargs={
                    "submission_uuid": submission.uuid,
                    "step_uuid": step.uuid,
                },
            ),
            {"data": {"postcode": "4505 XY", "birthdate": "1999-01-01"}},
        )

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(
            SubmissionValueVariable.objects.get(key="postcode").value, "4505 XY"
        )
        self.assertEqual(
            SubmissionValueVariable.objects.get(key="birthdate").value, "1999-01-01"
        )

    @tag("gh-1899")
    @patch(
        "openforms.prefill._fetch_prefill_values",
        return_value={
            "postcode": {"main": {"static": "1015CJ"}},
        },
    )
    def test_flow_with_badly_structure_prefill_data(self, m_prefill):
        form = FormFactory.create()
        form_step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "postcode",
                        "key": "postcode",
                        "inputMask": "9999 AA",
                        "prefill": {
                            "plugin": "postcode",
                            "attribute": "static",
                        },
                        "defaultValue": "",
                    }
                ]
            },
        )
        submission = SubmissionFactory.create(form=form)
        prefill_variables(submission=submission)
        self._add_submission_to_session(submission)

        response = self.client.get(
            reverse(
                "api:submission-steps-detail",
                kwargs={
                    "submission_uuid": submission.uuid,
                    "step_uuid": form_step.uuid,
                },
            ),
        )

        data = response.json()["data"]
        self.assertEqual(data["postcode"], "1015 CJ")

    def test_step_configuration_not_camelcased(self):
        form = FormFactory.create()
        form_step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "key": "time",
                        "type": "time",
                        "errors": {"invalid_time": "Invalid time! Oh no!"},
                    }
                ]
            },
        )
        submission = SubmissionFactory.create(form=form)

        self._add_submission_to_session(submission)
        response = self.client.get(
            reverse(
                "api:submission-steps-detail",
                kwargs={
                    "submission_uuid": submission.uuid,
                    "step_uuid": form_step.uuid,
                },
            ),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(
            "invalid_time",
            response.json()["formStep"]["configuration"]["components"][0]["errors"],
        )

    @tag("gh-4143")
    def test_data_validated(self):
        """
        Assert that the shape of data is validated according to the formio definition.

        The validate configuration of each component needs to be applied, but a field
        being required/optional is irrelevant at this stage (that runs at the end).
        """
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "textfield",
                        "label": "Patterned textfield",
                        "validate": {
                            "required": True,
                            "pattern": r"[0-9]{1,3}",
                        },
                    },
                    {
                        "type": "editgrid",
                        "key": "repeatingGroup",
                        "label": "Repeating group",
                        "components": [
                            {
                                "type": "number",
                                "key": "number",
                                "label": "Number",
                                "validate": {
                                    "required": True,
                                },
                            }
                        ],
                    },
                    {
                        "type": "date",
                        "key": "dateWithoutValidationInfo",
                        "label": "Date without validation info",
                        "validate": {},
                    },
                ]
            },
        )
        self._add_submission_to_session(submission)
        endpoint = reverse(
            "api:submission-steps-detail",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": submission.form.formstep_set.get().uuid,
            },
        )
        data = {
            "textfield": "1a34",  # invalid, because max 3 chars, all numeric
            "repeatingGroup": [
                {},  # valid, because required is not enforced
                {"number": "notanumber"},  # invalid, not a number
                {"number": None},  # valid: skip required, so `null` is allowed
            ],
        }

        response = self.client.put(endpoint, {"data": data})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        invalid_params = response.json()["invalidParams"]
        names = {error["name"] for error in invalid_params}
        expected_names = {"data.textfield", "data.repeatingGroup.1.number"}
        self.assertEqual(names, expected_names)

    def test_validate_selectboxes_with_dynamic_values_source(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "type": "selectboxes",
                    "key": "selectboxes",
                    "label": "Dynamic selectboxes",
                    "validate": {
                        "required": True,
                        "minSelectedCount": 1,
                        "maxSelectedCount": 3,
                    },
                    "openForms": {
                        "dataSrc": "variable",
                        "itemsExpression": {
                            "var": "items",
                        },
                    },
                    "values": [],
                },
            ]
        )
        FormVariableFactory.create(
            form=submission.form,
            user_defined=True,
            key="items",
            data_type=FormVariableDataTypes.array,
            initial_value=[
                ["a", "Value A"],
                ["b", "Value B"],
                ["c", "Value C"],
                ["d", "Value D"],
                ["e", "Value E"],
            ],
        )
        self._add_submission_to_session(submission)
        endpoint = reverse(
            "api:submission-steps-detail",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": submission.form.formstep_set.get().uuid,
            },
        )

        # sanity check
        with self.subTest("check valid configuration items expression"):
            resp = self.client.get(endpoint)

            values = resp.json()["formStep"]["configuration"]["components"][0]["values"]
            self.assertEqual(len(values), 5)

        with self.subTest("valid data"):
            data = {
                "selectboxes": {
                    "a": False,
                    "b": True,
                    "c": False,
                    "d": True,
                    "e": False,
                }
            }

            response = self.client.put(endpoint, {"data": data})

            self.assertEqual(response.status_code, status.HTTP_200_OK)

        # invalid data cases
        invalid_data_cases = [
            # missing keys
            {"a": True},
            # minimum count checked not okay
            {
                "a": False,
                "b": False,
                "c": False,
                "d": False,
                "e": False,
            },
            # maximum count checked not okay
            {
                "a": True,
                "b": True,
                "c": True,
                "d": True,
                "e": True,
            },
        ]

        for invalid_case in invalid_data_cases:
            data = {"selectboxes": invalid_case}
            with self.subTest("invalid data", data=data):
                response = self.client.put(endpoint, {"data": data})

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                error_names = [
                    param["name"] for param in response.json()["invalidParams"]
                ]
                self.assertTrue(
                    all(name.startswith("data.selectboxes") for name in error_names)
                )

    def test_validate_step_with_nested_files_in_columns(self):
        temporary_file_upload = TemporaryFileUploadFactory.create()
        file = SubmittedFileFactory.create(temporary_upload=temporary_file_upload)
        submission = temporary_file_upload.submission
        form_step = FormStepFactory.create(
            form=submission.form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "columns",
                        "key": "columns",
                        "label": "Columns",
                        "columns": [
                            {
                                "size": 6,
                                "components": [
                                    {
                                        "key": "fileUpload1",
                                        "file": {
                                            "name": "",
                                            "type": [],
                                            "allowedTypesLabels": [],
                                        },
                                        "type": "file",
                                        "label": "File Upload 1",
                                    },
                                ],
                            },
                            {
                                "size": 6,
                                "components": [
                                    {
                                        "key": "fileUpload2",
                                        "file": {
                                            "name": "",
                                            "type": [],
                                            "allowedTypesLabels": [],
                                        },
                                        "type": "file",
                                        "label": "File Upload 2",
                                    },
                                ],
                            },
                        ],
                    }
                ]
            },
        )

        self._add_submission_to_session(submission)
        response = self.client.post(
            reverse(
                "api:submission-steps-validate",
                kwargs={
                    "submission_uuid": submission.uuid,
                    "step_uuid": form_step.uuid,
                },
            ),
            {"data": {"columns": [{"fileUpload1": [file], "fileUpload2": [file]}]}},
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_validate_step_with_nested_files_in_fieldset(self):
        temporary_file_upload = TemporaryFileUploadFactory.create()
        file = SubmittedFileFactory.create(temporary_upload=temporary_file_upload)
        submission = temporary_file_upload.submission
        form_step = FormStepFactory.create(
            form=submission.form,
            form_definition__configuration={
                "components": [
                    {
                        "key": "fieldset",
                        "type": "fieldset",
                        "components": [
                            {
                                "key": "fileUpload1",
                                "file": {
                                    "name": "",
                                    "type": [],
                                    "allowedTypesLabels": [],
                                },
                                "type": "file",
                                "label": "File Upload 1",
                            },
                        ],
                    },
                ]
            },
        )

        self._add_submission_to_session(submission)
        response = self.client.post(
            reverse(
                "api:submission-steps-validate",
                kwargs={
                    "submission_uuid": submission.uuid,
                    "step_uuid": form_step.uuid,
                },
            ),
            {"data": {"fieldset": [{"fileUpload1": [file]}]}},
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
