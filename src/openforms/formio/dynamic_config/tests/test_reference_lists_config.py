from django.test import TestCase, tag
from django.utils.translation import gettext as _

import requests_mock
from requests import RequestException
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from zgw_consumers.constants import AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from formio_types import Option, Radio, Select, Selectboxes
from formio_types.radio import RadioExtensions
from formio_types.select import SelectData, SelectExtensions
from formio_types.selectboxes import SelectboxesExtensions
from openforms.api.exceptions import ServiceUnavailable
from openforms.forms.tests.factories import FormFactory
from openforms.logging.models import TimelineLogProxy
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.submissions.tests.mixins import SubmissionsMixin
from openforms.utils.tests.cache import clear_caches
from openforms.utils.tests.vcr import OFVCRMixin

from ...constants import DataSrcOptions
from ...datastructures import FormioData
from ...registry import register


@tag("gh-4993")
class SelectReferenceListsOptionsTests(OFVCRMixin, TestCase):
    def setUp(self):
        super().setUp()

        # The requests to Referentielijsten are cached, we need to make sure
        # that the cache is reset between tests to correctly test different scenarios
        self.addCleanup(clear_caches)

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.service = ServiceFactory.create(
            api_root="http://localhost:8004/api/v1/",
            slug="reference-lists",
            auth_type=AuthTypes.no_auth,
        )
        cls.submission = SubmissionFactory.create()

    def test_success(self):
        component = Select(
            key="select",
            label="Select",
            data=SelectData(),
            data_type="string",
            open_forms=SelectExtensions(
                data_src=DataSrcOptions.reference_lists.value,
                service=self.service.slug,
                code="tabel1",
                translations={},
            ),
        )

        register.update_config(component, submission=self.submission, data=FormioData())

        self.assertEqual(
            component.data.values,
            [
                Option(label="Option 2", value="option2"),
                Option(label="Option 1", value="option1"),
            ],
        )

    def test_table_with_paginated_items(self):
        component = Select(
            key="select",
            label="Select",
            data=SelectData(),
            data_type="string",
            open_forms=SelectExtensions(
                data_src=DataSrcOptions.reference_lists.value,
                service=self.service.slug,
                code="tabel-with-many-items",
                translations={},
            ),
        )

        register.update_config(component, submission=self.submission, data=FormioData())

        values = reversed(component.data.values)
        self.assertEqual(
            list(values),
            [Option(label=str(i), value=str(i)) for i in range(101)],
        )

    def test_no_service_configured(self):
        component = Select(
            key="select",
            label="Select",
            data=SelectData(),
            data_type="string",
            open_forms=SelectExtensions(
                data_src=DataSrcOptions.reference_lists.value,
                service="",
                code="tabel1",
                translations={},
            ),
        )

        with self.assertRaises(ServiceUnavailable):
            register.update_config(
                component, submission=self.submission, data=FormioData()
            )

        self.assertEqual(component.data.values, [])
        log = TimelineLogProxy.objects.for_object(self.submission.form).get()
        assert log.extra_data
        self.assertEqual(log.template, "logging/events/form_configuration_error.txt")
        self.assertEqual(
            log.extra_data["error"],
            _(
                "Cannot fetch from ReferenceLists API, because no `service` is configured."
            ),
        )

    def test_no_code_configured(self):
        component = Select(
            key="select",
            label="Select",
            data=SelectData(),
            data_type="string",
            open_forms=SelectExtensions(
                data_src=DataSrcOptions.reference_lists.value,
                service=self.service.slug,
                code="",
                translations={},
            ),
        )

        with self.assertRaises(ServiceUnavailable):
            register.update_config(
                component, submission=self.submission, data=FormioData()
            )

        self.assertEqual(component.data.values, [])
        log = TimelineLogProxy.objects.for_object(self.submission.form).get()
        assert log.extra_data
        self.assertEqual(log.template, "logging/events/form_configuration_error.txt")
        self.assertEqual(
            log.extra_data["error"],
            _("Cannot fetch from ReferenceLists API, because no `code` is configured."),
        )

    def test_service_does_not_exist(self):
        component = Select(
            key="select",
            label="Select",
            data=SelectData(),
            data_type="string",
            open_forms=SelectExtensions(
                code="tabel1",
                data_src=DataSrcOptions.reference_lists.value,
                service=self.service.slug,
                translations={},
            ),
        )

        self.service.delete()

        with self.assertRaises(ServiceUnavailable):
            register.update_config(
                component, submission=self.submission, data=FormioData()
            )

        self.assertEqual(component.data.values, [])
        log = TimelineLogProxy.objects.for_object(self.submission.form).get()
        assert log.extra_data
        self.assertEqual(log.template, "logging/events/form_configuration_error.txt")
        self.assertEqual(
            log.extra_data["error"],
            _(
                "Cannot fetch from ReferenceLists API, service with {service_slug} does not exist."
            ).format(service_slug=self.service.slug),
        )

    def test_items_not_found(self):
        component = Select(
            key="select",
            label="Select",
            data=SelectData(),
            data_type="string",
            open_forms=SelectExtensions(
                code="non-existent",
                data_src=DataSrcOptions.reference_lists.value,
                service=self.service.slug,
                translations={},
            ),
        )

        with self.assertRaises(ServiceUnavailable):
            register.update_config(
                component, submission=self.submission, data=FormioData()
            )

        self.assertEqual(component.data.values, [])
        log = TimelineLogProxy.objects.for_object(self.submission.form).get()
        assert log.extra_data
        self.assertEqual(
            log.template, "logging/events/reference_lists_failure_response.txt"
        )
        self.assertEqual(
            log.extra_data["error"],
            _("No results found from ReferenceLists API."),
        )

    def test_items_expired(self):
        component = Select(
            key="select",
            label="Select",
            data=SelectData(),
            data_type="string",
            open_forms=SelectExtensions(
                code="item-not-geldig-anymore",
                data_src=DataSrcOptions.reference_lists.value,
                service=self.service.slug,
                translations={},
            ),
        )

        register.update_config(component, submission=self.submission, data=FormioData())

        self.assertEqual(component.data.values, [])

    def test_table_expired_item_valid(self):
        component = Select(
            key="select",
            label="Select",
            data=SelectData(),
            data_type="string",
            open_forms=SelectExtensions(
                code="not-geldig-anymore",
                data_src=DataSrcOptions.reference_lists.value,
                service=self.service.slug,
                translations={},
            ),
        )

        register.update_config(component, submission=self.submission, data=FormioData())

        self.assertEqual(component.data.values, [])

    @requests_mock.Mocker()
    def test_request_exception(self, m):
        component = Select(
            key="select",
            label="Select",
            data=SelectData(),
            data_type="string",
            open_forms=SelectExtensions(
                code="tabel1",
                data_src=DataSrcOptions.reference_lists.value,
                service=self.service.slug,
                translations={},
            ),
        )

        m.get(
            f"{self.service.api_root}tabellen?code=tabel1",
            exc=RequestException("something went wrong"),
        )

        with self.assertRaises(ServiceUnavailable):
            register.update_config(
                component, submission=self.submission, data=FormioData()
            )

        self.assertEqual(component.data.values, [])
        log = TimelineLogProxy.objects.for_object(self.submission.form).get()
        assert log.extra_data
        self.assertEqual(
            log.template, "logging/events/reference_lists_failure_response.txt"
        )
        self.assertEqual(
            log.extra_data["error"],
            _(
                "Exception occurred while fetching from ReferenceLists API: {exception}."
            ).format(exception="something went wrong"),
        )


