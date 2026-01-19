from datetime import datetime, time
from unittest.mock import patch

from django.test import override_settings
from django.utils import timezone
from django.utils.translation import gettext as _

from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse, reverse_lazy
from rest_framework.test import APITestCase

from openforms.config.models import GlobalConfiguration
from openforms.forms.constants import SubmissionAllowedChoices
from openforms.submissions.constants import PostSubmissionEvents
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.submissions.tests.mixins import SubmissionsMixin

from ..models import Appointment, AppointmentsConfig

ENDPOINT = reverse_lazy("api:appointments-create")
TODAY = timezone.localdate()


class ConfigPatchMixin:
    def setUp(self):
        super().setUp()  # type: ignore
        self.config = AppointmentsConfig(plugin="demo", limit_to_location="1")
        paths = [
            "openforms.appointments.utils.AppointmentsConfig.get_solo",
            "openforms.appointments.api.serializers.AppointmentsConfig.get_solo",
        ]
        for path in paths:
            patcher = patch(path, return_value=self.config)
            patcher.start()
            self.addCleanup(patcher.stop)  # type: ignore

        self.global_configuration = GlobalConfiguration(ask_privacy_consent=True)
        global_config_patcher = patch(
            "openforms.forms.models.form.GlobalConfiguration.get_solo",
            return_value=self.global_configuration,
        )
        global_config_patcher.start()
        self.addCleanup(global_config_patcher.stop)  # type: ignore


