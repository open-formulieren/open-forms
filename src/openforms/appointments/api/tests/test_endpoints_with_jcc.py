import os

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

import requests_mock
from zeep.exceptions import Error as ZeepError

from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
)
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionStepFactory,
)
from openforms.submissions.tests.mixins import SubmissionsMixin
from stuf.tests.factories import SoapServiceFactory

from ...contrib.jcc.models import JccConfig
from ...contrib.jcc.tests.test_plugin import mock_response
from ...models import AppointmentsConfig
from ...tests.factories import AppointmentInfoFactory


class ProductsListTests(SubmissionsMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.submission = SubmissionFactory.create()
        cls.endpoint = reverse("api:appointments-products-list")

        appointments_config = AppointmentsConfig.get_solo()
        appointments_config.config_path = (
            "openforms.appointments.contrib.jcc.models.JccConfig"
        )
        appointments_config.save()

        config = JccConfig.get_solo()
        wsdl = os.path.abspath(
            os.path.join(
                settings.DJANGO_PROJECT_DIR,
                "appointments/contrib/jcc/tests/mock/GenericGuidanceSystem2.wsdl",
            )
        )
        config.service = SoapServiceFactory.create(url=wsdl)
        config.save()

    @requests_mock.Mocker()
    def test_get_products_returns_all_products(self, m):
        self._add_submission_to_session(self.submission)
        m.post(
            "http://example.com/soap11",
            text=mock_response("getGovAvailableProductsResponse.xml"),
        )

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 3)
        first_entry = response.json()[0]
        self.assertEqual(first_entry["code"], "PASAAN")
        self.assertEqual(first_entry["identifier"], "1")
        self.assertEqual(first_entry["name"], "Paspoort aanvraag")

    def test_get_products_returns_403_when_no_active_sessions(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, 403)


class LocationsListTests(SubmissionsMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.submission = SubmissionFactory.create()
        cls.endpoint = reverse("api:appointments-locations-list")

        appointments_config = AppointmentsConfig.get_solo()
        appointments_config.config_path = (
            "openforms.appointments.contrib.jcc.models.JccConfig"
        )
        appointments_config.save()

        config = JccConfig.get_solo()
        wsdl = os.path.abspath(
            os.path.join(
                settings.DJANGO_PROJECT_DIR,
                "appointments/contrib/jcc/tests/mock/GenericGuidanceSystem2.wsdl",
            )
        )
        config.service = SoapServiceFactory.create(url=wsdl)
        config.save()

    def setUp(self):
        super().setUp()
        self._add_submission_to_session(self.submission)

    @requests_mock.Mocker()
    def test_get_locations_returns_all_locations_for_a_product(self, m):
        m.post(
            "http://example.com/soap11",
            text=mock_response("getGovLocationsForProductResponse.xml"),
        )

        response = self.client.get(f"{self.endpoint}?product_id=79")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        location = response.json()[0]
        self.assertEqual(location["identifier"], "1")
        self.assertEqual(location["name"], "Maykin Media")

    def test_get_locations_returns_400_when_no_product_id_is_given(self):
        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, 400)

    def test_get_locations_returns_403_when_no_active_sessions(self):
        self._clear_session()
        response = self.client.get(f"{self.endpoint}?product_id=1&location_id=1")
        self.assertEqual(response.status_code, 403)


