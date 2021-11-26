from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from django.utils.translation import gettext as _

import requests_mock
from freezegun import freeze_time

from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
)
from openforms.logging.models import TimelineLogProxy
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionStepFactory,
)

from ..constants import AppointmentDetailsStatus
from ..contrib.jcc.tests.test_plugin import mock_response
from ..exceptions import AppointmentCreateFailed
from ..models import AppointmentInfo
from ..service import AppointmentRegistrationFailed
from ..utils import (
    book_appointment_for_submission,
    cancel_previous_submission_appointment,
    create_base64_qrcode,
    find_first_appointment_step,
    get_formatted_phone_number,
)
from .factories import AppointmentInfoFactory
from .utils import setup_jcc


class BookAppointmentForSubmissionTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        setup_jcc()

    def test_creating_appointment_with_no_appointment_information_does_nothing(self):
        submission = SubmissionFactory.create()
        book_appointment_for_submission(submission)
        submission.refresh_from_db()
        self.assertFalse(AppointmentInfo.objects.exists())
        self.assertFalse(TimelineLogProxy.objects.exists())

    def test_appointment_step_not_applicable(self):
        form = FormFactory.create()
        step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "display": "form",
                "components": [
                    {
                        "key": "product",
                        "appointments": {"showProducts": True},
                        "label": "Product",
                    },
                    {
                        "key": "location",
                        "appointments": {"showLocations": True},
                        "label": "Location",
                    },
                    {
                        "key": "time",
                        "appointments": {"showTimes": True},
                        "label": "Time",
                    },
                ],
            },
        )
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission,
            data={},
            form_step=step,
        )

        book_appointment_for_submission(submission)

        self.assertFalse(AppointmentInfo.objects.exists())
        self.assertFalse(TimelineLogProxy.objects.exists())

    def test_creating_appointment_with_missing_or_not_filled_in_appointment_information_adds_error_message(
        self,
    ):
        form = FormFactory.create()
        form_definition_1 = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {
                        "key": "product",
                        "appointments": {"showProducts": True},
                        "label": "Product",
                    },
                    {
                        "key": "time",
                        "appointments": {"showTimes": True},
                        "label": "Time",
                    },
                ],
            }
        )
        form_definition_2 = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {
                        "key": "lastName",
                        "appointments": {"lastName": True},
                        "label": "Last Name",
                    },
                    {
                        "key": "birthDate",
                        "appointments": {"birthDate": True},
                        "label": "Date of Birth",
                    },
                ],
            }
        )
        form_step_1 = FormStepFactory.create(
            form=form, form_definition=form_definition_1
        )
        form_step_2 = FormStepFactory.create(
            form=form, form_definition=form_definition_2
        )
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission,
            data={
                "product": {"identifier": "79", "name": "Paspoort"},
                "time": "2021-08-25T17:00:00",
            },
            form_step=form_step_1,
        )
        SubmissionStepFactory.create(
            submission=submission,
            data={
                "lastName": "Maykin",
                "birthDate": "",
            },
            form_step=form_step_2,
        )

        with self.assertRaises(AppointmentRegistrationFailed):
            book_appointment_for_submission(submission)

        info = AppointmentInfo.objects.filter(
            submission=submission,
            status=AppointmentDetailsStatus.missing_info,
        ).get()

        self.assertEqual(
            info.error_information,
            _("The following appointment fields should be filled out: {fields}").format(
                fields="Date of Birth, locationIDAndName"
            ),
        )
        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/appointment_register_skip.txt"
            ).count(),
            1,
        )

    @requests_mock.Mocker()
    def test_creating_appointment_properly_creates_appointment_and_adds_appointment_information(
        self, m
    ):
        form = FormFactory.create()
        form_definition_1 = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {
                        "key": "product",
                        "appointments": {"showProducts": True},
                        "label": "Product",
                    },
                    {
                        "key": "location",
                        "appointments": {"showLocations": True},
                        "label": "Location",
                    },
                    {
                        "key": "time",
                        "appointments": {"showTimes": True},
                        "label": "Time",
                    },
                ],
            }
        )
        form_definition_2 = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {
                        "key": "lastName",
                        "appointments": {"lastName": True},
                        "label": "Last Name",
                    },
                    {
                        "key": "birthDate",
                        "appointments": {"birthDate": True},
                        "label": "Date of Birth",
                    },
                ],
            }
        )
        form_step_1 = FormStepFactory.create(
            form=form, form_definition=form_definition_1
        )
        form_step_2 = FormStepFactory.create(
            form=form, form_definition=form_definition_2
        )
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission,
            data={
                "product": {"identifier": "79", "name": "Paspoort"},
                "location": {"identifier": "1", "name": "Amsterdam"},
                "time": "2021-08-25T17:00:00+02:00",
            },
            form_step=form_step_1,
        )
        SubmissionStepFactory.create(
            submission=submission,
            data={
                "lastName": "Maykin",
                "birthDate": "1990-08-01",
            },
            form_step=form_step_2,
        )

        m.post(
            "http://example.com/soap11",
            text=mock_response("bookGovAppointmentResponse.xml"),
        )

        book_appointment_for_submission(submission)
        self.assertTrue(
            AppointmentInfo.objects.filter(
                appointment_id="1234567890",
                submission=submission,
                status=AppointmentDetailsStatus.success,
            ).exists()
        )
        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/appointment_register_start.txt"
            ).count(),
            1,
        )
        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/appointment_register_success.txt"
            ).count(),
            1,
        )

    @freeze_time("2021-08-21T18:00:00+02:00")
    @requests_mock.Mocker()
    def test_creating_appointment_deletes_previous_appointment_when_one_exists(self, m):
        new_completed_on = timezone.now() - timedelta(hours=1)
        base_data = {
            "product": {"identifier": "79", "name": "Paspoort"},
            "location": {"identifier": "1", "name": "Amsterdam"},
            "lastName": "Maykin",
            "birthDate": "1990-08-01",
        }
        submission = SubmissionFactory.from_components(
            completed=True,
            completed_on=new_completed_on,
            components_list=[
                {
                    "key": "product",
                    "appointments": {"showProducts": True},
                    "label": "Product",
                },
                {
                    "key": "location",
                    "appointments": {"showLocations": True},
                    "label": "Location",
                },
                {
                    "key": "time",
                    "appointments": {"showTimes": True},
                    "label": "Time",
                },
                {
                    "key": "lastName",
                    "appointments": {"lastName": True},
                    "label": "Last Name",
                },
                {
                    "key": "birthDate",
                    "appointments": {"birthDate": True},
                    "label": "Date of Birth",
                },
            ],
            submitted_data={**base_data, "time": "2021-08-26T17:00:00+02:00"},
            has_previous_submission=True,
            previous_submission__completed=True,
            previous_submission__completed_on=new_completed_on - timedelta(hours=12),
        )

        # set the data of the previous submission
        appointment_info = AppointmentInfoFactory.create(
            submission=submission.previous_submission,
            registration_ok=True,
            appointment_id="98765",
        )
        SubmissionStepFactory.create(
            submission=submission.previous_submission,
            form_step=submission.form.formstep_set.get(),
            data={**base_data, "time": "2021-08-25T17:00:00+02:00"},
        )
        m.post(
            "http://example.com/soap11",
            [
                {"text": mock_response("bookGovAppointmentResponse.xml")},
                {"text": mock_response("deleteGovAppointmentResponse.xml")},
            ],
        )

        book_appointment_for_submission(submission)

        self.assertTrue(
            AppointmentInfo.objects.filter(
                appointment_id="1234567890",
                submission=submission,
                status=AppointmentDetailsStatus.success,
            ).exists()
        )

        appointment_info.refresh_from_db()
        self.assertEqual(appointment_info.status, AppointmentDetailsStatus.cancelled)
        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/appointment_register_start.txt"
            ).count(),
            1,
        )
        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/appointment_register_success.txt"
            ).count(),
            1,
        )

    @requests_mock.Mocker()
    def test_failed_creating_appointment_adds_error_message_to_submission(self, m):
        form = FormFactory.create()
        form_definition_1 = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {
                        "key": "product",
                        "appointments": {"showProducts": True},
                        "label": "Product",
                    },
                    {
                        "key": "location",
                        "appointments": {"showLocations": True},
                        "label": "Location",
                    },
                    {
                        "key": "time",
                        "appointments": {"showTimes": True},
                        "label": "Time",
                    },
                ],
            }
        )
        form_definition_2 = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {
                        "key": "lastName",
                        "appointments": {"lastName": True},
                        "label": "Last Name",
                    },
                    {
                        "key": "birthDate",
                        "appointments": {"birthDate": True},
                        "label": "Date of Birth",
                    },
                ],
            }
        )
        form_step_1 = FormStepFactory.create(
            form=form, form_definition=form_definition_1
        )
        form_step_2 = FormStepFactory.create(
            form=form, form_definition=form_definition_2
        )
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission,
            data={
                "product": {"identifier": "79", "name": "Paspoort"},
                "location": {"identifier": "1", "name": "Amsterdam"},
                "time": "2021-08-25T17:00:00+02:00",
            },
            form_step=form_step_1,
        )
        SubmissionStepFactory.create(
            submission=submission,
            data={
                "lastName": "Maykin",
                "birthDate": "1990-08-01",
            },
            form_step=form_step_2,
        )

        m.post(
            "http://example.com/soap11",
            exc=AppointmentCreateFailed,
        )

        with self.assertRaises(AppointmentRegistrationFailed):
            book_appointment_for_submission(submission)

        self.assertTrue(
            AppointmentInfo.objects.filter(
                submission=submission,
                status=AppointmentDetailsStatus.failed,
            ).exists()
        )
        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/appointment_register_start.txt"
            ).count(),
            1,
        )
        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/appointment_register_failure.txt"
            ).count(),
            1,
        )

    @requests_mock.Mocker()
    def test_failed_creating_appointment_when_submission_previously_failed(self, m):
        form = FormFactory.create()
        form_definition_1 = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {
                        "key": "product",
                        "appointments": {"showProducts": True},
                        "label": "Product",
                    },
                    {
                        "key": "location",
                        "appointments": {"showLocations": True},
                        "label": "Location",
                    },
                    {
                        "key": "time",
                        "appointments": {"showTimes": True},
                        "label": "Time",
                    },
                ],
            }
        )
        form_definition_2 = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {
                        "key": "lastName",
                        "appointments": {"lastName": True},
                        "label": "Last Name",
                    },
                    {
                        "key": "birthDate",
                        "appointments": {"birthDate": True},
                        "label": "Date of Birth",
                    },
                ],
            }
        )
        form_step_1 = FormStepFactory.create(
            form=form, form_definition=form_definition_1
        )
        form_step_2 = FormStepFactory.create(
            form=form, form_definition=form_definition_2
        )
        submission = SubmissionFactory.create(form=form)
        first_appointment_info = AppointmentInfoFactory.create(
            status=AppointmentDetailsStatus.failed,
            error_information="Failed to make appointment",
            submission=submission,
        )
        SubmissionStepFactory.create(
            submission=submission,
            data={
                "product": {"identifier": "79", "name": "Paspoort"},
                "location": {"identifier": "1", "name": "Amsterdam"},
                "time": "2021-08-25T17:00:00+02:00",
            },
            form_step=form_step_1,
        )
        SubmissionStepFactory.create(
            submission=submission,
            data={
                "lastName": "Maykin",
                "birthDate": "1990-08-01",
            },
            form_step=form_step_2,
        )

        m.post(
            "http://example.com/soap11",
            exc=AppointmentCreateFailed,
        )

        with self.assertRaises(AppointmentRegistrationFailed):
            book_appointment_for_submission(submission)

        submission.refresh_from_db()
        second_appointment_info = submission.appointment_info

        self.assertNotEqual(first_appointment_info.pk, second_appointment_info.pk)

        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/appointment_register_start.txt"
            ).count(),
            1,
        )
        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/appointment_register_failure.txt"
            ).count(),
            1,
        )

    def test_cancelling_previous_appointments_nothing_to_cancel(self):
        submission1 = SubmissionFactory.create(has_previous_submission=True)
        AppointmentInfoFactory.create(
            submission=submission1.previous_submission,
            registration_failed=True,
        )
        submission2 = SubmissionFactory.create(has_previous_submission=True)
        AppointmentInfoFactory.create(
            submission=submission2.previous_submission,
            registration_ok=True,
            appointment_id="",
        )
        submissions = [
            ("no previous", SubmissionFactory.create(has_previous_submission=False)),
            (
                "no appointment info",
                SubmissionFactory.create(has_previous_submission=True),
            ),
            ("failed registration", submission1),
            ("succeeded registration but no id", submission2),
        ]

        for label, submission in submissions:
            with self.subTest(type=label):
                with requests_mock.Mocker() as m:
                    cancel_previous_submission_appointment(submission)

                self.assertFalse(m.called)


