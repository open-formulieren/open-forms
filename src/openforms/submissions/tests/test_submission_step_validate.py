from unittest.mock import patch
from uuid import UUID

from django.test import tag
from django.utils.translation import gettext as _

from privates.test import temp_private_root
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.formio.constants import DataSrcOptions
from openforms.formio.tests.factories import (
    SubmittedFileFactory,
    TemporaryFileUploadFactory,
)
from openforms.forms.tests.factories import (
    FormFactory,
    FormLogicFactory,
    FormStepFactory,
    FormVariableFactory,
)
from openforms.prefill.service import prefill_variables
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

    def test_prefill_data_with_hidden_component(self):
        form = FormFactory.create()
        step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "display": "form",
                "components": [
                    {
                        "type": "textfield",
                        "key": "name",
                        "label": "Name",
                        "prefill": {"plugin": "test-prefill", "attribute": "name"},
                        "disabled": True,
                        "defaultValue": "",
                        "hidden": False,
                    },
                    {
                        "type": "textfield",
                        "key": "surname",
                        "label": "Surname",
                        "prefill": {"plugin": "test-prefill", "attribute": "surname"},
                        "disabled": True,
                        "defaultValue": "",
                        "hidden": True,
                    },
                ],
            },
        )
        submission = SubmissionFactory.create(
            form=form, prefill_data={"surname": "test"}
        )
        self._add_submission_to_session(submission)
        endpoint = reverse(
            "api:submission-steps-validate",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": step.uuid,
            },
        )

        response = self.client.post(endpoint, {"data": {"surname": "test"}})

        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)

    def test_prefill_data_with_hidden_parent_component(self):
        form = FormFactory.create()
        step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "display": "form",
                "components": [
                    {
                        "key": "fieldset",
                        "type": "fieldset",
                        "hidden": True,
                        "components": [
                            {
                                "type": "textfield",
                                "key": "name",
                                "label": "Name",
                                "prefill": {
                                    "plugin": "test-prefill",
                                    "attribute": "name",
                                },
                                "disabled": True,
                                "defaultValue": "",
                                "hidden": False,
                            },
                        ],
                    },
                ],
            },
        )
        submission = SubmissionFactory.create(form=form, prefill_data={"name": "test"})
        self._add_submission_to_session(submission)
        endpoint = reverse(
            "api:submission-steps-validate",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": step.uuid,
            },
        )

        response = self.client.post(endpoint, {"data": {}})

        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)

    def test_prefill_data_is_persisted_when_submission_data_omitted(self):
        form = FormFactory.create()
        step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "display": "form",
                "components": [
                    {
                        "type": "textfield",
                        "key": "name",
                        "label": "Name",
                        "prefill": {"plugin": "test-prefill", "attribute": "name"},
                        "disabled": True,
                        "defaultValue": "",
                        "hidden": False,
                    },
                ],
            },
        )
        submission = SubmissionFactory.create(form=form, prefill_data={"name": "test"})
        self._add_submission_to_session(submission)
        endpoint = reverse(
            "api:submission-steps-validate",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": step.uuid,
            },
        )

        with self.subTest("empty data field"):
            response = self.client.post(endpoint, {"data": {}})

            submission.refresh_from_db()
            variable = submission.submissionvaluevariable_set.get()

            self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
            self.assertEqual(variable.value, "test")

        with self.subTest("data field not present"):
            response = self.client.post(endpoint, {})

            submission.refresh_from_db()
            variable = submission.submissionvaluevariable_set.get()

            self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
            self.assertEqual(variable.value, "test")

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
        "openforms.prefill.service.fetch_prefill_values_from_attribute",
        return_value={"postcode": "1015CJ"},
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
                        "dataSrc": DataSrcOptions.variable,
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
            {"data": {"fileUpload1": [file], "fileUpload2": [file]}},
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
            {"data": {"fileUpload1": [file]}},
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_validate_step_with_soft_hyphen_filename(self):
        temporary_file_upload = TemporaryFileUploadFactory.create(
            file_name="Schermafbeelding 2025-07-08 om 09.39.36.png"  # no soft-hyphen
        )
        file = SubmittedFileFactory.create(
            temporary_upload=temporary_file_upload,
            temporary_upload__data_name="Schermafbeelding 2025-07-08 om 09.39.36.png",  # no soft-hyphen
            temporary_upload__original_name="Scherm­afbeelding 2025-07-08 om 09.39.36.png",  # soft-hyphen
        )

        submission = temporary_file_upload.submission
        form_step = FormStepFactory.create(
            form=submission.form,
            form_definition__configuration={
                "components": [
                    {
                        "key": "fileUpload",
                        "file": {
                            "name": "",
                            "type": ["image/png", "image/jpeg"],
                            "allowedTypesLabels": [".png", ".jpg"],
                        },
                        "type": "file",
                        "input": True,
                        "label": "File Upload",
                        "tableView": False,
                        "filePattern": "image/png,image/jpeg",
                        "useConfigFiletypes": True,
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
            {"data": {"fileUpload": [file]}},
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @tag("gh-5557")
    def test_validate_step_with_filename_with_diff_chars(self):
        for filename in [
            "Name with parentheses ()[]{}.png",
            "Name with non-latin chars например.png",
            "Name with magic t̸̨͔͍̭̜̦̙͈̐̃̃̇͊̈́͆͂͗̔̕͠͝ẹ̴̡̠̼͍̙̲̱̩̫̝̜̝̬̲̟̳͔̘͓͔̙̲̐̄͐̏̌̒́̎̒͂̐͛͗̚ͅŝ̶̢̧̢̠̦̞̬̯̖̺̱̯̣̹̗͕̳̆̅̃̄̾̂̈́̃͋͊̍̈͒͌̈́͐͜͠ͅ.png",
        ]:
            with self.subTest(filename):
                temporary_file_upload = TemporaryFileUploadFactory.create(
                    file_name=filename
                )
                file = SubmittedFileFactory.create(
                    temporary_upload=temporary_file_upload,
                    temporary_upload__original_name=filename,
                )

                submission = temporary_file_upload.submission
                form_step = FormStepFactory.create(
                    form=submission.form,
                    form_definition__configuration={
                        "components": [
                            {
                                "key": "fileUpload",
                                "file": {
                                    "name": "",
                                    "type": ["image/png", "image/jpeg"],
                                    "allowedTypesLabels": [".png", ".jpg"],
                                },
                                "type": "file",
                                "input": True,
                                "label": "File Upload",
                                "tableView": False,
                                "filePattern": "image/png,image/jpeg",
                                "useConfigFiletypes": True,
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
                    {"data": {"fileUpload": [file]}},
                )

                self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @tag("gh-5191")
    def test_validate_map_component_hidden_and_clear_on_hide(self):
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "radio",
                        "key": "radio",
                        "label": "Radio",
                        "openForms": {"dataSrc": "manual"},
                        "values": [
                            {"value": "a", "label": "A"},
                            {"value": "b", "label": "B"},
                        ],
                    },
                    {
                        "type": "map",
                        "key": "map",
                        "label": "Map",
                        "clearOnHide": True,
                        "interactions": {
                            "marker": True,
                            "polygon": False,
                            "polyline": False,
                        },
                    },
                ]
            },
        )
        FormLogicFactory.create(
            form=submission.form,
            json_logic_trigger={"==": [{"var": "toggle"}, "a"]},
            actions=[
                {
                    "uuid": "981ebf58-4d2e-4b1f-bf6b-709a52104714",
                    "component": "kaart",
                    "formStepUuid": None,
                    "action": {
                        "type": "property",
                        "property": {"value": "hidden", "type": "bool"},
                        "state": True,
                    },
                }
            ],
        )
        step = submission.form.formstep_set.get()
        self._add_submission_to_session(submission)

        endpoint = reverse(
            "api:submission-steps-validate",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": step.uuid,
            },
        )

        response = self.client.post(
            endpoint,
            {
                "data": {
                    "radio": "a",
                    "map": None,
                }
            },
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_validate_partners_component(self):
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "partners",
                        "key": "partners",
                        "label": "Partners",
                    },
                ]
            },
        )
        FormVariableFactory.create(
            form=submission.form,
            user_defined=True,
            key="immutable_partners",
            data_type=FormVariableDataTypes.array,
            prefill_plugin="family_members",
            prefill_options={
                "type": "partners",
                "mutable_data_form_variable": "partners",
            },
            initial_value=[
                {
                    "bsn": "123456782",
                    "initials": "",
                    "affixes": "L",
                    "lastName": "Boei",
                    "dateOfBirth": "1990-01-01",
                }
            ],
        )

        step = submission.form.formstep_set.get()
        self._add_submission_to_session(submission)

        endpoint = reverse(
            "api:submission-steps-validate",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": step.uuid,
            },
        )

        response = self.client.post(
            endpoint,
            {
                "data": {
                    "partners": [
                        {
                            "bsn": "123456782",
                            "initials": "",
                            "affixes": "L",
                            "lastName": "Boei",
                            "dateOfBirth": "1990-01-01",
                        }
                    ]
                }
            },
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_partners_component_fails_when_data_is_tampered(self):
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "partners",
                        "key": "partners",
                        "label": "Partners",
                    },
                ]
            },
        )
        FormVariableFactory.create(
            form=submission.form,
            user_defined=True,
            key="immutable_partners",
            data_type=FormVariableDataTypes.array,
            prefill_plugin="family_members",
            prefill_options={
                "type": "partners",
                "mutable_data_form_variable": "partners",
            },
            initial_value=[
                {
                    "bsn": "123456782",
                    "initials": "",
                    "affixes": "L",
                    "lastName": "Boei",
                    "dateOfBirth": "1990-01-01",
                }
            ],
        )

        step = submission.form.formstep_set.get()
        self._add_submission_to_session(submission)

        endpoint = reverse(
            "api:submission-steps-validate",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": step.uuid,
            },
        )

        response = self.client.post(
            endpoint,
            {
                "data": {
                    "partners": [
                        {
                            "bsn": "123456782",
                            "initials": "",
                            "affixes": "",
                            "lastName": "Another name",
                            "dateOfBirth": "1990-01-01",
                        }
                    ]
                }
            },
        )

        invalid_params = response.json()["invalidParams"]

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(invalid_params), 1)
        self.assertEqual(invalid_params[0]["name"], "data.partners")
        self.assertEqual(
            invalid_params[0]["reason"],
            _("The family members prefill data may not be altered."),
        )

    def test_partners_component_retrieves_correct_variable_for_validation(self):
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "partners",
                        "key": "partners",
                        "label": "Partners",
                    },
                ]
            },
        )

        # The order of the variables matters here, we want the unmatched variable first
        FormVariableFactory.create(
            user_defined=True,
            key="immutable_partners_2",
            data_type=FormVariableDataTypes.array,
            prefill_plugin="family_members",
            prefill_options={
                "type": "partners",
                "mutable_data_form_variable": "partners",
            },
            initial_value=[
                {
                    "bsn": "123456782",
                    "initials": "",
                    "affixes": "L",
                    "lastName": "Boei",
                    "dateOfBirth": "1990-01-01",
                }
            ],
        )

        FormVariableFactory.create(
            form=submission.form,
            user_defined=True,
            key="immutable_partners",
            data_type=FormVariableDataTypes.array,
            prefill_plugin="family_members",
            prefill_options={
                "type": "partners",
                "mutable_data_form_variable": "partners",
            },
            initial_value=[
                {
                    "bsn": "123456782",
                    "initials": "",
                    "affixes": "L",
                    "lastName": "Boei",
                    "dateOfBirth": "1990-01-01",
                }
            ],
        )

        step = submission.form.formstep_set.get()
        self._add_submission_to_session(submission)

        endpoint = reverse(
            "api:submission-steps-validate",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": step.uuid,
            },
        )

        response = self.client.post(
            endpoint,
            {
                "data": {
                    "partners": [
                        {
                            "bsn": "123456782",
                            "initials": "",
                            "affixes": "L",
                            "lastName": "Boei",
                            "dateOfBirth": "1990-01-01",
                        }
                    ]
                }
            },
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_validate_children_component(self):
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "children",
                        "key": "children",
                        "label": "Children",
                        "enableSelection": False,
                    },
                ]
            },
        )
        FormVariableFactory.create(
            form=submission.form,
            user_defined=True,
            key="immutable_children",
            data_type=FormVariableDataTypes.array,
            prefill_plugin="family_members",
            prefill_options={
                "type": "children",
                "mutable_data_form_variable": "children",
            },
            initial_value=[
                {
                    "bsn": "999970409",
                    "firstNames": "Pero",
                    "dateOfBirth": "2023-02-01",
                },
            ],
        )

        step = submission.form.formstep_set.get()
        self._add_submission_to_session(submission)

        endpoint = reverse(
            "api:submission-steps-validate",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": step.uuid,
            },
        )

        response = self.client.post(
            endpoint,
            {
                # TODO
                # Make sure this is updated (the data we get from the submission) when task
                # 2324 is completed
                # the data here is coming from the submission so that's why we have the extra
                # keys (used only for frontend operations)
                "data": {
                    "children": [
                        {
                            "bsn": "999970409",
                            "affixes": "van",
                            "initials": "P.",
                            "lastName": "Paassen",
                            "firstNames": "Pero",
                            "dateOfBirth": "2023-02-01",
                            "dateOfBirthPrecision": "date",
                            "selected": None,
                            "__addedManually": False,
                            "__id": UUID("2232657a-cb04-467d-9ded-6eb7a4819cc4"),
                        },
                    ]
                }
            },
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_children_component_retrieves_correct_variable_for_validation(self):
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "children",
                        "key": "children",
                        "label": "Children",
                        "enableSelection": False,
                    },
                ]
            },
        )
        FormVariableFactory.create(
            user_defined=True,
            key="immutable_children_2",
            data_type=FormVariableDataTypes.array,
            prefill_plugin="family_members",
            prefill_options={
                "type": "children",
                "mutable_data_form_variable": "children",
            },
            initial_value=[
                {
                    "bsn": "999970409",
                    "firstNames": "Pero",
                    "dateOfBirth": "2023-02-01",
                },
            ],
        )
        FormVariableFactory.create(
            form=submission.form,
            user_defined=True,
            key="immutable_children",
            data_type=FormVariableDataTypes.array,
            prefill_plugin="family_members",
            prefill_options={
                "type": "children",
                "mutable_data_form_variable": "children",
            },
            initial_value=[
                {
                    "bsn": "999970409",
                    "firstNames": "Pero",
                    "dateOfBirth": "2023-02-01",
                },
            ],
        )

        step = submission.form.formstep_set.get()
        self._add_submission_to_session(submission)

        endpoint = reverse(
            "api:submission-steps-validate",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": step.uuid,
            },
        )

        response = self.client.post(
            endpoint,
            {
                # TODO
                # Make sure this is updated (the data we get from the submission) when task
                # 2324 is completed
                # the data here is coming from the submission so that's why we have the extra
                # keys (used only for frontend operations)
                "data": {
                    "children": [
                        {
                            "bsn": "999970409",
                            "affixes": "van",
                            "initials": "P.",
                            "lastName": "Paassen",
                            "firstNames": "Pero",
                            "dateOfBirth": "2023-02-01",
                            "dateOfBirthPrecision": "date",
                            "selected": None,
                            "__addedManually": False,
                            "__id": UUID("2232657a-cb04-467d-9ded-6eb7a4819cc4"),
                        },
                    ]
                }
            },
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_children_component_fails_when_data_is_tampered(self):
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "children",
                        "key": "children",
                        "label": "Children",
                        "enableSelection": False,
                    },
                ]
            },
        )
        FormVariableFactory.create(
            form=submission.form,
            user_defined=True,
            key="immutable_children",
            data_type=FormVariableDataTypes.array,
            prefill_plugin="family_members",
            prefill_options={
                "type": "children",
                "mutable_data_form_variable": "children",
            },
            initial_value=[
                {
                    "bsn": "123456782",
                    "firstNames": "Pero",
                    "dateOfBirth": "1990-01-01",
                }
            ],
        )

        step = submission.form.formstep_set.get()
        self._add_submission_to_session(submission)

        endpoint = reverse(
            "api:submission-steps-validate",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": step.uuid,
            },
        )

        response = self.client.post(
            endpoint,
            {
                # TODO
                # Make sure this is updated (the data we get from the submission) when task
                # 2324 is completed
                # the data here is coming from the submission so that's why we have the extra
                # keys (used only for frontend operations)
                "data": {
                    "children": [
                        {
                            "bsn": "999970409",
                            "affixes": "van",
                            "initials": "P.",
                            "lastName": "Paassen",
                            "firstNames": "Another name",
                            "dateOfBirth": "2023-02-01",
                            "dateOfBirthPrecision": "date",
                            "selected": None,
                            "__addedManually": False,
                            "__id": UUID("2232657a-cb04-467d-9ded-6eb7a4819cc4"),
                        },
                    ]
                }
            },
        )

        invalid_params = response.json()["invalidParams"]

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(invalid_params), 1)
        self.assertEqual(invalid_params[0]["name"], "data.children")
        self.assertEqual(
            invalid_params[0]["reason"],
            _("The family members prefill data may not be altered."),
        )
