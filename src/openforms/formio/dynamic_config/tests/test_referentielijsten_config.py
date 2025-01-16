from pathlib import Path

from django.test import TestCase, tag
from django.utils.translation import gettext as _

import requests_mock
from requests import RequestException
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from zgw_consumers.constants import AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from openforms.formio.components.vanilla import Select, SelectBoxes
from openforms.forms.tests.factories import FormFactory
from openforms.logging.models import TimelineLogProxy
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.submissions.tests.mixins import SubmissionsMixin
from openforms.utils.tests.cache import clear_caches
from openforms.utils.tests.vcr import OFVCRMixin

from ...dynamic_config.dynamic_options import DynamicOptionException

TESTS_DIR = Path(__file__).parent.resolve()
TEST_FILES = TESTS_DIR / "files"


@tag("gh-4993")
class SelectReferentielijstenOptionsTests(OFVCRMixin, TestCase):
    VCR_TEST_FILES = TEST_FILES

    def setUp(self):
        super().setUp()

        self.service = ServiceFactory.create(
            api_root="http://localhost:8004/api/v1/",
            slug="referentielijsten",
            auth_type=AuthTypes.no_auth,
        )
        self.component = {
            "key": "select",
            "type": "select",
            "label": "Select",
            "values": [{"label": "", "value": ""}],
            "dataType": "string",
            "openForms": {
                "code": "tabel1",
                "dataSrc": "referentielijsten",
                "service": self.service.slug,
                "translations": {},
            },
            "id": "ew0bwv7",
        }
        self.submission = SubmissionFactory.create()

        # The requests to Referentielijsten are cached, we need to make sure
        # that the cache is reset between tests to correctly test different scenarios
        self.addCleanup(clear_caches)

    def test_success(self):
        Select("select").mutate_config_dynamically(self.component, self.submission, {})

        self.assertEqual(
            self.component["data"]["values"],
            [
                {"label": "Option 1", "value": "option1"},
                {"label": "Option 2", "value": "option2"},
            ],
        )

    def test_table_with_paginated_items(self):
        self.component["openForms"]["code"] = "tabel-with-many-items"

        Select("select").mutate_config_dynamically(self.component, self.submission, {})

        self.assertEqual(
            self.component["data"]["values"],
            [{"label": str(i), "value": str(i)} for i in range(101)],
        )

    def test_no_service_configured(self):
        self.component["openForms"]["service"] = ""

        with self.assertRaises(DynamicOptionException):
            Select("select").mutate_config_dynamically(
                self.component, self.submission, {}
            )

        self.assertNotIn("data", self.component)
        log = TimelineLogProxy.objects.get(object_id=self.submission.form.id)
        assert log.extra_data
        self.assertEqual(log.template, "logging/events/form_configuration_error.txt")
        self.assertEqual(
            log.extra_data["error"],
            _(
                "Cannot fetch from Referentielijsten API, because no `service` is configured."
            ),
        )

    def test_no_code_configured(self):
        self.component["openForms"]["code"] = ""

        with self.assertRaises(DynamicOptionException):
            Select("select").mutate_config_dynamically(
                self.component, self.submission, {}
            )

        self.assertNotIn("data", self.component)
        log = TimelineLogProxy.objects.get(object_id=self.submission.form.id)
        assert log.extra_data
        self.assertEqual(log.template, "logging/events/form_configuration_error.txt")
        self.assertEqual(
            log.extra_data["error"],
            _(
                "Cannot fetch from Referentielijsten API, because no `code` is configured."
            ),
        )

    def test_service_does_not_exist(self):
        self.service.delete()

        with self.assertRaises(DynamicOptionException):
            Select("select").mutate_config_dynamically(
                self.component, self.submission, {}
            )

        self.assertNotIn("data", self.component)
        log = TimelineLogProxy.objects.get(object_id=self.submission.form.id)
        assert log.extra_data
        self.assertEqual(log.template, "logging/events/form_configuration_error.txt")
        self.assertEqual(
            log.extra_data["error"],
            _(
                "Cannot fetch from Referentielijsten API, service with {service_slug} does not exist."
            ).format(service_slug=self.service.slug),
        )

    def test_items_not_found(self):
        self.component["openForms"]["code"] = "non-existent"

        with self.assertRaises(DynamicOptionException):
            Select("select").mutate_config_dynamically(
                self.component, self.submission, {}
            )

        self.assertNotIn("data", self.component)
        log = TimelineLogProxy.objects.get(object_id=self.submission.form.id)
        assert log.extra_data
        self.assertEqual(
            log.template, "logging/events/referentielijsten_failure_response.txt"
        )
        self.assertEqual(
            log.extra_data["error"],
            _("No results found from Referentielijsten API."),
        )

    @requests_mock.Mocker()
    def test_request_exception(self, m):
        m.get(
            f"{self.service.api_root}items?tabel__code=tabel1",
            exc=RequestException("something went wrong"),
        )

        with self.assertRaises(DynamicOptionException):
            Select("select").mutate_config_dynamically(
                self.component, self.submission, {}
            )

        self.assertNotIn("data", self.component)
        log = TimelineLogProxy.objects.get(object_id=self.submission.form.id)
        assert log.extra_data
        self.assertEqual(
            log.template, "logging/events/referentielijsten_failure_response.txt"
        )
        self.assertEqual(
            log.extra_data["error"],
            _(
                "Exception occurred while fetching from Referentielijsten API: something went wrong."
            ),
        )