class UtilsTests(TestCase):
    maxDiff = 1024

    def test_create_base64_qrcode(self):
        data = "44b322c32c5329b135e1"
        expected = (
            "iVBORw0KGgoAAAANSUhEUgAAAUoAAAFKAQAAAABTUiuoAAAB50lEQVR4n"
            "O2bzY3cMAxGHyMDe5Q72FLkDlJSkJLSgVXKdiAfA9j4cpA849nLziQYr4IlT/p5h"
            "w8gKNKibOJOy9/uJcFRRx111FFHn4laswGb2Mxs3AyWfXl6ugBHH0GTJKmAfo5Bm"
            "gmyiSBJ0i36HAGOPoIulxACSG9DHZjZcI4AR++w4d3cwFCeMLGcIcDRf0FTCbLpE"
            "wU4+jEaJc37ouao6jJJ6zkCHL3D2kmYDYBQZ5behhXY7PkCHH3YW4frp/y6QnVUv"
            "L2V+nStjlJr9CSJVAAIkkrYPRXbruZP1+po9Zakdc9RUYK4HtxYzb3VD7q8yKZlQ"
            "DObkQqYjUAeTxLg6D3WAodWCTYrQaQS2obHVifo5cBbOeSteU9etar3vNUJevQWc"
            "UUzYa834gpJq8dWN+ixgk+/BoDNyCMIthMEOPp3NeEhmOY6kuetvtB2ElZHlZvp1"
            "TxvdYJeYkuXXtaxtvC81SF67R1XS5JgGfx7q0v02jue44pNi1k7DhfvRvaD7hV8o"
            "ba26tpMON7oet7qFK1PMn7Uj+WwF4snCnD0ETSVzchmrbWVR2htyv60fjl0z0pRU"
            "B9ixHVQ/l4gv/6263uaDrQ62tBsZmYj2LS8vH+X0aa9aP3CqPlfC4466qijjv5H6"
            "B/hFU+U471mPQAAAABJRU5ErkJggg=="
        )

        result = create_base64_qrcode(data)

        self.assertEqual(result, expected)

    def test_find_first_appointment_step_returns_None_for_no_appointment_data(self):
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "type": "textfield",
                    "key": "placeholder",
                }
            ]
        )

        step = find_first_appointment_step(submission.form)

        self.assertIsNone(step)

    def test_find_first_appointment_step_finds_correct_step(self):
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "product",
                    "appointments": {"showProducts": True},
                    "label": "Product",
                },
                {
                    "key": "time",
                    "appointments": {"showTimes": True},
                    "label": "Time",
                },
            ]
        )

        step = find_first_appointment_step(submission.form)

        self.assertIsNotNone(step)
        self.assertEqual(step, submission.submissionstep_set.get().form_step)


class GetFormattedPhoneNumberTest(TestCase):
    def test_get_formatted_phone_number_returns_expected_format(self):
        test_numbers = [
            "+31 20 753 05 23",
            "+31 20 753 05 abcdef23",
            "+31 20 753 05 {}()!@#$%^&*23",
            "+31 20 753 05 2333",
        ]

        for test_number in test_numbers:
            with self.subTest(test_number=test_number):
                self.assertEqual(
                    get_formatted_phone_number(test_number), "+31 20 753 05 23"
                )