@tag("gh-4993")
class SelectboxesReferenceListsOptionsTests(OFVCRMixin, TestCase):
    def setUp(self):
        super().setUp()

        # The requests to Referentielijsten are cached, we need to make sure
        # that the cache is reset between tests to correctly test different scenarios
        self.addCleanup(clear_caches)

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.service = ServiceFactory.create(
            api_root="http://localhost:8004/api/v1/",
            slug="reference-lists",
            auth_type=AuthTypes.no_auth,
        )
        cls.submission = SubmissionFactory.create()

    def test_success(self):
        component = Selectboxes(
            key="selectboxes",
            label="Selectboxes",
            values=[],
            open_forms=SelectboxesExtensions(
                data_src=DataSrcOptions.reference_lists.value,
                service=self.service.slug,
                code="tabel1",
                translations={},
            ),
        )

        register.update_config(component, submission=self.submission, data=FormioData())

        self.assertEqual(
            component.values,
            [
                Option(label="Option 2", value="option2"),
                Option(label="Option 1", value="option1"),
            ],
        )

    def test_no_service_configured(self):
        component = Selectboxes(
            key="selectboxes",
            label="Selectboxes",
            values=[],
            open_forms=SelectboxesExtensions(
                data_src=DataSrcOptions.reference_lists.value,
                service="",
                code="tabel1",
                translations={},
            ),
        )

        with self.assertRaises(ServiceUnavailable):
            register.update_config(
                component, submission=self.submission, data=FormioData()
            )

        self.assertEqual(component.values, [])

        log = TimelineLogProxy.objects.for_object(self.submission.form).get()
        assert log.extra_data
        self.assertEqual(log.template, "logging/events/form_configuration_error.txt")
        self.assertEqual(
            log.extra_data["error"],
            _(
                "Cannot fetch from ReferenceLists API, because no `service` is configured."
            ),
        )

    def test_no_code_configured(self):
        component = Selectboxes(
            key="selectboxes",
            label="Selectboxes",
            values=[],
            open_forms=SelectboxesExtensions(
                data_src=DataSrcOptions.reference_lists.value,
                service=self.service.slug,
                code="",
                translations={},
            ),
        )

        with self.assertRaises(ServiceUnavailable):
            register.update_config(
                component, submission=self.submission, data=FormioData()
            )

        self.assertEqual(component.values, [])

        log = TimelineLogProxy.objects.for_object(self.submission.form).get()
        assert log.extra_data
        self.assertEqual(log.template, "logging/events/form_configuration_error.txt")
        self.assertEqual(
            log.extra_data["error"],
            _("Cannot fetch from ReferenceLists API, because no `code` is configured."),
        )

    def test_service_does_not_exist(self):
        component = Selectboxes(
            key="selectboxes",
            label="Selectboxes",
            values=[],
            open_forms=SelectboxesExtensions(
                data_src=DataSrcOptions.reference_lists.value,
                service=self.service.slug,
                code="tabel1",
                translations={},
            ),
        )

        self.service.delete()

        with self.assertRaises(ServiceUnavailable):
            register.update_config(
                component, submission=self.submission, data=FormioData()
            )

        self.assertEqual(component.values, [])

        log = TimelineLogProxy.objects.for_object(self.submission.form).get()
        assert log.extra_data
        self.assertEqual(log.template, "logging/events/form_configuration_error.txt")
        self.assertEqual(
            log.extra_data["error"],
            _(
                "Cannot fetch from ReferenceLists API, service with {service_slug} does not exist."
            ).format(service_slug=self.service.slug),
        )

    def test_items_not_found(self):
        component = Selectboxes(
            key="selectboxes",
            label="Selectboxes",
            values=[],
            open_forms=SelectboxesExtensions(
                data_src=DataSrcOptions.reference_lists.value,
                service=self.service.slug,
                code="non-existent",
                translations={},
            ),
        )

        with self.assertRaises(ServiceUnavailable):
            register.update_config(
                component, submission=self.submission, data=FormioData()
            )

        self.assertEqual(component.values, [])

        log = TimelineLogProxy.objects.for_object(self.submission.form).get()
        assert log.extra_data
        self.assertEqual(
            log.template, "logging/events/reference_lists_failure_response.txt"
        )
        self.assertEqual(
            log.extra_data["error"],
            _("No results found from ReferenceLists API."),
        )

    def test_table_expired_item_valid(self):
        component = Selectboxes(
            key="selectboxes",
            label="Selectboxes",
            values=[],
            open_forms=SelectboxesExtensions(
                data_src=DataSrcOptions.reference_lists.value,
                service=self.service.slug,
                code="not-geldig-anymore",
                translations={},
            ),
        )

        register.update_config(component, submission=self.submission, data=FormioData())

        self.assertEqual(component.values, [])

    def test_items_expired(self):
        component = Selectboxes(
            key="selectboxes",
            label="Selectboxes",
            values=[],
            open_forms=SelectboxesExtensions(
                data_src=DataSrcOptions.reference_lists.value,
                service=self.service.slug,
                code="item-not-geldig-anymore",
                translations={},
            ),
        )

        register.update_config(component, submission=self.submission, data=FormioData())

        self.assertEqual(component.values, [])

    @requests_mock.Mocker()
    def test_request_exception(self, m):
        component = Selectboxes(
            key="selectboxes",
            label="Selectboxes",
            values=[],
            open_forms=SelectboxesExtensions(
                data_src=DataSrcOptions.reference_lists.value,
                service=self.service.slug,
                code="tabel1",
                translations={},
            ),
        )

        m.get(
            f"{self.service.api_root}tabellen?code=tabel1",
            exc=RequestException("something went wrong"),
        )

        with self.assertRaises(ServiceUnavailable):
            register.update_config(
                component, submission=self.submission, data=FormioData()
            )

        self.assertEqual(component.values, [])

        log = TimelineLogProxy.objects.for_object(self.submission.form).get()
        assert log.extra_data
        self.assertEqual(
            log.template, "logging/events/reference_lists_failure_response.txt"
        )
        self.assertEqual(
            log.extra_data["error"],
            _(
                "Exception occurred while fetching from ReferenceLists API: {exception}."
            ).format(exception="something went wrong"),
        )