class DatesListTests(SubmissionsMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.submission = SubmissionFactory.create()
        cls.endpoint = reverse("api:appointments-dates-list")

        appointments_config = AppointmentsConfig.get_solo()
        appointments_config.config_path = (
            "openforms.appointments.contrib.jcc.models.JccConfig"
        )
        appointments_config.save()

        config = JccConfig.get_solo()
        wsdl = os.path.abspath(
            os.path.join(
                settings.DJANGO_PROJECT_DIR,
                "appointments/contrib/jcc/tests/mock/GenericGuidanceSystem2.wsdl",
            )
        )
        config.service = SoapServiceFactory.create(url=wsdl)
        config.save()

    def setUp(self):
        super().setUp()
        self._add_submission_to_session(self.submission)

    @requests_mock.Mocker()
    def test_get_dates_returns_all_dates_for_a_give_location_and_product(self, m):
        m.post(
            "http://example.com/soap11",
            [
                {"text": mock_response("getGovLatestPlanDateResponse.xml")},
                {"text": mock_response("getGovAvailableDaysResponse.xml")},
            ],
        )

        response = self.client.get(f"{self.endpoint}?product_id=1&location_id=1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            [{"date": "2021-08-19"}, {"date": "2021-08-20"}, {"date": "2021-08-23"}],
        )

    def test_get_dates_returns_400_when_missing_query_params(self):
        for query_param in [{}, {"product_id": 79}, {"location_id": 1}]:
            with self.subTest(query_param=query_param):
                response = self.client.get(self.endpoint, query_param)
                self.assertEqual(response.status_code, 400)

    def test_get_dates_returns_403_when_no_active_sessions(self):
        self._clear_session()
        response = self.client.get(f"{self.endpoint}?product_id=1&location_id=1")
        self.assertEqual(response.status_code, 403)


class TimesListTests(SubmissionsMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.submission = SubmissionFactory.create()
        cls.endpoint = reverse("api:appointments-times-list")

        appointments_config = AppointmentsConfig.get_solo()
        appointments_config.config_path = (
            "openforms.appointments.contrib.jcc.models.JccConfig"
        )
        appointments_config.save()

        config = JccConfig.get_solo()
        wsdl = os.path.abspath(
            os.path.join(
                settings.DJANGO_PROJECT_DIR,
                "appointments/contrib/jcc/tests/mock/GenericGuidanceSystem2.wsdl",
            )
        )
        config.service = SoapServiceFactory.create(url=wsdl)
        config.save()

    def setUp(self):
        super().setUp()
        self._add_submission_to_session(self.submission)

    @requests_mock.Mocker()
    def test_get_times_returns_all_times_for_a_give_location_product_and_date(self, m):

        m.post(
            "http://example.com/soap11",
            text=mock_response("getGovAvailableTimesPerDayResponse.xml"),
        )

        response = self.client.get(
            f"{self.endpoint}?product_id=1&location_id=1&date=2021-8-23"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 106)
        self.assertEqual(response.json()[0], {"time": "2021-08-23T08:00:00+02:00"})

    def test_get_times_returns_400_when_missing_query_params(self):
        for query_param in [
            {},
            {"product_id": 79},
            {"location_id": 1},
            {"location_id": 1, "date": 2021 - 8 - 23},
            {"product_id": 1, "date": 2021 - 8 - 23},
            {"product_id": 1, "location_id": 1},
        ]:
            with self.subTest(query_param=query_param):
                response = self.client.get(self.endpoint, query_param)
                self.assertEqual(response.status_code, 400)

    def test_get_times_returns_403_when_no_active_sessions(self):
        self._clear_session()
        response = self.client.get(
            f"{self.endpoint}?product_id=1&location_id=1&date=2021-8-23"
        )
        self.assertEqual(response.status_code, 403)


class CancelAppointmentTests(SubmissionsMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.submission = SubmissionFactory.create()
        cls.endpoint = reverse(
            "api:appointments-cancel",
            kwargs={"submission_uuid": str(cls.submission.uuid)},
        )

        appointments_config = AppointmentsConfig.get_solo()
        appointments_config.config_path = (
            "openforms.appointments.contrib.jcc.models.JccConfig"
        )
        appointments_config.save()

        config = JccConfig.get_solo()
        wsdl = os.path.abspath(
            os.path.join(
                settings.DJANGO_PROJECT_DIR,
                "appointments/contrib/jcc/tests/mock/GenericGuidanceSystem2.wsdl",
            )
        )
        config.service = SoapServiceFactory.create(url=wsdl)
        config.save()

    @requests_mock.Mocker()
    def test_cancel_appointment_deletes_the_appointment(self, m):
        self._add_submission_to_session(self.submission)
        AppointmentInfoFactory.create(submission=self.submission)
        form = FormFactory.create(slug="a-form", name="A form")

        form_def = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {"key": "email", "label": "Email", "confirmationRecipient": True},
                ],
            }
        )

        form_step = FormStepFactory.create(form=form, form_definition=form_def)

        self.submission.form = form
        self.submission.save()

        SubmissionStepFactory.create(
            submission=self.submission,
            data={
                "email": "maykin@media.nl",
            },
            form_step=form_step,
        )

        m.post(
            "http://example.com/soap11",
            text=mock_response("deleteGovAppointmentResponse.xml"),
        )

        data = {
            "email": "maykin@media.nl",
        }

        response = self.client.post(self.endpoint, data=data)

        self.assertEqual(response.status_code, 204)

    @requests_mock.Mocker()
    def test_cancel_appointment_properly_handles_plugin_exception(self, m):
        self._add_submission_to_session(self.submission)
        form = FormFactory.create(slug="a-form", name="A form")

        form_def = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {"key": "email", "label": "Email", "confirmationRecipient": True},
                ],
            }
        )

        form_step = FormStepFactory.create(form=form, form_definition=form_def)

        self.submission.form = form
        self.submission.save()

        SubmissionStepFactory.create(
            submission=self.submission,
            data={
                "email": "maykin@media.nl",
            },
            form_step=form_step,
        )

        m.post(
            "http://example.com/soap11",
            exc=ZeepError,
        )

        data = {
            "email": "maykin@media.nl",
        }

        response = self.client.post(self.endpoint, data=data)

        self.assertEqual(response.status_code, 502)

    def test_cancel_appointment_returns_403_when_no_appointment_is_in_session(self):
        data = {
            "email": "maykin@media.nl",
        }

        response = self.client.post(self.endpoint, data=data)

        self.assertEqual(response.status_code, 403)
