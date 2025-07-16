from django.core.exceptions import ObjectDoesNotExist
from django.test import SimpleTestCase, TestCase

from openforms.submissions.tests.factories import SubmissionFactory

from ..models import Appointment, AppointmentProduct
from .factories import AppointmentInfoFactory


class TestRelationBetweenAppointmentInfoAndSubmissions(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.submission = SubmissionFactory.create()
        self.appointment_info = AppointmentInfoFactory.create(
            submission=self.submission
        )

    def test_deleting_submission_also_deletes_appointment_info(self):
        self.submission.delete()
        with self.assertRaises(ObjectDoesNotExist):
            self.appointment_info.refresh_from_db()

    def test_deleting_appointment_info_does_not_delete_submission(self):
        self.appointment_info.delete()
        try:
            self.submission.refresh_from_db()
        except ObjectDoesNotExist:
            self.fail("Submission was deleted when it should not have been")


class AppointmentModelTests(SimpleTestCase):
    def test_model_str_for_unsaved_instance(self):
        instance = Appointment()

        result = str(instance)

        self.assertIsInstance(result, str)


class AppointmentProductTests(SimpleTestCase):
    def test_model_str_for_unsaved_instance(self):
        instance = AppointmentProduct()

        result = str(instance)

        self.assertIsInstance(result, str)
