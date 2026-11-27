from collections.abc import Callable
from datetime import UTC, datetime
from unittest.mock import patch

from django.test import TestCase, tag

from furl import furl
from privates.test import temp_private_root
from requests import RequestException
from vcr.request import Request as VCRRequest

from openforms.authentication.constants import AuthAttribute
from openforms.authentication.tests.factories import RegistratorInfoFactory
from openforms.contrib.objects_api.clients import get_objects_client
from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory
from openforms.contrib.zgw.clients.zaken import CRS_HEADERS, ZakenClient
from openforms.submissions.constants import PostSubmissionEvents, RegistrationStatuses
from openforms.submissions.tasks import pre_registration
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
)
from openforms.utils.tests.vcr import OFVCRMixin

from ....constants import RegistrationAttribute
from ....exceptions import RegistrationFailed
from ....tasks import register_submission
from ..client import get_documents_client, get_zaken_client
from ..constants import SummaryDocumentChoices
from ..plugin import PLUGIN_IDENTIFIER, ZGWRegistration
from ..typing import RegistrationOptions
from .factories import ZGWApiGroupConfigFactory


class BeforeRecordRequestWrapper:
    hook: Callable[[VCRRequest], VCRRequest | None] | None = None

    def __call__(self, request: VCRRequest) -> VCRRequest | None:
        if hook := self.hook:
            return hook(request)
        return request