@tag("gh-4993")
class SelectboxesReferentielijstenOptionsTests(OFVCRMixin, TestCase):
    VCR_TEST_FILES = TEST_FILES

    def setUp(self):
        super().setUp()

        self.service = ServiceFactory.create(
            api_root="http://localhost:8004/api/v1/",
            slug="referentielijsten",
            auth_type=AuthTypes.no_auth,
        )
        self.component = {
            "key": "selectboxes",
            "type": "selectboxes",
            "label": "Selectboxes",
            "values": [{"label": "", "value": ""}],
            "dataType": "string",
            "openForms": {
                "code": "tabel1",
                "dataSrc": "referentielijsten",
                "service": self.service.slug,
                "translations": {},
            },
            "id": "ew0bwv7",
        }
        self.submission = SubmissionFactory.create()

        # The requests to Referentielijsten are cached, we need to make sure
        # that the cache is reset between tests to correctly test different scenarios
        self.addCleanup(clear_caches)

    def test_success(self):
        Select("selectboxes").mutate_config_dynamically(
            self.component, self.submission, {}
        )

        self.assertEqual(
            self.component["data"]["values"],
            [
                {"label": "Option 1", "value": "option1"},
                {"label": "Option 2", "value": "option2"},
            ],
        )

    def test_no_service_configured(self):
        self.component["openForms"]["service"] = ""

        with self.assertRaises(DynamicOptionException):
            SelectBoxes("selectboxes").mutate_config_dynamically(
                self.component, self.submission, {}
            )

        self.assertNotIn("data", self.component)
        log = TimelineLogProxy.objects.get(object_id=self.submission.form.id)
        assert log.extra_data
        self.assertEqual(log.template, "logging/events/form_configuration_error.txt")
        self.assertEqual(
            log.extra_data["error"],
            _(
                "Cannot fetch from Referentielijsten API, because no `service` is configured."
            ),
        )

    def test_no_code_configured(self):
        self.component["openForms"]["code"] = ""

        with self.assertRaises(DynamicOptionException):
            SelectBoxes("selectboxes").mutate_config_dynamically(
                self.component, self.submission, {}
            )

        self.assertNotIn("data", self.component)
        log = TimelineLogProxy.objects.get(object_id=self.submission.form.id)
        assert log.extra_data
        self.assertEqual(log.template, "logging/events/form_configuration_error.txt")
        self.assertEqual(
            log.extra_data["error"],
            _(
                "Cannot fetch from Referentielijsten API, because no `code` is configured."
            ),
        )

    def test_service_does_not_exist(self):
        self.service.delete()

        with self.assertRaises(DynamicOptionException):
            SelectBoxes("selectboxes").mutate_config_dynamically(
                self.component, self.submission, {}
            )

        self.assertNotIn("data", self.component)
        log = TimelineLogProxy.objects.get(object_id=self.submission.form.id)
        assert log.extra_data
        self.assertEqual(log.template, "logging/events/form_configuration_error.txt")
        self.assertEqual(
            log.extra_data["error"],
            _(
                "Cannot fetch from Referentielijsten API, service with {service_slug} does not exist."
            ).format(service_slug=self.service.slug),
        )

    def test_items_not_found(self):
        self.component["openForms"]["code"] = "non-existent"

        with self.assertRaises(DynamicOptionException):
            SelectBoxes("selectboxes").mutate_config_dynamically(
                self.component, self.submission, {}
            )

        self.assertNotIn("data", self.component)
        log = TimelineLogProxy.objects.get(object_id=self.submission.form.id)
        assert log.extra_data
        self.assertEqual(
            log.template, "logging/events/referentielijsten_failure_response.txt"
        )
        self.assertEqual(
            log.extra_data["error"],
            _("No results found from Referentielijsten API."),
        )

    @requests_mock.Mocker()
    def test_request_exception(self, m):
        m.get(
            f"{self.service.api_root}items?tabel__code=tabel1",
            exc=RequestException("something went wrong"),
        )

        with self.assertRaises(DynamicOptionException):
            SelectBoxes("selectboxes").mutate_config_dynamically(
                self.component, self.submission, {}
            )

        self.assertNotIn("data", self.component)
        log = TimelineLogProxy.objects.get(object_id=self.submission.form.id)
        assert log.extra_data
        self.assertEqual(
            log.template, "logging/events/referentielijsten_failure_response.txt"
        )
        self.assertEqual(
            log.extra_data["error"],
            _(
                "Exception occurred while fetching from Referentielijsten API: something went wrong."
            ),
        )


@tag("gh-4993")
class SubmissionStepDetailTest(SubmissionsMixin, APITestCase):
    def test_get_submissionstep_detail_raises_error_for_referentielijsten_if_service_is_incorrect(
        self,
    ):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "selectboxes",
                        "type": "selectboxes",
                        "label": "Selectboxes",
                        "values": [{"label": "", "value": ""}],
                        "dataType": "string",
                        "openForms": {
                            "code": "tabel1",
                            "dataSrc": "referentielijsten",
                            "service": "non-existent",
                            "translations": {},
                        },
                        "id": "ew0bwv7",
                    }
                ]
            },
        )
        submission = SubmissionFactory.create(form=form)
        endpoint = reverse(
            "api:submission-steps-detail",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": form.formstep_set.get().uuid,
            },
        )
        self._add_submission_to_session(submission)

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        # the detail message should be passed for errors that occur when fetching referentielijsten
        self.assertEqual(
            response.json()["detail"],
            _(
                "Loading the form failed due to problems with an external system, please try again later"
            ),
        )