@tag("gh-4993")
class RadioReferenceListsOptionsTests(OFVCRMixin, TestCase):
    def setUp(self):
        super().setUp()

        # The requests to Referentielijsten are cached, we need to make sure
        # that the cache is reset between tests to correctly test different scenarios
        self.addCleanup(clear_caches)

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.service = ServiceFactory.create(
            api_root="http://localhost:8004/api/v1/",
            slug="reference-lists",
            auth_type=AuthTypes.no_auth,
        )
        cls.submission = SubmissionFactory.create()

    def test_success(self):
        component = Radio(
            key="radio",
            label="Radio",
            values=[],
            open_forms=RadioExtensions(
                data_src=DataSrcOptions.reference_lists.value,
                service=self.service.slug,
                code="tabel1",
                translations={},
            ),
        )

        register.update_config(component, submission=self.submission, data=FormioData())

        self.assertEqual(
            component.values,
            [
                Option(label="Option 2", value="option2"),
                Option(label="Option 1", value="option1"),
            ],
        )

    def test_no_service_configured(self):
        component = Radio(
            key="radio",
            label="Radio",
            values=[],
            open_forms=RadioExtensions(
                data_src=DataSrcOptions.reference_lists.value,
                service="",
                code="tabel1",
                translations={},
            ),
        )

        with self.assertRaises(ServiceUnavailable):
            register.update_config(
                component, submission=self.submission, data=FormioData()
            )

        self.assertEqual(component.values, [])
        log = TimelineLogProxy.objects.for_object(self.submission.form).get()
        assert log.extra_data
        self.assertEqual(log.template, "logging/events/form_configuration_error.txt")
        self.assertEqual(
            log.extra_data["error"],
            _(
                "Cannot fetch from ReferenceLists API, because no `service` is configured."
            ),
        )

    def test_no_code_configured(self):
        component = Radio(
            key="radio",
            label="Radio",
            values=[],
            open_forms=RadioExtensions(
                data_src=DataSrcOptions.reference_lists.value,
                service=self.service.slug,
                code="",
                translations={},
            ),
        )

        with self.assertRaises(ServiceUnavailable):
            register.update_config(
                component, submission=self.submission, data=FormioData()
            )

        self.assertEqual(component.values, [])
        log = TimelineLogProxy.objects.for_object(self.submission.form).get()
        assert log.extra_data
        self.assertEqual(log.template, "logging/events/form_configuration_error.txt")
        self.assertEqual(
            log.extra_data["error"],
            _("Cannot fetch from ReferenceLists API, because no `code` is configured."),
        )

    def test_service_does_not_exist(self):
        component = Radio(
            key="radio",
            label="Radio",
            values=[],
            open_forms=RadioExtensions(
                data_src=DataSrcOptions.reference_lists.value,
                service=self.service.slug,
                code="tabel1",
                translations={},
            ),
        )

        self.service.delete()

        with self.assertRaises(ServiceUnavailable):
            register.update_config(
                component, submission=self.submission, data=FormioData()
            )

        self.assertEqual(component.values, [])
        log = TimelineLogProxy.objects.for_object(self.submission.form).get()
        assert log.extra_data
        self.assertEqual(log.template, "logging/events/form_configuration_error.txt")
        self.assertEqual(
            log.extra_data["error"],
            _(
                "Cannot fetch from ReferenceLists API, service with {service_slug} does not exist."
            ).format(service_slug=self.service.slug),
        )

    def test_items_not_found(self):
        component = Radio(
            key="radio",
            label="Radio",
            values=[],
            open_forms=RadioExtensions(
                data_src=DataSrcOptions.reference_lists.value,
                service=self.service.slug,
                code="non-existent",
                translations={},
            ),
        )

        with self.assertRaises(ServiceUnavailable):
            register.update_config(
                component, submission=self.submission, data=FormioData()
            )

        self.assertEqual(component.values, [])
        log = TimelineLogProxy.objects.for_object(self.submission.form).get()
        assert log.extra_data
        self.assertEqual(
            log.template, "logging/events/reference_lists_failure_response.txt"
        )
        self.assertEqual(
            log.extra_data["error"],
            _("No results found from ReferenceLists API."),
        )

    def test_items_expired(self):
        component = Radio(
            key="radio",
            label="Radio",
            values=[],
            open_forms=RadioExtensions(
                data_src=DataSrcOptions.reference_lists.value,
                service=self.service.slug,
                code="item-not-geldig-anymore",
                translations={},
            ),
        )

        register.update_config(component, submission=self.submission, data=FormioData())

        self.assertEqual(component.values, [])

    def test_table_expired_item_valid(self):
        component = Radio(
            key="radio",
            label="Radio",
            values=[],
            open_forms=RadioExtensions(
                data_src=DataSrcOptions.reference_lists.value,
                service=self.service.slug,
                code="not-geldig-anymore",
                translations={},
            ),
        )

        register.update_config(component, submission=self.submission, data=FormioData())

        self.assertEqual(component.values, [])

    @requests_mock.Mocker()
    def test_request_exception(self, m):
        component = Radio(
            key="radio",
            label="Radio",
            values=[],
            open_forms=RadioExtensions(
                data_src=DataSrcOptions.reference_lists.value,
                service=self.service.slug,
                code="tabel1",
                translations={},
            ),
        )

        m.get(
            f"{self.service.api_root}tabellen?code=tabel1",
            exc=RequestException("something went wrong"),
        )

        with self.assertRaises(ServiceUnavailable):
            register.update_config(
                component, submission=self.submission, data=FormioData()
            )

        self.assertEqual(component.values, [])
        log = TimelineLogProxy.objects.for_object(self.submission.form).get()
        assert log.extra_data
        self.assertEqual(
            log.template, "logging/events/reference_lists_failure_response.txt"
        )
        self.assertEqual(
            log.extra_data["error"],
            _(
                "Exception occurred while fetching from ReferenceLists API: {exception}."
            ).format(exception="something went wrong"),
        )


@tag("gh-4993")
class SubmissionStepDetailTest(SubmissionsMixin, APITestCase):
    def test_get_submissionstep_detail_raises_error_for_reference_lists_if_service_is_incorrect(
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
                        "openForms": {
                            "dataSrc": DataSrcOptions.reference_lists,
                            "service": "non-existent",
                            "code": "tabel1",
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

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        # the detail message should be passed for errors that occur when fetching referentielijsten
        self.assertEqual(
            response.json()["detail"],
            _("Could not retrieve options from Referentielijsten API."),
        )