@tag("gh-6919")
@temp_private_root()
class IdempotencyTests(OFVCRMixin, TestCase):
    """
    Assert that running the (pre-)registration multiple times for the same submission
    does not create anything new in the external services.
    """

    OBJECTTYPE_URL = "http://host.docker.internal:8001/api/v2/objecttypes/8faed0fa-7864-4409-aa6d-533a37616a9e"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.zgw_api_group = ZGWApiGroupConfigFactory.create(
            for_test_docker_compose=True,
            organisatie_rsin="000000000",
        )

        cls.options: RegistrationOptions = {
            "zgw_api_group": cls.zgw_api_group,
            "catalogue": {"domain": "TEST", "rsin": "000000000"},
            "case_type_identification": "ZT-001",
            "document_type_description": "Attachment Informatieobjecttype",
            "product_url": "",
            "objects_api_group": None,
            "organisatie_rsin": "000000000",
            "summary_documents": [
                SummaryDocumentChoices.pdf,
                SummaryDocumentChoices.json,
            ],
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
        }

    def setUp(self):
        super().setUp()

        # TODO-6919: is this correct?
        self.zaken_client = get_zaken_client(self.zgw_api_group)
        self.addCleanup(self.zaken_client.close)
        self.documents_client = get_documents_client(self.zgw_api_group)
        self.addCleanup(self.documents_client.close)

    def _count_zaken(self) -> int:
        response = self.zaken_client.get(
            "zaken",
            params={"bronorganisatie": "000000000"},
            headers=CRS_HEADERS,
        )
        response.raise_for_status()
        return response.json()["count"]

    def _count_documents(self) -> int:
        response = self.documents_client.get(
            "enkelvoudiginformatieobjecten",
            params={"bronorganisatie": "000000000"},
        )
        response.raise_for_status()
        return response.json()["count"]

    def _count_objects(self, objects_api_group) -> int:
        with get_objects_client(objects_api_group) as client:
            response = client.get(
                "objects",
                params={
                    "type": self.OBJECTTYPE_URL.replace(
                        "host.docker.internal", "localhost", 1
                    ),
                    "pageSize": 1,
                },
            )
            response.raise_for_status()
            return response.json()["count"]

    def _count_zaak_related(self, endpoint: str, zaak_url: str) -> int:
        response = self.zaken_client.get(endpoint, params={"zaak": zaak_url})
        response.raise_for_status()
        data = response.json()
        # some endpoints are paginated, others return a plain list
        return data["count"] if isinstance(data, dict) else len(data)

    def _count_zaakeigenschappen(self, zaak_url: str) -> int:
        # zaakeigenschappen are a nested resource of the zaak, so they can't be
        # filtered with the ``zaak`` query parameter
        zaak_uuid = furl(zaak_url).path.segments[-1]
        response = self.zaken_client.get(f"zaken/{zaak_uuid}/zaakeigenschappen")
        response.raise_for_status()
        return len(response.json())

    def test_pre_registering_twice_does_not_create_zaak_again(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "textfield",
                    "type": "textfield",
                    "label": "Textfield",
                },
            ],
            completed_not_preregistered=True,
            submitted_data={"textfield": "foo"},
            bsn="111222333",
            # Pin to a known case type version
            completed_on=datetime(2024, 11, 9, 15, 30, 0, tzinfo=UTC),
        )
        plugin = ZGWRegistration(PLUGIN_IDENTIFIER)
        n_zaken_before = self._count_zaken()

        result = plugin.pre_register_submission(submission, self.options)
        assert result.data is not None
        zaak_url = result.data["zaak"]["url"]
        n_zaken_after_first_run = self._count_zaken()

        result = plugin.pre_register_submission(submission, self.options)
        assert result.data is not None
        self.assertEqual(n_zaken_after_first_run - n_zaken_before, 1)
        self.assertEqual(self._count_zaken(), n_zaken_after_first_run)
        self.assertEqual(result.data["zaak"]["url"], zaak_url)

    def test_registering_twice_does_not_create_anything_again(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "textfield1",
                    "type": "textfield",
                    "label": "Textfield 1",
                },
                {
                    "key": "textfield2",
                    "type": "textfield",
                    "label": "Textfield 2",
                },
                {
                    "type": "file",
                    "key": "file",
                    "label": "File",
                    "file": {"type": []},
                    "filePattern": "",
                    "url": "",
                    "multiple": False,
                },
            ],
            submitted_data={
                "textfield1": "some data",
                "textfield2": "more data",
                "file": [],  # in this case, actual data is not relevant for registration
            },
            bsn="111222333",
            completed_not_preregistered=True,
            # Pin to a known case & document type version (2024-10-31)
            completed_on=datetime(2024, 11, 9, 15, 30, 0, tzinfo=UTC),
            with_report=True,
        )
        SubmissionFileAttachmentFactory.create(
            submission_step=submission.steps[0],
            submission_variable__key="file",
            file_name="attachment.txt",
            original_name="attachment.txt",
        )
        RegistratorInfoFactory.create(submission=submission, value="123456782")
        options: RegistrationOptions = {
            **self.options,
            "medewerker_roltype": "Baliemedewerker",
            "property_mappings": [
                {"component_key": "textfield1", "eigenschap": "a property name"},
                {"component_key": "textfield2", "eigenschap": "second property"},
            ],
            "case_objects": [
                {
                    "case_object_type": "overige",
                    "case_object_type_overige": "building in construction",
                    "case_object_identification": {
                        "overige_data": "Building: {{ variables.textField1 }}"
                    },
                },
            ],
        }
        plugin = ZGWRegistration(PLUGIN_IDENTIFIER)

        result = plugin.pre_register_submission(submission, options)
        assert result.data is not None
        submission.registration_result.update(result.data)
        zaak_url = result.data["zaak"]["url"]

        n_documents_before = self._count_documents()
        plugin.register_submission(submission, options)
        with self.subTest("After first run"):
            # PDF summary, JSON summary, and attachment
            self.assertEqual(self._count_documents() - n_documents_before, 3)
            # Initiator and medewerker
            self.assertEqual(self._count_zaak_related("rollen", zaak_url), 2)
            # Initial status
            self.assertEqual(self._count_zaak_related("statussen", zaak_url), 1)
            # PDF summary, JSON summary, and attachment
            self.assertEqual(
                self._count_zaak_related("zaakinformatieobjecten", zaak_url), 3
            )
            # Single zaakobject (see "case_objects")
            self.assertEqual(self._count_zaak_related("zaakobjecten", zaak_url), 1)
            # Two eigenschappen for both text fields (see "property_mappings")
            self.assertEqual(self._count_zaakeigenschappen(zaak_url), 2)

        plugin.register_submission(submission, options)
        with self.subTest("Second run does not create new objects"):
            self.assertEqual(self._count_documents() - n_documents_before, 3)
            self.assertEqual(self._count_zaak_related("rollen", zaak_url), 2)
            self.assertEqual(self._count_zaak_related("statussen", zaak_url), 1)
            self.assertEqual(
                self._count_zaak_related("zaakinformatieobjecten", zaak_url), 3
            )
            self.assertEqual(self._count_zaak_related("zaakobjecten", zaak_url), 1)
            self.assertEqual(self._count_zaakeigenschappen(zaak_url), 2)

    def test_registering_twice_with_partners_does_not_create_rollen_again(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "partners",
                    "type": "partners",
                    "label": "Partners",
                    "registration": {
                        "attribute": RegistrationAttribute.partners,
                    },
                }
            ],
            auth_info__value="123456782",
            auth_info__attribute=AuthAttribute.bsn,
            completed_not_preregistered=True,
            completed_on=datetime(2024, 11, 9, 15, 30, 0, tzinfo=UTC),
            submitted_data={
                "partners": [
                    {
                        "bsn": "999970136",
                        "firstNames": "Pia",
                        "initials": "P.",
                        "affixes": "",
                        "lastName": "Pauw",
                        "dateOfBirth": "1989-04-01",
                        "dateOfBirthPrecision": "date",
                        "__addedManually": True,
                    }
                ]
            },
            with_report=True,
        )
        options: RegistrationOptions = {
            **self.options,
            "catalogue": {"domain": "PARTN", "rsin": "000000000"},
            "case_type_identification": "ZAAKTYPE-2020-0000000001",
            "document_type_description": "Partners PDF Informatieobjecttype",
            "partners_roltype": "Partner role type",
        }
        plugin = ZGWRegistration(PLUGIN_IDENTIFIER)

        result = plugin.pre_register_submission(submission, options)
        assert result.data is not None
        submission.registration_result.update(result.data)
        zaak_url = result.data["zaak"]["url"]

        plugin.register_submission(submission, options)
        with self.subTest("After first run"):
            # Initiator and partner
            self.assertEqual(self._count_zaak_related("rollen", zaak_url), 2)

        plugin.register_submission(submission, options)
        with self.subTest("Second run does not create new rollen"):
            self.assertEqual(self._count_zaak_related("rollen", zaak_url), 2)

    def test_registering_twice_with_children_does_not_create_rollen_again(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "children",
                    "type": "children",
                    "label": "Children",
                    "enableSelection": False,
                    "registration": {
                        "attribute": RegistrationAttribute.children,
                    },
                }
            ],
            auth_info__value="123456782",
            auth_info__attribute=AuthAttribute.bsn,
            completed_not_preregistered=True,
            completed_on=datetime(2024, 11, 9, 15, 30, 0, tzinfo=UTC),
            submitted_data={
                "children": [
                    {
                        "bsn": "999970409",
                        "affixes": "van",
                        "initials": "P.",
                        "lastName": "Paassen",
                        "firstNames": "Pero",
                        "dateOfBirth": "2023-02-01",
                        "dateOfBirthPrecision": "date",
                        "__addedManually": True,
                    },
                ]
            },
            with_report=True,
        )
        options: RegistrationOptions = {
            **self.options,
            "catalogue": {"domain": "CHILD", "rsin": "000000000"},
            "case_type_identification": "ZAAKTYPE-2020-0000000002",
            "document_type_description": "Children PDF Informatieobjecttype",
            "children_roltype": "Children role type",
        }
        plugin = ZGWRegistration(PLUGIN_IDENTIFIER)

        result = plugin.pre_register_submission(submission, options)
        assert result.data is not None
        submission.registration_result.update(result.data)
        zaak_url = result.data["zaak"]["url"]

        plugin.register_submission(submission, options)
        with self.subTest("After first run"):
            # Initiator and child
            self.assertEqual(self._count_zaak_related("rollen", zaak_url), 2)

        plugin.register_submission(submission, options)
        with self.subTest("Second run does not create new rollen"):
            self.assertEqual(self._count_zaak_related("rollen", zaak_url), 2)

    def test_registering_twice_with_objects_api_does_not_create_object_again(self):
        objects_api_group = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True
        )
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "textfield",
                    "type": "textfield",
                    "label": "Textfield",
                },
            ],
            submitted_data={"textfield": "foo"},
            bsn="111222333",
            completed_not_preregistered=True,
            # Pin to a known case & document type version
            completed_on=datetime(2024, 11, 9, 15, 30, 0, tzinfo=UTC),
            with_report=True,
        )
        options: RegistrationOptions = {
            **self.options,
            "objects_api_group": objects_api_group,
            "objecttype": self.OBJECTTYPE_URL,
            "objecttype_version": 1,
            "content_json": '{"data": {% json_summary %}, "type": "{{ productaanvraag_type }}"}',
            "summary_documents": [SummaryDocumentChoices.pdf],
        }
        plugin = ZGWRegistration(PLUGIN_IDENTIFIER)

        # we need to patch the ZGW client `create_zaakobject_with_object` method so that we can
        # fix up the object URL since Open Zaak validates the format and needs to resolve
        # this inside the container network
        original_create_zaakobject = ZakenClient.create_zaakobject_with_object

        def wrapped_create_zaakobject(
            self, zaak, object_url: str, objecttype_version_url: str
        ):
            object_url = object_url.replace(
                "http://localhost:8001", "http://host.docker.internal:8001", 1
            )
            return original_create_zaakobject(
                self, zaak, object_url, objecttype_version_url
            )

        objects_before = self._count_objects(objects_api_group)
        with patch.object(
            ZakenClient,
            "create_zaakobject_with_object",
            side_effect=wrapped_create_zaakobject,
            autospec=True,
        ):
            result = plugin.pre_register_submission(submission, options)
            assert result.data is not None
            submission.registration_result.update(result.data)

            plugin.register_submission(submission, options)
            with self.subTest("After first run"):
                self.assertEqual(
                    self._count_objects(objects_api_group) - objects_before, 1
                )

            plugin.register_submission(submission, options)
            with self.subTest("Second run does not create new object"):
                self.assertEqual(
                    self._count_objects(objects_api_group) - objects_before, 1
                )