class AppointmentCreateSuccessTests(ConfigPatchMixin, SubmissionsMixin, APITestCase):
    """
    Test the appointment create happy flow.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.submission = SubmissionFactory.create(form__is_appointment_form=True)

    def setUp(self):
        super().setUp()
        self._add_submission_to_session(self.submission)

    def test_appointment_data_is_recorded(self):
        appointment_datetime = timezone.make_aware(
            datetime.combine(TODAY, time(15, 15))
        )
        data = {
            "submission": reverse(
                "api:submission-detail", kwargs={"uuid": self.submission.uuid}
            ),
            "products": [
                {
                    "productId": "2",
                    "amount": 1,
                }
            ],
            "location": "1",
            "date": TODAY.isoformat(),
            "datetime": appointment_datetime.isoformat(),
            "contactDetails": {
                "lastName": "Periwinkle",
                "email": "user@example.com",
            },
            "privacy_policy_accepted": True,
        }

        response = self.client.post(ENDPOINT, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        appointment = Appointment.objects.get()
        self.assertEqual(appointment.submission, self.submission)
        self.assertEqual(appointment.plugin, "demo")
        self.assertEqual(appointment.location, "1")
        self.assertEqual(appointment.datetime, appointment_datetime)
        self.assertEqual(
            appointment.contact_details_meta,
            [
                {
                    "key": "lastName",
                    "type": "textfield",
                    "label": _("Last name"),
                    "validate": {"required": True, "maxLength": 20},
                },
                {
                    "key": "email",
                    "type": "email",
                    "label": _("Email"),
                    "validate": {"required": True, "maxLength": 100},
                },
            ],
        )
        self.assertEqual(
            appointment.contact_details,
            {"email": "user@example.com", "lastName": "Periwinkle"},
        )
        products = appointment.products.all()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].product_id, "2")
        self.assertEqual(products[0].amount, 1)

        self.submission.refresh_from_db()
        self.assertTrue(self.submission.privacy_policy_accepted)

    @patch("openforms.submissions.api.mixins.on_post_submission_event")
    def test_submission_is_completed(self, mock_on_post_submission_event):
        appointment_datetime = timezone.make_aware(
            datetime.combine(TODAY, time(15, 15))
        )
        data = {
            "submission": reverse(
                "api:submission-detail", kwargs={"uuid": self.submission.uuid}
            ),
            "products": [
                {
                    "productId": "2",
                    "amount": 1,
                }
            ],
            "location": "1",
            "date": TODAY,
            "datetime": appointment_datetime.isoformat(),
            "contactDetails": {
                "lastName": "Periwinkle",
                "email": "user@example.com",
            },
            "privacy_policy_accepted": True,
        }

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(ENDPOINT, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.submission.refresh_from_db()
        self.assertTrue(self.submission.is_completed)
        self.assertIn("statusUrl", response.json())

        # assert that the async celery task execution is scheduled
        mock_on_post_submission_event.assert_called_once_with(
            self.submission.id, PostSubmissionEvents.on_completion
        )

    def test_retry_does_not_cause_integrity_error(self):
        # When there are on_completion processing errors, the client will re-post the
        # same state. This must update the existing appointment rather than trying to
        # create a new one.
        appointment_datetime = timezone.make_aware(
            datetime.combine(TODAY, time(15, 15))
        )
        data = {
            "submission": reverse(
                "api:submission-detail", kwargs={"uuid": self.submission.uuid}
            ),
            "products": [{"productId": "2", "amount": 1}],
            "location": "1",
            "date": TODAY,
            "datetime": appointment_datetime.isoformat(),
            "contactDetails": {
                "lastName": "Periwinkle",
                "email": "user@example.com",
            },
            "privacy_policy_accepted": True,
        }
        # first POST
        response = self.client.post(ENDPOINT, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # retry attempt - SubmissionProcessingStatus.ensure_failure_can_be_managed adds
        # the submission ID back to the session
        self._add_submission_to_session(self.submission)
        updated_data = {
            **data,
            "contactDetails": {
                "lastName": "Periwinkle",
                "firstName": "Caro",
                "email": "user@example.com",
            },
        }
        response = self.client.post(ENDPOINT, updated_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Appointment.objects.count(), 1)
        appointment = Appointment.objects.get()
        self.assertEqual(
            appointment.contact_details,
            {
                "lastName": "Periwinkle",
                "firstName": "Caro",
                "email": "user@example.com",
            },
        )

    def test_privacy_policy_not_required(self):
        self.global_configuration.ask_privacy_consent = False
        appointment_datetime = timezone.make_aware(
            datetime.combine(TODAY, time(15, 15))
        )
        data = {
            "submission": reverse(
                "api:submission-detail", kwargs={"uuid": self.submission.uuid}
            ),
            "products": [
                {
                    "productId": "2",
                    "amount": 1,
                }
            ],
            "location": "1",
            "date": TODAY.isoformat(),
            "datetime": appointment_datetime.isoformat(),
            "contactDetails": {
                "lastName": "Periwinkle",
                "email": "user@example.com",
            },
            "privacy_policy_accepted": False,
        }

        response = self.client.post(ENDPOINT, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class AppointmentCreateInvalidPermissionsTests(SubmissionsMixin, APITestCase):
    def test_no_submission_in_session(self):
        submission = SubmissionFactory.create(form__is_appointment_form=True)
        submission_url = reverse(
            "api:submission-detail", kwargs={"uuid": submission.uuid}
        )

        response = self.client.post(ENDPOINT, {"submission": submission_url})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_no_submission_in_request_body(self):
        submission = SubmissionFactory.create(form__is_appointment_form=True)
        self._add_submission_to_session(submission)

        empty_ish_bodies = [
            {},
            {"submission": None},
            {"submission": ""},
        ]
        for data in empty_ish_bodies:
            with self.subTest(json_data=data):
                response = self.client.post(ENDPOINT, data)

                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_different_submission_url_in_request_body(self):
        submission1, submission2 = SubmissionFactory.create_batch(
            2, form__is_appointment_form=True
        )
        self._add_submission_to_session(submission1)
        submission2_url = reverse(
            "api:submission-detail", kwargs={"uuid": submission2.uuid}
        )

        response = self.client.post(ENDPOINT, {"submission": submission2_url})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_submission_url_in_request_body(self):
        invalid_values = (False, True, 3.14, None, "", {"foo": "bar"}, ["nope"])
        for value in invalid_values:
            with self.subTest(value=value):
                response = self.client.post(ENDPOINT, {"submission": value})

                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_no_submission_allowed_on_form(self):
        submission = SubmissionFactory.create(
            form__is_appointment_form=True,
            form__submission_allowed=SubmissionAllowedChoices.no_with_overview,
        )
        self._add_submission_to_session(submission)
        submission_url = reverse(
            "api:submission-detail", kwargs={"uuid": submission.uuid}
        )

        response = self.client.post(ENDPOINT, {"submission": submission_url})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AppointmentCreateValidationErrorTests(
    ConfigPatchMixin, SubmissionsMixin, APITestCase
):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.submission = SubmissionFactory.create(form__is_appointment_form=True)

    def setUp(self):
        super().setUp()
        self._add_submission_to_session(self.submission)

    def test_required_privacy_policy_accept_missing(self):
        valid_data = {
            "submission": reverse(
                "api:submission-detail", kwargs={"uuid": self.submission.uuid}
            ),
            "products": [
                {
                    "productId": "2",
                    "amount": 1,
                }
            ],
            "location": "1",
            "date": TODAY.isoformat(),
            "datetime": f"{TODAY.isoformat()}T13:15:00Z",
            "contactDetails": {
                "lastName": "Periwinkle",
                "email": "user@example.com",
            },
        }

        invalid_privacy_policy_accepted_variants = [
            {"privacy_policy_accepted": None},
            {"privacy_policy_accepted": False},
            {"privacy_policy_accepted": ""},
            {"privacy_policy_accepted": "nope"},
            {},
        ]

        for variant in invalid_privacy_policy_accepted_variants:
            with self.subTest(privacy_policy_accepted=variant):
                data = {**valid_data, **variant}

                response = self.client.post(ENDPOINT, data)

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                invalid_params = response.json()["invalidParams"]
                self.assertEqual(len(invalid_params), 1)
                self.assertEqual(invalid_params[0]["name"], "privacyPolicyAccepted")

    def test_invalid_products(self):
        appointment_datetime = timezone.make_aware(
            datetime.combine(TODAY, time(15, 15))
        )
        base = {
            "submission": reverse(
                "api:submission-detail", kwargs={"uuid": self.submission.uuid}
            ),
            "location": "1",
            "date": TODAY.isoformat(),
            "datetime": appointment_datetime.isoformat(),
            "contactDetails": {
                "lastName": "Periwinkle",
                "email": "user@example.com",
            },
            "privacyPolicyAccepted": True,
        }

        with self.subTest("invalid product ID"):
            data = {
                **base,
                "products": [
                    {
                        "productId": "123",
                        "amount": 1,
                    }
                ],
            }

            response = self.client.post(ENDPOINT, data)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            invalid_params = response.json()["invalidParams"]
            self.assertEqual(len(invalid_params), 1)
            self.assertEqual(invalid_params[0]["name"], "products.0.productId")

        with self.subTest("invalid amount"):
            for amount in (0, -2, 4.2, "foo"):
                with self.subTest(amount=amount):
                    data = {
                        **base,
                        "products": [
                            {
                                "productId": "123",
                                "amount": amount,
                            }
                        ],
                    }

                    response = self.client.post(ENDPOINT, data)

                    self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                    invalid_params = response.json()["invalidParams"]
                    self.assertEqual(len(invalid_params), 1)
                    self.assertEqual(invalid_params[0]["name"], "products.0.amount")

        with self.subTest("plugin does not support multiple products"):
            data = {
                **base,
                "products": [
                    {
                        "productId": "1",
                        "amount": 1,
                    },
                    {
                        "productId": "2",
                        "amount": 1,
                    },
                ],
            }

            response = self.client.post(ENDPOINT, data)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            invalid_params = response.json()["invalidParams"]
            self.assertEqual(len(invalid_params), 1)
            self.assertEqual(invalid_params[0]["name"], "products")

    def test_invalid_location_with_fixed_location_in_config(self):
        # made up, but you can assume this is valid via the admin validation
        self.config.limit_to_location = "2"
        appointment_datetime = timezone.make_aware(
            datetime.combine(TODAY, time(15, 15))
        )
        data = {
            "submission": reverse(
                "api:submission-detail", kwargs={"uuid": self.submission.uuid}
            ),
            "products": [{"productId": "1", "amount": 1}],
            "location": "1",
            "date": TODAY.isoformat(),
            "datetime": appointment_datetime.isoformat(),
            "contactDetails": {
                "lastName": "Periwinkle",
                "email": "user@example.com",
            },
            "privacyPolicyAccepted": True,
        }

        response = self.client.post(ENDPOINT, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        invalid_params = response.json()["invalidParams"]
        self.assertEqual(len(invalid_params), 1)
        self.assertEqual(invalid_params[0]["name"], "location")

    def test_invalid_location_from_plugins_available_locations(self):
        # made up, but you can assume this is valid via the admin validation
        self.config.limit_to_location = ""
        appointment_datetime = timezone.make_aware(
            datetime.combine(TODAY, time(15, 15))
        )
        data = {
            "submission": reverse(
                "api:submission-detail", kwargs={"uuid": self.submission.uuid}
            ),
            "products": [{"productId": "1", "amount": 1}],
            "location": "123",
            "date": TODAY.isoformat(),
            "datetime": appointment_datetime.isoformat(),
            "contactDetails": {
                "lastName": "Periwinkle",
                "email": "user@example.com",
            },
            "privacyPolicyAccepted": True,
        }

        response = self.client.post(ENDPOINT, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        invalid_params = response.json()["invalidParams"]
        self.assertEqual(len(invalid_params), 1)
        self.assertEqual(invalid_params[0]["name"], "location")

    def test_invalid_date(self):
        appointment_datetime = timezone.make_aware(
            datetime.combine(TODAY, time(15, 15))
        )
        base = {
            "submission": reverse(
                "api:submission-detail", kwargs={"uuid": self.submission.uuid}
            ),
            "products": [{"productId": "1", "amount": 1}],
            "location": "1",
            "datetime": appointment_datetime.isoformat(),
            "contactDetails": {
                "lastName": "Periwinkle",
                "email": "user@example.com",
            },
            "privacyPolicyAccepted": True,
        }

        with self.subTest("not ISO 8601 date"):
            data = {**base, "date": "18/7/2023"}

            response = self.client.post(ENDPOINT, data)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            invalid_params = response.json()["invalidParams"]
            self.assertEqual(len(invalid_params), 1)
            self.assertEqual(invalid_params[0]["name"], "date")

        with self.subTest("date not available in backend"):
            # demo plugin only has 'today' available
            data = {**base, "date": "2021-01-01", "datetime": "2021-01-01T13:15:00Z"}

            response = self.client.post(ENDPOINT, data)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            invalid_params = response.json()["invalidParams"]
            self.assertEqual(len(invalid_params), 1)
            self.assertEqual(invalid_params[0]["name"], "date")

    @freeze_time("2023-07-18T07:42:00Z")  # pin to DST, UTC+2
    def test_invalid_datetime(self):
        today = timezone.localdate()
        base = {
            "submission": reverse(
                "api:submission-detail", kwargs={"uuid": self.submission.uuid}
            ),
            "products": [{"productId": "1", "amount": 1}],
            "location": "1",
            "date": today.isoformat(),
            "contactDetails": {
                "lastName": "Periwinkle",
                "email": "user@example.com",
            },
            "privacyPolicyAccepted": True,
        }

        with self.subTest("not ISO 8601 datetime"):
            data = {**base, "datetime": "12:00"}

            response = self.client.post(ENDPOINT, data)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            invalid_params = response.json()["invalidParams"]
            self.assertEqual(len(invalid_params), 1)
            self.assertEqual(invalid_params[0]["name"], "datetime")

        with self.subTest("different date part than date field"):
            data = {**base, "datetime": "2023-01-01T10:00:00Z"}

            response = self.client.post(ENDPOINT, data)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            invalid_params = response.json()["invalidParams"]
            self.assertEqual(len(invalid_params), 1)
            self.assertEqual(invalid_params[0]["name"], "date")

        with self.subTest("time slot not available in plugin (AMS timezone)"):
            data = {**base, "datetime": f"{today.isoformat()}T09:11:00+02:00"}

            response = self.client.post(ENDPOINT, data)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            invalid_params = response.json()["invalidParams"]
            self.assertEqual(len(invalid_params), 1)
            self.assertEqual(invalid_params[0]["name"], "datetime")

        with self.subTest("time slot not available in plugin (UTC timezone)"):
            data = {**base, "datetime": f"{today.isoformat()}T07:11:00Z"}

            response = self.client.post(ENDPOINT, data)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            invalid_params = response.json()["invalidParams"]
            self.assertEqual(len(invalid_params), 1)
            self.assertEqual(invalid_params[0]["name"], "datetime")

    def test_invalid_contact_details(self):
        appointment_datetime = timezone.make_aware(
            datetime.combine(TODAY, time(15, 15))
        )
        base = {
            "submission": reverse(
                "api:submission-detail", kwargs={"uuid": self.submission.uuid}
            ),
            "products": [{"productId": "1", "amount": 1}],
            "location": "1",
            "date": TODAY.isoformat(),
            "datetime": appointment_datetime.isoformat(),
            "privacyPolicyAccepted": True,
        }

        with self.subTest("missing contact details"):
            response = self.client.post(ENDPOINT, base)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            invalid_params = response.json()["invalidParams"]
            self.assertEqual(len(invalid_params), 1)
            self.assertEqual(invalid_params[0]["name"], "contactDetails")

        with self.subTest("missing required field"):
            data = {**base, "contactDetails": {}}

            response = self.client.post(ENDPOINT, data)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            invalid_params = response.json()["invalidParams"]
            self.assertEqual(len(invalid_params), 2)
            self.assertEqual(invalid_params[0]["name"], "contactDetails.lastName")
            self.assertEqual(invalid_params[0]["code"], "required")

            self.assertEqual(invalid_params[1]["name"], "contactDetails.email")
            self.assertEqual(invalid_params[1]["code"], "required")

        with self.subTest("value too long"):
            data = {
                **base,
                "contactDetails": {
                    "lastName": "abcd" * 6,
                    "email": "user" * 23 + "@example.com",
                },
            }  # 24 > 20 & 112>100

            response = self.client.post(ENDPOINT, data)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            invalid_params = response.json()["invalidParams"]

            self.assertEqual(len(invalid_params), 2)
            self.assertEqual(invalid_params[0]["name"], "contactDetails.lastName")
            self.assertEqual(invalid_params[0]["code"], "max_length")
            self.assertEqual(invalid_params[1]["name"], "contactDetails.email")
            self.assertEqual(invalid_params[1]["code"], "max_length")

    @override_settings(LANGUAGE_CODE="en")
    @patch(
        "openforms.appointments.contrib.demo.plugin.DemoAppointment.get_required_customer_fields"
    )
    def test_require_one_of_rule_in_contact_details(self, m):
        m.return_value = (
            [
                {
                    "type": "textfield",
                    "key": "lastName",
                    "label": "Last name",
                    "validate": {
                        "required": False,
                        "maxLength": 20,
                    },
                    "description": "At least one of the lastName, email must be filled in",
                },
                {
                    "type": "email",
                    "key": "email",
                    "label": "Email",
                    "validate": {
                        "required": False,
                        "maxLength": 100,
                    },
                    "description": "At least one of the lastName, email must be filled in",
                },
                {
                    "type": "textfield",
                    "key": "firstName",
                    "label": "First name",
                    "validate": {
                        "required": False,
                        "maxLength": 20,
                    },
                    "description": "At least one of the firstName, initials must be filled in",
                },
                {
                    "type": "textfield",
                    "key": "initials",
                    "label": "Initialen",
                    "autocomplete": "initials",
                    "validate": {"maxLength": 128, "required": False},
                    "description": "At least one of the firstName, initials must be filled in",
                },
            ],
            [
                {
                    "type": "require_one_of",
                    "fields": ("lastName", "email"),
                    "error_message": _(
                        "At least one of the {fields} is required."
                    ).format(fields=", ".join(("lastName", "email"))),
                },
                {
                    "type": "require_one_of",
                    "fields": ("firstName", "initials"),
                    "error_message": _(
                        "At least one of the {fields} is required."
                    ).format(fields=", ".join(("firstName", "initials"))),
                },
            ],
        )

        appointment_datetime = timezone.make_aware(
            datetime.combine(TODAY, time(15, 15))
        )
        base = {
            "submission": reverse(
                "api:submission-detail", kwargs={"uuid": self.submission.uuid}
            ),
            "products": [{"productId": "1", "amount": 1}],
            "location": "1",
            "date": TODAY.isoformat(),
            "datetime": appointment_datetime.isoformat(),
            "privacyPolicyAccepted": True,
        }

        data = {
            **base,
            "contactDetails": {
                "lastName": "",
                "email": "",
                "firstName": "",
                "initials": "",
            },
        }

        response = self.client.post(ENDPOINT, data)

        invalid_params = response.json()["invalidParams"]

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(invalid_params), 4)
        self.assertEqual(invalid_params[0]["name"], "contactDetails.lastName")
        self.assertEqual(
            invalid_params[0]["reason"],
            "At least one of the lastName, email is required.",
        )
        self.assertEqual(invalid_params[1]["name"], "contactDetails.email")
        self.assertEqual(
            invalid_params[1]["reason"],
            "At least one of the lastName, email is required.",
        )
        self.assertEqual(invalid_params[2]["name"], "contactDetails.firstName")
        self.assertEqual(
            invalid_params[2]["reason"],
            "At least one of the firstName, initials is required.",
        )
        self.assertEqual(invalid_params[3]["name"], "contactDetails.initials")
        self.assertEqual(
            invalid_params[3]["reason"],
            "At least one of the firstName, initials is required.",
        )

    @override_settings(LANGUAGE_CODE="en")
    @patch(
        "openforms.appointments.contrib.demo.plugin.DemoAppointment.get_required_customer_fields"
    )
    def test_require_one_of_rule_with_no_specific_error_message_in_contact_details(
        self, m
    ):
        m.return_value = (
            [
                {
                    "type": "textfield",
                    "key": "lastName",
                    "label": "Last name",
                    "validate": {
                        "required": False,
                        "maxLength": 20,
                    },
                    "description": "At least one of the lastName, email must be filled in",
                },
                {
                    "type": "email",
                    "key": "email",
                    "label": "Email",
                    "validate": {
                        "required": False,
                        "maxLength": 100,
                    },
                    "description": "At least one of the lastName, email must be filled in",
                },
            ],
            [
                {
                    "type": "require_one_of",
                    "fields": ("lastName", "email"),
                    "error_message": "",
                }
            ],
        )

        appointment_datetime = timezone.make_aware(
            datetime.combine(TODAY, time(15, 15))
        )
        base = {
            "submission": reverse(
                "api:submission-detail", kwargs={"uuid": self.submission.uuid}
            ),
            "products": [{"productId": "1", "amount": 1}],
            "location": "1",
            "date": TODAY.isoformat(),
            "datetime": appointment_datetime.isoformat(),
            "privacyPolicyAccepted": True,
        }

        data = {
            **base,
            "contactDetails": {
                "lastName": "",
                "email": "",
            },
        }

        response = self.client.post(ENDPOINT, data)

        invalid_params = response.json()["invalidParams"]

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(invalid_params), 2)
        self.assertEqual(invalid_params[0]["name"], "contactDetails.lastName")
        self.assertEqual(invalid_params[0]["reason"], "This field may not be blank.")
        self.assertEqual(invalid_params[1]["name"], "contactDetails.email")
        self.assertEqual(invalid_params[1]["reason"], "This field may not be blank.")

    @patch(
        "openforms.appointments.contrib.demo.plugin.DemoAppointment.get_required_customer_fields"
    )
    def test_require_one_of_rule_with_required_values_present(self, m):
        m.return_value = (
            [
                {
                    "type": "textfield",
                    "key": "lastName",
                    "label": "Last name",
                    "validate": {
                        "required": False,
                        "maxLength": 20,
                    },
                    "description": "At least one of the lastName, email must be filled in",
                },
                {
                    "type": "email",
                    "key": "email",
                    "label": "Email",
                    "validate": {
                        "required": False,
                        "maxLength": 100,
                    },
                    "description": "At least one of the lastName, email must be filled in",
                },
            ],
            [
                {
                    "type": "require_one_of",
                    "fields": ("lastName", "email"),
                    "error_message": "A message",
                }
            ],
        )

        appointment_datetime = timezone.make_aware(
            datetime.combine(TODAY, time(15, 15))
        )
        base = {
            "submission": reverse(
                "api:submission-detail", kwargs={"uuid": self.submission.uuid}
            ),
            "products": [{"productId": "1", "amount": 1}],
            "location": "1",
            "date": TODAY.isoformat(),
            "datetime": appointment_datetime.isoformat(),
            "privacyPolicyAccepted": True,
        }

        data = {
            **base,
            "contactDetails": {
                "lastName": "Boei",
                "email": "",
            },
        }

        response = self.client.post(ENDPOINT, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @patch(
        "openforms.appointments.contrib.demo.plugin.DemoAppointment.get_required_customer_fields"
    )
    def test_unknown_rule_is_ignored(self, m):
        m.return_value = (
            [
                {
                    "type": "textfield",
                    "key": "lastName",
                    "label": "Last name",
                    "validate": {
                        "required": False,
                        "maxLength": 20,
                    },
                    "description": "At least one of the lastName, email must be filled in",
                },
                {
                    "type": "email",
                    "key": "email",
                    "label": "Email",
                    "validate": {
                        "required": False,
                        "maxLength": 100,
                    },
                    "description": "At least one of the lastName, email must be filled in",
                },
            ],
            [
                {
                    "type": "non_existing",
                    "fields": ("lastName", "email"),
                    "error_message": "A message",
                }
            ],
        )

        appointment_datetime = timezone.make_aware(
            datetime.combine(TODAY, time(15, 15))
        )
        base = {
            "submission": reverse(
                "api:submission-detail", kwargs={"uuid": self.submission.uuid}
            ),
            "products": [{"productId": "1", "amount": 1}],
            "location": "1",
            "date": TODAY.isoformat(),
            "datetime": appointment_datetime.isoformat(),
            "privacyPolicyAccepted": True,
        }

        data = {
            **base,
            "contactDetails": {
                "lastName": "",
                "email": "",
            },
        }

        response = self.client.post(ENDPOINT, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
