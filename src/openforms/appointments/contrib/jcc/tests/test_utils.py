import os

from django.conf import settings
from django.test import TestCase

import requests_mock

from openforms.appointments.contrib.jcc.models import JccConfig
from openforms.appointments.contrib.jcc.tests.utils import mock_response
from openforms.appointments.contrib.jcc.utils import book_appointment_for_submission
from openforms.appointments.exceptions import AppointmentCreateFailed
from openforms.forms.tests.factories import FormDefinitionFactory, FormStepFactory
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionStepFactory,
)
from stuf.tests.factories import SoapServiceFactory


class BookAppointmentForSubmissionTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        config = JccConfig.get_solo()
        wsdl = os.path.abspath(
            os.path.join(
                settings.DJANGO_PROJECT_DIR,
                "appointments/contrib/jcc/tests/mock/GenericGuidanceSystem2.wsdl",
            )
        )
        config.service = SoapServiceFactory.create(url=wsdl)
        config.save()

    def test_creating_appointment_with_no_appointment_information_does_nothing(self):
        submission = SubmissionFactory.create()
        book_appointment_for_submission(submission)
        submission.refresh_from_db()
        self.assertEqual(submission.appointment_information, "")

    def test_creating_appointment_with_missing_or_not_filled_in_appointment_information_adds_error_message(
        self,
    ):
        form_definition_1 = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {"key": "product", "showProducts": True},
                    {"key": "time", "showTimes": True},
                ],
            }
        )
        form_definition_2 = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {"key": "lastName", "appointmentLastName": True},
                    {"key": "birthDate", "appointmentBirthDate": True},
                ],
            }
        )
        submission = SubmissionFactory.create()
        SubmissionStepFactory.create(
            submission=submission,
            data={"product": "79", "time": "2021-08-25T17:00:00"},
            form_step=FormStepFactory.create(form_definition=form_definition_1),
        )
        SubmissionStepFactory.create(
            submission=submission,
            data={
                "lastName": "Maykin",
                "birthDate": "",
            },
            form_step=FormStepFactory.create(form_definition=form_definition_2),
        )
        book_appointment_for_submission(submission)
        submission.refresh_from_db()
        self.assertEqual(
            submission.appointment_information,
            "Missing information in form: locationID. Information not filled in by user: clientDateOfBirth. ",
        )

    @requests_mock.Mocker()
    def test_creating_appointment_properly_creates_appointment_and_adds_appointment_information(
        self, m
    ):
        form_definition_1 = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {"key": "product", "showProducts": True},
                    {"key": "location", "showLocations": True},
                    {"key": "time", "showTimes": True},
                ],
            }
        )
        form_definition_2 = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {"key": "lastName", "appointmentLastName": True},
                    {"key": "birthDate", "appointmentBirthDate": True},
                ],
            }
        )
        submission = SubmissionFactory.create()
        SubmissionStepFactory.create(
            submission=submission,
            data={"product": "79", "location": "1", "time": "2021-08-25T17:00:00"},
            form_step=FormStepFactory.create(form_definition=form_definition_1),
        )
        SubmissionStepFactory.create(
            submission=submission,
            data={
                "lastName": "Maykin",
                "birthDate": "1990-08-01",
            },
            form_step=FormStepFactory.create(form_definition=form_definition_2),
        )

        m.post(
            "http://example.com/soap11",
            text=mock_response("bookGovAppointmentResponse.xml"),
        )

        book_appointment_for_submission(submission)
        submission.refresh_from_db()
        self.assertEqual(
            submission.appointment_information, "Appointment Id: 1234567890"
        )

    @requests_mock.Mocker()
    def test_failed_creating_appointment_adds_error_message_to_submission(self, m):
        form_definition_1 = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {"key": "product", "showProducts": True},
                    {"key": "location", "showLocations": True},
                    {"key": "time", "showTimes": True},
                ],
            }
        )
        form_definition_2 = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {"key": "lastName", "appointmentLastName": True},
                    {"key": "birthDate", "appointmentBirthDate": True},
                ],
            }
        )
        submission = SubmissionFactory.create()
        SubmissionStepFactory.create(
            submission=submission,
            data={"product": "79", "location": "1", "time": "2021-08-25T17:00:00"},
            form_step=FormStepFactory.create(form_definition=form_definition_1),
        )
        SubmissionStepFactory.create(
            submission=submission,
            data={
                "lastName": "Maykin",
                "birthDate": "1990-08-01",
            },
            form_step=FormStepFactory.create(form_definition=form_definition_2),
        )

        m.post(
            "http://example.com/soap11",
            exc=AppointmentCreateFailed,
        )

        book_appointment_for_submission(submission)
        submission.refresh_from_db()
        self.assertEqual(
            submission.appointment_information, "Failed to make appointment"
        )