@tag("gh-1183")
@temp_private_root(reset_storage=False)
class PartialRegistrationFailureTests(OFVCRMixin, TestCase):
    """
    Test that partial results are stored and don't cause excessive registration calls.

    Issue #1183 -- case numbers are reserved to often, as a retry reserves a new one. It
    also happens that when certain other calls fail, a new Zaak is created which
    should not have been created again.
    """

    _vcr_before_record_request: BeforeRecordRequestWrapper = (
        BeforeRecordRequestWrapper()
    )
    """
    Instance variable to intercept and modify requests to introduce error behaviour.

    Set this in the test with a callback to introduce test-specific failure situations.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.zgw_api_group = ZGWApiGroupConfigFactory.create(
            for_test_docker_compose=True,
            organisatie_rsin="000000000",
        )

    def setUp(self):
        super().setUp()

        def _reset_vcr_hook():
            self._vcr_before_record_request.hook = None

        self.addCleanup(_reset_vcr_hook)

        # set up a simple form to track the partial result storing state
        self.submission = SubmissionFactory.from_components(
            [
                {
                    "key": "voornaam",
                    "type": "textfield",
                },
                {
                    "key": "achternaam",
                    "type": "textfield",
                },
            ],
            submitted_data={
                "voornaam": "Foo",
                "achternaam": "Bar",
            },
            form__name="my-form",
            form__registration_backend="zgw-create-zaak",
            form__registration_backend_options={
                "zgw_api_group": self.zgw_api_group.pk,
                "catalogue": {"domain": "TEST", "rsin": "000000000"},
                "case_type_identification": "ZT-001",
                "document_type_description": "Attachment Informatieobjecttype",
                "objects_api_group": None,
                "zaaktype": "",
                "informatieobjecttype": "",
                "organisatie_rsin": "000000000",
                "vertrouwelijkheidaanduiding": "",
                "summary_documents": [SummaryDocumentChoices.pdf],
            },
            completed_not_preregistered=True,
            bsn="111222333",
            # Pin to a known case & document type version
            completed_on=datetime(2024, 11, 9, 15, 30, 0).replace(tzinfo=UTC),
            with_report=True,
        )

    def _get_vcr_kwargs(self, **kwargs):
        kwargs["before_record_request"] = self._vcr_before_record_request
        return super()._get_vcr_kwargs(**kwargs)

    def test_failure_after_zaak_creation(self):
        submission = self.submission
        create_document_call_count = 0

        def fail_create_document_request(request: VCRRequest):
            if (
                request.url.startswith(
                    "http://localhost:8003/documenten/api/v1/enkelvoudiginformatieobjecten"
                )
                and request.method == "POST"
            ):
                nonlocal create_document_call_count
                create_document_call_count += 1
                raise RequestException("Server error")

            return request

        self._vcr_before_record_request.hook = fail_create_document_request

        with self.subTest("Initial document creation fails"):
            pre_registration(submission.pk, PostSubmissionEvents.on_completion)
            register_submission(submission.pk, PostSubmissionEvents.on_completion)

            submission.refresh_from_db()
            assert submission.registration_result
            self.assertEqual(
                submission.registration_status, RegistrationStatuses.failed
            )
            intermediate_results = submission.registration_result["intermediate"]
            initially_created_zaak_url = intermediate_results["zaak"]["url"]
            self.assertTrue(
                initially_created_zaak_url.startswith(
                    "http://localhost:8003/zaken/api/v1/zaken/"
                )
            )
            self.assertIn("traceback", submission.registration_result)

        with self.subTest("New document creation attempt does not create zaak again"):
            with self.assertRaises(RegistrationFailed):
                register_submission(submission.pk, PostSubmissionEvents.on_retry)

            submission.refresh_from_db()
            self.assertEqual(
                submission.registration_status, RegistrationStatuses.failed
            )
            intermediate_results = submission.registration_result["intermediate"]
            self.assertEqual(
                intermediate_results["zaak"]["url"], initially_created_zaak_url
            )
            self.assertIn("traceback", submission.registration_result)

        with self.subTest("verify request counts"):
            create_zaak_calls = [
                req
                for req in self.cassette.requests
                if req.method == "POST"
                if req.url == "http://localhost:8003/zaken/api/v1/zaken"
            ]
            self.assertEqual(len(create_zaak_calls), 1)
            self.assertEqual(create_document_call_count, 1 + 1)  # first attempt = retry

    def test_attachment_document_relation_create_fails(self):
        submission = self.submission
        attachment = SubmissionFileAttachmentFactory.create(
            submission_step=submission.steps[0],
            file_name="attachment1.jpg",
            submission_variable__key="field1",
        )

        relate_document_call_count = 0
        original_relate_document = ZakenClient.relate_document

        def wrapped_related_document(self, zaak, document):
            nonlocal relate_document_call_count
            relate_document_call_count += 1
            if (
                relate_document_call_count > 1
            ):  # let the PDF relation request go through
                raise RequestException("Simulted failure")
            return original_relate_document(self, zaak, document)

        with (
            self.subTest("First try, attachment relation fails"),
            patch.object(
                ZakenClient,
                "relate_document",
                autospec=True,
                side_effect=wrapped_related_document,
            ),
        ):
            pre_registration(submission.pk, PostSubmissionEvents.on_completion)
            register_submission(submission.pk, PostSubmissionEvents.on_completion)

            submission.refresh_from_db()
            assert submission.registration_result
            self.assertEqual(
                submission.registration_status, RegistrationStatuses.failed
            )
            self.assertIn("traceback", submission.registration_result)

            intermediate_results = submission.registration_result["intermediate"]
            initially_created_zaak_url = intermediate_results["zaak"]["url"]
            self.assertTrue(
                initially_created_zaak_url.startswith(
                    "http://localhost:8003/zaken/api/v1/zaken/"
                )
            )

            doc_report = intermediate_results["documents"]["report"]
            intially_created_doc_report_url = doc_report["document"]["url"]
            intially_created_doc_relation_url = doc_report["relation"]["url"]
            self.assertTrue(
                intially_created_doc_report_url.startswith(
                    "http://localhost:8003/documenten/api/v1/enkelvoudiginformatieobjecten/"
                )
            )

            doc_attachment = intermediate_results["documents"][str(attachment.pk)]
            initially_created_attachment_url = doc_attachment["document"]["url"]

            initially_created_initiator_rol_url = intermediate_results["initiator_rol"][
                "url"
            ]
            initially_created_status_url = intermediate_results["status"]["url"]

        with (
            self.subTest("New attempt - ensure existing data is not created again"),
            patch.object(
                ZakenClient,
                "relate_document",
                autospec=True,
                side_effect=wrapped_related_document,
            ),
        ):
            with self.assertRaises(RegistrationFailed):
                register_submission(submission.pk, PostSubmissionEvents.on_retry)

            submission.refresh_from_db()
            self.assertEqual(
                submission.registration_status, RegistrationStatuses.failed
            )
            intermediate_results = submission.registration_result["intermediate"]
            self.assertIn("traceback", submission.registration_result)

            self.assertEqual(
                intermediate_results["zaak"]["url"], initially_created_zaak_url
            )
            doc_report = intermediate_results["documents"]["report"]
            self.assertTrue(
                doc_report["document"]["url"].startswith(
                    "http://localhost:8003/documenten/api/v1/enkelvoudiginformatieobjecten/"
                )
            )
            self.assertTrue(
                doc_report["relation"]["url"].startswith(
                    "http://localhost:8003/zaken/api/v1/zaakinformatieobjecten/"
                )
            )

            doc_report = intermediate_results["documents"]["report"]
            self.assertEqual(
                doc_report["document"]["url"], intially_created_doc_report_url
            )
            self.assertEqual(
                doc_report["relation"]["url"], intially_created_doc_relation_url
            )

            doc_attachment = intermediate_results["documents"][str(attachment.pk)]
            self.assertEqual(
                doc_attachment["document"]["url"], initially_created_attachment_url
            )
            self.assertNotIn("relation", doc_attachment)

            self.assertEqual(
                intermediate_results["initiator_rol"]["url"],
                initially_created_initiator_rol_url,
            )
            self.assertEqual(
                intermediate_results["status"]["url"], initially_created_status_url
            )

    def test_zaakeigenschappen_creation_failure(self):
        submission = self.submission
        registration_backend = submission.form.registration_backends.get()
        registration_backend.options.update(
            {
                "property_mappings": [
                    {"component_key": "voornaam", "eigenschap": "a property name"}
                ],
            }
        )
        registration_backend.save()

        def fail_zaakeigenschappen_creation(request: VCRRequest):
            if (
                request.method == "POST"
                and request.url.startswith("http://localhost:8003/zaken/api/v1/zaken/")
                and request.url.endswith("zaakeigenschappen")
            ):
                raise RequestException("Server error")
            return request

        self._vcr_before_record_request.hook = fail_zaakeigenschappen_creation

        pre_registration(submission.pk, PostSubmissionEvents.on_completion)
        register_submission(submission.pk, PostSubmissionEvents.on_completion)

        submission.refresh_from_db()
        assert submission.registration_result
        self.assertEqual(submission.registration_status, RegistrationStatuses.failed)
        self.assertIn("traceback", submission.registration_result)

        zt_eigenschappen = submission.registration_result["intermediate"][
            "zaaktype_eigenschappen"
        ]
        self.assertEqual(
            len(zt_eigenschappen), 2
        )  # 2 eigenschappen defined on the case type

    def test_failure_on_object_relation_zaakobject_creation(self):
        # no need to mock the failure - the host names in the compose setup already
        # genuinely break and cause validation issues :-)
        objects_api_group = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True
        )

        submission = self.submission
        registration_backend = submission.form.registration_backends.get()
        registration_backend.options.update(
            {
                "objects_api_group": objects_api_group.identifier,
                "objecttype": (
                    "http://host.docker.internal:8001/api/v2/"
                    "objecttypes/8faed0fa-7864-4409-aa6d-533a37616a9e"
                ),
                "objecttype_version": 1,
            }
        )
        registration_backend.save()

        pre_registration(submission.pk, PostSubmissionEvents.on_completion)
        register_submission(submission.pk, PostSubmissionEvents.on_completion)

        submission.refresh_from_db()
        assert submission.registration_result
        self.assertEqual(submission.registration_status, RegistrationStatuses.failed)
        self.assertIn("traceback", submission.registration_result)

        intermediate_results = submission.registration_result["intermediate"]

        object_data = intermediate_results["objects_api_object"]
        self.assertTrue(
            object_data["url"].startswith("http://localhost:8001/api/v2/objects/")
        )
