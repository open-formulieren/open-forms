from io import StringIO
from uuid import UUID, uuid4

from django.core.management import CommandError, call_command
from django.test import TestCase

from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory
from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormRegistrationBackendFactory,
)
from openforms.registrations.contrib.objects_api.config import (
    ObjectsAPIOptionsSerializer,
)
from openforms.registrations.contrib.objects_api.constants import (
    PLUGIN_IDENTIFIER as OBJECTS_PLUGIN_IDENTIFIER,
)
from openforms.registrations.contrib.objects_api.typing import (
    RegistrationOptionsV2 as ObjectsRegistrationOptionsV2,
)
from openforms.registrations.contrib.zgw_apis.constants import SummaryDocumentChoices
from openforms.registrations.contrib.zgw_apis.options import ZaakOptionsSerializer
from openforms.registrations.contrib.zgw_apis.tests.factories import (
    ZGWApiGroupConfigFactory,
)
from openforms.registrations.contrib.zgw_apis.typing import (
    RegistrationOptions as ZGWRegistrationOptions,
)
from openforms.utils.tests.vcr import OFVCRMixin

from ..zgw_urls_migrator import (
    MigrationProblem,
    Migrator,
    look_up_case_type,
    look_up_document_type,
)


class MigratorTests(OFVCRMixin, TestCase):
    """
    Requires the VCR services, see ``docker/start_vcr_services.sh``.
    """

    maxDiff = None

    def setUp(self):
        super().setUp()

        def clear_cache():
            look_up_case_type.cache_clear()
            look_up_document_type.cache_clear()

        self.addCleanup(clear_cache)

    def test_doesnot_crash_without_any_data(self):
        outfile = StringIO()
        migrator = Migrator(outfile=outfile)

        result = migrator.migrate()

        self.assertIsNone(result)

    def test_ok_for_forms_with_nothing_to_do(self):
        FormFactory.create_batch(
            3,
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "ignoreMe",
                        "label": "Ignore me",
                    },
                ]
            },
        )
        FormFactory.create(is_appointment_form=True)
        outfile = StringIO()
        migrator = Migrator(outfile=outfile)

        result = migrator.migrate()

        self.assertIsNone(result)

    def test_happy_flow_migrate_objects_api_groups(self):
        objects_api_group_with_modern_config = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True,
            catalogue_domain="DNT",
            catalogue_rsin="DNTDNTDNT",
            iot_submission_report="do not touch",
            iot_submission_csv="do not touch",
            iot_attachment="do not touch",
            informatieobjecttype_submission_report=(
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "7a474713-0833-402a-8441-e467c08ac55b"
            ),
            informatieobjecttype_submission_csv=(
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "b2d83b94-9b9b-4e80-a82f-73ff993c62f3"
            ),
            informatieobjecttype_attachment=(
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "531f6c1a-97f7-478c-85f0-67d2f23661c7"
            ),
        )
        objects_api_group_without_catalogue_with_urls = (
            ObjectsAPIGroupConfigFactory.create(
                for_test_docker_compose=True,
                catalogue_domain="",
                catalogue_rsin="",
                iot_submission_report="",
                iot_submission_csv="",
                iot_attachment="",
                informatieobjecttype_submission_report=(
                    "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                    "7a474713-0833-402a-8441-e467c08ac55b"
                ),
                informatieobjecttype_submission_csv=(
                    "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                    "b2d83b94-9b9b-4e80-a82f-73ff993c62f3"
                ),
                informatieobjecttype_attachment=(
                    "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                    "531f6c1a-97f7-478c-85f0-67d2f23661c7"
                ),
            )
        )
        objects_api_group_with_catalogue_with_urls = (
            ObjectsAPIGroupConfigFactory.create(
                for_test_docker_compose=True,
                catalogue_domain="TEST",
                catalogue_rsin="000000000",
                iot_submission_report="",
                iot_submission_csv="",
                iot_attachment="",
                informatieobjecttype_submission_report=(
                    "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                    "7a474713-0833-402a-8441-e467c08ac55b"
                ),
                informatieobjecttype_submission_csv=(
                    "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                    "b2d83b94-9b9b-4e80-a82f-73ff993c62f3"
                ),
                informatieobjecttype_attachment=(
                    "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                    "531f6c1a-97f7-478c-85f0-67d2f23661c7"
                ),
            )
        )

        outfile = StringIO()
        migrator = Migrator(outfile=outfile)
        migrator.migrate()

        with self.subTest("objects_api_group_with_modern_config"):
            objects_api_group_with_modern_config.refresh_from_db()
            self.assertEqual(
                objects_api_group_with_modern_config.catalogue_domain,
                "DNT",
            )
            self.assertEqual(
                objects_api_group_with_modern_config.catalogue_rsin,
                "DNTDNTDNT",
            )
            self.assertEqual(
                objects_api_group_with_modern_config.iot_submission_report,
                "do not touch",
            )
            self.assertEqual(
                objects_api_group_with_modern_config.iot_submission_csv,
                "do not touch",
            )
            self.assertEqual(
                objects_api_group_with_modern_config.iot_attachment,
                "do not touch",
            )

        with self.subTest("objects_api_group_without_catalogue_with_urls"):
            objects_api_group_without_catalogue_with_urls.refresh_from_db()
            self.assertEqual(
                objects_api_group_without_catalogue_with_urls.catalogue_domain,
                "TEST",
            )
            self.assertEqual(
                objects_api_group_without_catalogue_with_urls.catalogue_rsin,
                "000000000",
            )
            self.assertEqual(
                objects_api_group_without_catalogue_with_urls.iot_submission_report,
                "PDF Informatieobjecttype",
            )
            self.assertEqual(
                objects_api_group_without_catalogue_with_urls.iot_submission_csv,
                "CSV Informatieobjecttype",
            )
            self.assertEqual(
                objects_api_group_without_catalogue_with_urls.iot_attachment,
                "Attachment Informatieobjecttype",
            )

        with self.subTest("objects_api_group_with_catalogue_with_urls"):
            objects_api_group_with_catalogue_with_urls.refresh_from_db()
            self.assertEqual(
                objects_api_group_with_catalogue_with_urls.catalogue_domain,
                "TEST",
            )
            self.assertEqual(
                objects_api_group_with_catalogue_with_urls.catalogue_rsin,
                "000000000",
            )
            self.assertEqual(
                objects_api_group_with_catalogue_with_urls.iot_submission_report,
                "PDF Informatieobjecttype",
            )
            self.assertEqual(
                objects_api_group_with_catalogue_with_urls.iot_submission_csv,
                "CSV Informatieobjecttype",
            )
            self.assertEqual(
                objects_api_group_with_catalogue_with_urls.iot_attachment,
                "Attachment Informatieobjecttype",
            )

    def test_happy_flow_migrate_form(self):
        zgw_group_without_catalogue = ZGWApiGroupConfigFactory.create(
            for_test_docker_compose=True,
            catalogue_domain="",
            catalogue_rsin="",
        )
        zgw_group_with_catalogue = ZGWApiGroupConfigFactory.create(
            for_test_docker_compose=True,
            catalogue_domain="TEST",
            catalogue_rsin="000000000",
        )
        objects_api_group_without_catalogue = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True,
            catalogue_domain="",
            catalogue_rsin="",
            iot_submission_report="",
            iot_submission_csv="",
            iot_attachment="",
        )
        objects_api_group_with_catalogue = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True,
            catalogue_domain="TEST",
            catalogue_rsin="000000000",
            iot_submission_report="",
            iot_submission_csv="",
            iot_attachment="",
        )

        # form with some file components with varying configurations
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "ignoreMe",
                        "label": "Ignore me",
                    },
                    {
                        "type": "file",
                        "key": "fileToIgnore",
                        "label": "Do not update",
                        "file": {"type": []},
                        "filePattern": "",
                        "registration": {
                            "documentType": {
                                # despite these references not being valid, we don't
                                # touch them or block the migration - it is assumed the
                                # starting configuration validates the admin UI. Fixing
                                # this is out of scope, as without the migration tool
                                # this would be broken anyway
                                "catalogue": {
                                    "domain": "DNT",
                                    "rsin": "DNTDNTDNT",
                                },
                                "description": "do not touch",
                            },
                            # resolves to actual catalogue, but ignored because
                            # modern config is already present
                            "informatieobjecttype": (
                                "http://localhost:8003/catalogi/api/v1/"
                                "informatieobjecttypen/"
                                "f2908f6f-aa07-42ef-8760-74c5234f2d25"
                            ),
                        },
                    },
                    # good old edit grid - we expect file components to be detected in
                    # recursive structures
                    {
                        "type": "editgrid",
                        "key": "editgrid",
                        "label": "Edit grid",
                        "groupLabel": "Item",
                        "components": [
                            {
                                "type": "file",
                                "key": "fileToUpdate",
                                "label": "File to update",
                                "file": {"type": []},
                                "filePattern": "",
                                "registration": {
                                    # a *different* catalogue, should resolve just fine,
                                    # we can't really validate that against the
                                    # registration backends because they may have
                                    # different catalogues themselves!
                                    "informatieobjecttype": (
                                        "http://localhost:8003/catalogi/api/v1/"
                                        "informatieobjecttypen/"
                                        "f2908f6f-aa07-42ef-8760-74c5234f2d25"
                                    ),
                                },
                            },
                            {
                                "type": "file",
                                "key": "fileToIgnore2",
                                "label": "File to ignore",
                                "file": {"type": []},
                                "filePattern": "",
                                "registration": {"informatieobjecttype": ""},
                            },
                            {
                                "type": "file",
                                "key": "fileToIgnore3",
                                "label": "File to ignore",
                                "file": {"type": []},
                                "filePattern": "",
                            },
                        ],
                    },
                ],
            },
        )
        # set up registration backends with various combinations of properties...
        objects_options_1: ObjectsRegistrationOptionsV2 = {
            "informatieobjecttype_submission_report": (
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "7a474713-0833-402a-8441-e467c08ac55b"
            ),
            "informatieobjecttype_submission_csv": (
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "b2d83b94-9b9b-4e80-a82f-73ff993c62f3"
            ),
            "informatieobjecttype_attachment": (
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "531f6c1a-97f7-478c-85f0-67d2f23661c7"
            ),
            "iot_submission_report": "",
            "iot_submission_csv": "",
            "iot_attachment": "",
            "version": 2,
            "objects_api_group": objects_api_group_without_catalogue,
            # See the docker compose fixtures for more info on these values:
            "objecttype": UUID("8e46e0a5-b1b4-449b-b9e9-fa3cea655f48"),
            "objecttype_version": 3,
            "upload_submission_csv": True,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "organisatie_rsin": "000000000",
            "transform_to_list": [],
            "variables_mapping": [],
        }
        objects_backend_1 = FormRegistrationBackendFactory.create(
            form=form,
            name="Objects without catalogue in group or options",
            backend=OBJECTS_PLUGIN_IDENTIFIER,
            options=ObjectsAPIOptionsSerializer(
                instance=objects_options_1, context={"in_migrator": True}
            ).data,
        )
        objects_options_2: ObjectsRegistrationOptionsV2 = {
            "informatieobjecttype_submission_report": (
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "7a474713-0833-402a-8441-e467c08ac55b"
            ),
            # deliberately empty, these fields are optional
            "informatieobjecttype_submission_csv": "",
            "informatieobjecttype_attachment": "",
            "iot_submission_report": "",
            "iot_submission_csv": "",
            "iot_attachment": "",
            "version": 2,
            "objects_api_group": objects_api_group_with_catalogue,
            # See the docker compose fixtures for more info on these values:
            "objecttype": UUID("8e46e0a5-b1b4-449b-b9e9-fa3cea655f48"),
            "objecttype_version": 3,
            "upload_submission_csv": True,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "organisatie_rsin": "000000000",
            "transform_to_list": [],
            "variables_mapping": [],
        }
        objects_backend_2 = FormRegistrationBackendFactory.create(
            form=form,
            name="Objects with catalogue in group",
            backend=OBJECTS_PLUGIN_IDENTIFIER,
            options=ObjectsAPIOptionsSerializer(
                instance=objects_options_2, context={"in_migrator": True}
            ).data,
        )
        # type ignore because the 4.0+ types require catalogue to be set
        zgw_options_1: ZGWRegistrationOptions = {  # pyright: ignore[reportAssignmentType]
            "zgw_api_group": zgw_group_without_catalogue,
            "case_type_identification": "",
            "document_type_description": "",
            "product_url": "",
            "zaaktype": (
                "http://localhost:8003/catalogi/api/v1/zaaktypen/"
                "1f41885e-23fc-4462-bbc8-80be4ae484dc"
            ),
            "informatieobjecttype": (
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "531f6c1a-97f7-478c-85f0-67d2f23661c7"
            ),
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
            "objects_api_group": None,
            "summary_documents": [SummaryDocumentChoices.pdf],
        }
        zgw_backend_1 = FormRegistrationBackendFactory.create(
            form=form,
            name="ZGW without catalogue in group or options",
            backend="zgw-create-zaak",
            options=ZaakOptionsSerializer(
                instance=zgw_options_1, context={"in_migrator": True}
            ).data,
        )
        # type ignore because the 4.0+ types require catalogue to be set
        zgw_options_2: ZGWRegistrationOptions = {  # pyright: ignore[reportAssignmentType]
            "zgw_api_group": zgw_group_with_catalogue,
            "case_type_identification": "",
            "document_type_description": "",
            "product_url": "",
            "zaaktype": (
                "http://localhost:8003/catalogi/api/v1/zaaktypen/"
                "1f41885e-23fc-4462-bbc8-80be4ae484dc"
            ),
            "informatieobjecttype": (
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "531f6c1a-97f7-478c-85f0-67d2f23661c7"
            ),
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
            "objects_api_group": None,
            "summary_documents": [SummaryDocumentChoices.pdf],
        }
        zgw_backend_2 = FormRegistrationBackendFactory.create(
            form=form,
            name="ZGW with catalogue in group",
            backend="zgw-create-zaak",
            options=ZaakOptionsSerializer(
                instance=zgw_options_2, context={"in_migrator": True}
            ).data,
        )

        outfile = StringIO()
        migrator = Migrator(outfile=outfile)
        migrator.migrate()

        form.refresh_from_db()
        with self.subTest("formio components"):
            formio_config = form.formstep_set.get().form_definition.configuration
            (
                textfield,
                file_to_ignore,
                editgrid,
            ) = formio_config["components"]

            self.assertEqual(
                textfield,
                {
                    "type": "textfield",
                    "key": "ignoreMe",
                    "label": "Ignore me",
                },
            )
            self.assertEqual(
                file_to_ignore,
                {
                    "type": "file",
                    "key": "fileToIgnore",
                    "label": "Do not update",
                    "file": {"type": []},
                    "filePattern": "",
                    "registration": {
                        "documentType": {
                            "catalogue": {
                                "domain": "DNT",
                                "rsin": "DNTDNTDNT",
                            },
                            "description": "do not touch",
                        },
                        "informatieobjecttype": (
                            "http://localhost:8003/catalogi/api/v1/"
                            "informatieobjecttypen/"
                            "f2908f6f-aa07-42ef-8760-74c5234f2d25"
                        ),
                    },
                },
            )

            file_to_update, file_to_ignore2, file_to_ignore3 = editgrid["components"]
            self.assertEqual(
                file_to_update,
                {
                    "type": "file",
                    "key": "fileToUpdate",
                    "label": "File to update",
                    "file": {"type": []},
                    "filePattern": "",
                    "registration": {
                        "documentType": {
                            "catalogue": {
                                "domain": "OTHER",
                                "rsin": "000000000",
                            },
                            "description": "PDF Informatieobjecttype other catalog",
                        },
                        "informatieobjecttype": (
                            "http://localhost:8003/catalogi/api/v1/"
                            "informatieobjecttypen/"
                            "f2908f6f-aa07-42ef-8760-74c5234f2d25"
                        ),
                    },
                },
            )
            self.assertEqual(
                file_to_ignore2,
                {
                    "type": "file",
                    "key": "fileToIgnore2",
                    "label": "File to ignore",
                    "file": {"type": []},
                    "filePattern": "",
                    "registration": {"informatieobjecttype": ""},
                },
            )
            self.assertEqual(
                file_to_ignore3,
                {
                    "type": "file",
                    "key": "fileToIgnore3",
                    "label": "File to ignore",
                    "file": {"type": []},
                    "filePattern": "",
                },
            )

        with self.subTest("backend: objects api, without catalogue"):
            objects_backend_1.refresh_from_db()
            objects_api_group_without_catalogue.refresh_from_db()
            self.assertEqual(
                objects_backend_1.options["catalogue"],
                {
                    "domain": "TEST",
                    "rsin": "000000000",
                },
            )
            self.assertEqual(
                objects_backend_1.options["iot_submission_report"],
                "PDF Informatieobjecttype",
            )
            self.assertEqual(
                objects_backend_1.options["iot_submission_csv"],
                "CSV Informatieobjecttype",
            )
            self.assertEqual(
                objects_backend_1.options["iot_attachment"],
                "Attachment Informatieobjecttype",
            )
            self.assertEqual(objects_api_group_without_catalogue.catalogue_domain, "")
            self.assertEqual(objects_api_group_without_catalogue.catalogue_rsin, "")
            self.assertEqual(
                objects_api_group_without_catalogue.iot_submission_report, ""
            )
            self.assertEqual(objects_api_group_without_catalogue.iot_submission_csv, "")
            self.assertEqual(objects_api_group_without_catalogue.iot_attachment, "")

        with self.subTest("backend: objects api, with catalogue"):
            objects_backend_2.refresh_from_db()
            objects_api_group_with_catalogue.refresh_from_db()
            self.assertNotIn("catalogue", objects_backend_2.options)
            self.assertEqual(
                objects_backend_2.options["iot_submission_report"],
                "PDF Informatieobjecttype",
            )
            self.assertEqual(objects_backend_2.options["iot_submission_csv"], "")
            self.assertEqual(objects_backend_2.options["iot_attachment"], "")
            self.assertEqual(objects_api_group_with_catalogue.catalogue_domain, "TEST")
            self.assertEqual(
                objects_api_group_with_catalogue.catalogue_rsin, "000000000"
            )
            self.assertEqual(objects_api_group_with_catalogue.iot_submission_report, "")
            self.assertEqual(objects_api_group_with_catalogue.iot_submission_csv, "")
            self.assertEqual(objects_api_group_with_catalogue.iot_attachment, "")

        with self.subTest("backend: zgw, without catalogue"):
            zgw_backend_1.refresh_from_db()
            zgw_group_without_catalogue.refresh_from_db()

            self.assertEqual(
                zgw_backend_1.options["catalogue"],
                {
                    "domain": "TEST",
                    "rsin": "000000000",
                },
            )
            self.assertEqual(
                zgw_backend_1.options["case_type_identification"],
                "ZT-001",
            )
            self.assertEqual(
                zgw_backend_1.options["document_type_description"],
                "Attachment Informatieobjecttype",
            )
            self.assertEqual(zgw_group_without_catalogue.catalogue_domain, "")
            self.assertEqual(zgw_group_without_catalogue.catalogue_rsin, "")

        with self.subTest("backend: zgw, with catalogue"):
            zgw_backend_2.refresh_from_db()
            zgw_group_with_catalogue.refresh_from_db()

            # it gets migrated to the options either way
            self.assertIn("catalogue", zgw_backend_2.options)
            self.assertEqual(
                zgw_backend_2.options["case_type_identification"],
                "ZT-001",
            )
            self.assertEqual(
                zgw_backend_2.options["document_type_description"],
                "Attachment Informatieobjecttype",
            )
            self.assertEqual(zgw_group_with_catalogue.catalogue_domain, "TEST")
            self.assertEqual(zgw_group_with_catalogue.catalogue_rsin, "000000000")

    def test_happy_flow_already_modern_config_is_left_untouched(self):
        zgw_group_with_catalogue = ZGWApiGroupConfigFactory.create(
            for_test_docker_compose=True,
            catalogue_domain="TEST",
            catalogue_rsin="000000000",
        )
        objects_api_group_with_catalogue = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True,
            catalogue_domain="TEST",
            catalogue_rsin="000000000",
            iot_submission_report="",
            iot_submission_csv="",
            iot_attachment="",
        )
        form = FormFactory.create()
        # set up registration backends with various combinations of properties...
        objects_options_1: ObjectsRegistrationOptionsV2 = {
            "informatieobjecttype_submission_report": (
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "7a474713-0833-402a-8441-e467c08ac55b"
            ),
            "informatieobjecttype_submission_csv": (
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "b2d83b94-9b9b-4e80-a82f-73ff993c62f3"
            ),
            "informatieobjecttype_attachment": (
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "531f6c1a-97f7-478c-85f0-67d2f23661c7"
            ),
            "iot_submission_report": "do-not-touch",
            "iot_submission_csv": "do-not-touch",
            "iot_attachment": "do-not-touch",
            "version": 2,
            "objects_api_group": objects_api_group_with_catalogue,
            # See the docker compose fixtures for more info on these values:
            "objecttype": UUID("8e46e0a5-b1b4-449b-b9e9-fa3cea655f48"),
            "objecttype_version": 3,
            "upload_submission_csv": True,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "organisatie_rsin": "000000000",
            "transform_to_list": [],
            "variables_mapping": [],
        }
        objects_backend_1 = FormRegistrationBackendFactory.create(
            form=form,
            name="All document types already configured",
            backend=OBJECTS_PLUGIN_IDENTIFIER,
            options=ObjectsAPIOptionsSerializer(
                instance=objects_options_1, context={"in_migrator": True}
            ).data,
        )
        objects_options_2: ObjectsRegistrationOptionsV2 = {
            "informatieobjecttype_submission_report": (
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "7a474713-0833-402a-8441-e467c08ac55b"
            ),
            # deliberately empty, these fields are optional
            "informatieobjecttype_submission_csv": "",
            "informatieobjecttype_attachment": "",
            "iot_submission_report": "",
            "iot_submission_csv": "do-not-touch",
            "iot_attachment": "do-not-touch",
            "version": 2,
            "objects_api_group": objects_api_group_with_catalogue,
            # See the docker compose fixtures for more info on these values:
            "objecttype": UUID("8e46e0a5-b1b4-449b-b9e9-fa3cea655f48"),
            "objecttype_version": 3,
            "upload_submission_csv": True,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "organisatie_rsin": "000000000",
            "transform_to_list": [],
            "variables_mapping": [],
        }
        objects_backend_2 = FormRegistrationBackendFactory.create(
            form=form,
            name="Partial document types already configured",
            backend=OBJECTS_PLUGIN_IDENTIFIER,
            options=ObjectsAPIOptionsSerializer(
                instance=objects_options_2, context={"in_migrator": True}
            ).data,
        )
        # type ignore because the 4.0+ types require catalogue to be set
        zgw_options_1: ZGWRegistrationOptions = {  # pyright: ignore[reportAssignmentType]
            "zgw_api_group": zgw_group_with_catalogue,
            "case_type_identification": "do-not-touch",
            "document_type_description": "do-not-touch",
            "product_url": "",
            "zaaktype": (
                "http://localhost:8003/catalogi/api/v1/zaaktypen/"
                "1f41885e-23fc-4462-bbc8-80be4ae484dc"
            ),
            "informatieobjecttype": (
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "531f6c1a-97f7-478c-85f0-67d2f23661c7"
            ),
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
            "objects_api_group": None,
            "summary_documents": [SummaryDocumentChoices.pdf],
        }
        zgw_backend_1 = FormRegistrationBackendFactory.create(
            form=form,
            name="Case type and document type references configured",
            backend="zgw-create-zaak",
            options=ZaakOptionsSerializer(
                instance=zgw_options_1, context={"in_migrator": True}
            ).data,
        )
        # type ignore because the 4.0+ types require catalogue to be set
        zgw_options_2: ZGWRegistrationOptions = {  # pyright: ignore[reportAssignmentType]
            "zgw_api_group": zgw_group_with_catalogue,
            "case_type_identification": "",
            "document_type_description": "PDF Informatieobjecttype",
            "product_url": "",
            "zaaktype": (
                "http://localhost:8003/catalogi/api/v1/zaaktypen/"
                "1f41885e-23fc-4462-bbc8-80be4ae484dc"
            ),
            "informatieobjecttype": (
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "531f6c1a-97f7-478c-85f0-67d2f23661c7"
            ),
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
            "objects_api_group": None,
            "summary_documents": [SummaryDocumentChoices.pdf],
        }
        zgw_backend_2 = FormRegistrationBackendFactory.create(
            form=form,
            name="Document type reference configured",
            backend="zgw-create-zaak",
            options=ZaakOptionsSerializer(
                instance=zgw_options_2, context={"in_migrator": True}
            ).data,
        )

        outfile = StringIO()
        migrator = Migrator(outfile=outfile)
        migrator.migrate()

        with self.subTest("objects backend 1 is untouched"):
            objects_backend_1.refresh_from_db()
            self.assertEqual(
                objects_backend_1.options["iot_submission_report"], "do-not-touch"
            )
            self.assertEqual(
                objects_backend_1.options["iot_submission_csv"], "do-not-touch"
            )
            self.assertEqual(
                objects_backend_1.options["iot_attachment"], "do-not-touch"
            )

        with self.subTest("objects backend 2 is partially updated"):
            objects_backend_2.refresh_from_db()
            self.assertEqual(
                objects_backend_2.options["iot_submission_report"],
                "PDF Informatieobjecttype",
            )
            self.assertEqual(
                objects_backend_2.options["iot_submission_csv"], "do-not-touch"
            )
            self.assertEqual(
                objects_backend_2.options["iot_attachment"], "do-not-touch"
            )

        with self.subTest("zgw backend 1 is untouched"):
            zgw_backend_1.refresh_from_db()
            self.assertEqual(
                zgw_backend_1.options["case_type_identification"], "do-not-touch"
            )
            self.assertEqual(
                zgw_backend_1.options["document_type_description"], "do-not-touch"
            )

        with self.subTest("zgw backend 2 is partially updated"):
            zgw_backend_2.refresh_from_db()
            self.assertEqual(
                zgw_backend_2.options["case_type_identification"], "ZT-001"
            )
            self.assertEqual(
                zgw_backend_2.options["document_type_description"],
                "PDF Informatieobjecttype",
            )

    def test_reusable_formstep_processed_only_once(self):
        fd = FormDefinitionFactory.create(name="Reusable fd", is_reusable=True)
        FormFactory.create_batch(
            2,
            generate_minimal_setup=True,
            formstep__form_definition=fd,
        )
        outfile = StringIO()
        migrator = Migrator(outfile=outfile)

        migrator.migrate()

        output = outfile.getvalue()
        self.assertIn("Reusable fd", output)
        self.assertEqual(output.count("Reusable fd"), 1)

    def test_error_flow_bad_file_component_informatieobjecttype_references(self):
        # set up a service for the local docker compose URLs
        ZGWApiGroupConfigFactory.create(
            for_test_docker_compose=True,
            catalogue_domain="",
            catalogue_rsin="",
        )
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "file",
                        "key": "fileToUpdate1",
                        "label": "File to update",
                        "file": {"type": []},
                        "filePattern": "",
                        "registration": {
                            # Simulates a URL to ACC on a PROD environment, which *does*
                            # happen
                            "informatieobjecttype": (
                                "http://bad.host.internal:80/catalogi/api/v1/"
                                "informatieobjecttypen/"
                                "f2908f6f-aa07-42ef-8760-74c5234f2d25"
                            ),
                        },
                    },
                    {
                        "type": "file",
                        "key": "fileToUpdate2",
                        "label": "File to update",
                        "file": {"type": []},
                        "filePattern": "",
                        "registration": {
                            # valid URL/host, but the UUID does not exist (404)
                            "informatieobjecttype": (
                                "http://localhost:8003/catalogi/api/v1/"
                                "informatieobjecttypen/"
                                "183f2c86-8651-4ca2-afd8-81c40ede21a9"
                            ),
                        },
                    },
                ],
            },
        )
        outfile = StringIO()
        migrator = Migrator(outfile=outfile)

        with self.assertRaisesMessage(
            MigrationProblem,
            "There are automatic migration problems, please analyze the output.",
        ):
            migrator.migrate()

        output = outfile.getvalue()

        with self.subTest("resolution error with unknown host"):
            self.assertIn(form.admin_name, output)
            self.assertIn("fileToUpdate1", output)
            self.assertIn("No service configured", output)

        with self.subTest("resolution error with bad UUID"):
            self.assertIn(form.admin_name, output)
            self.assertIn("fileToUpdate2", output)
            self.assertIn("Documenttype URL response:", output)
            self.assertIn("HTTP 404", output)

    def test_error_flow_objects_api_invalid_registration_options(self):
        FormRegistrationBackendFactory.create(
            name="Invalid registration options",
            backend=OBJECTS_PLUGIN_IDENTIFIER,
            options={},
        )
        outfile = StringIO()
        migrator = Migrator(outfile=outfile)

        with self.assertRaisesMessage(
            MigrationProblem,
            "There are automatic migration problems, please analyze the output.",
        ):
            migrator.migrate()

        output = outfile.getvalue()
        self.assertIn("The registration options are not valid.", output)

    def test_error_flow_objects_api_inconsistent_catalogues_used(self):
        objects_api_group_without_catalogue = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True,
            catalogue_domain="",
            catalogue_rsin="",
            iot_submission_report="",
            iot_submission_csv="",
            iot_attachment="",
        )
        form = FormFactory.create()
        objects_options_1: ObjectsRegistrationOptionsV2 = {
            # catalogue TEST/000000000
            "informatieobjecttype_submission_report": (
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "7a474713-0833-402a-8441-e467c08ac55b"
            ),
            # catalogue OTHER/000000000
            "informatieobjecttype_submission_csv": (
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "cd6aeaf2-ca37-416f-b78c-1cc302f81a81"
            ),
            "informatieobjecttype_attachment": "",
            "iot_submission_report": "",
            "iot_submission_csv": "",
            "iot_attachment": "",
            "version": 2,
            "objects_api_group": objects_api_group_without_catalogue,
            # See the docker compose fixtures for more info on these values:
            "objecttype": UUID("8e46e0a5-b1b4-449b-b9e9-fa3cea655f48"),
            "objecttype_version": 3,
            "upload_submission_csv": True,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "organisatie_rsin": "000000000",
            "transform_to_list": [],
            "variables_mapping": [],
        }
        FormRegistrationBackendFactory.create(
            form=form,
            name="Document types with mismatched catalogues",
            backend=OBJECTS_PLUGIN_IDENTIFIER,
            options=ObjectsAPIOptionsSerializer(
                instance=objects_options_1, context={"in_migrator": True}
            ).data,
        )
        objects_options_2: ObjectsRegistrationOptionsV2 = {
            "catalogue": {
                "domain": "OTHER",
                "rsin": "000000000",
            },
            # catalogue TEST/000000000
            "informatieobjecttype_submission_report": (
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "7a474713-0833-402a-8441-e467c08ac55b"
            ),
            # catalogue OTHER/000000000
            "informatieobjecttype_submission_csv": "",
            "informatieobjecttype_attachment": "",
            "iot_submission_report": "",
            "iot_submission_csv": "",
            "iot_attachment": "",
            "version": 2,
            "objects_api_group": objects_api_group_without_catalogue,
            # See the docker compose fixtures for more info on these values:
            "objecttype": UUID("8e46e0a5-b1b4-449b-b9e9-fa3cea655f48"),
            "objecttype_version": 3,
            "upload_submission_csv": True,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "organisatie_rsin": "000000000",
            "transform_to_list": [],
            "variables_mapping": [],
        }
        FormRegistrationBackendFactory.create(
            form=form,
            name="Document type & options catalogue mismatch",
            backend=OBJECTS_PLUGIN_IDENTIFIER,
            options=ObjectsAPIOptionsSerializer(
                instance=objects_options_2, context={"in_migrator": True}
            ).data,
        )
        outfile = StringIO()
        migrator = Migrator(outfile=outfile)

        with self.assertRaisesMessage(
            MigrationProblem,
            "There are automatic migration problems, please analyze the output.",
        ):
            migrator.migrate()

        output = outfile.getvalue()
        self.assertIn(
            "Resolving the document types didn't converge to a single catalogue", output
        )
        self.assertIn("OTHER", output)
        self.assertIn("TEST", output)
        self.assertIn("(000000000)", output)

    def test_error_flow_objects_api_invalid_urls_used(self):
        api_group = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True,
            catalogue_domain="",
            catalogue_rsin="",
            iot_submission_report="",
            iot_submission_csv="",
            iot_attachment="",
        )
        objects_options_1: ObjectsRegistrationOptionsV2 = {
            # Does not exist in fixture data
            "informatieobjecttype_submission_report": (
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "a8fa5a01-41a2-48c0-aac8-807bad95b2bb"
            ),
            "informatieobjecttype_submission_csv": "",
            "informatieobjecttype_attachment": "",
            "iot_submission_report": "",
            "iot_submission_csv": "",
            "iot_attachment": "",
            "version": 2,
            "objects_api_group": api_group,
            # See the docker compose fixtures for more info on these values:
            "objecttype": UUID("8e46e0a5-b1b4-449b-b9e9-fa3cea655f48"),
            "objecttype_version": 3,
            "upload_submission_csv": True,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "organisatie_rsin": "000000000",
            "transform_to_list": [],
            "variables_mapping": [],
        }
        FormRegistrationBackendFactory.create(
            name="Objects with bad PDF document type (404)",
            backend=OBJECTS_PLUGIN_IDENTIFIER,
            options=ObjectsAPIOptionsSerializer(
                instance=objects_options_1, context={"in_migrator": True}
            ).data,
        )
        outfile = StringIO()
        migrator = Migrator(outfile=outfile)

        with self.assertRaisesMessage(
            MigrationProblem,
            "There are automatic migration problems, please analyze the output.",
        ):
            migrator.migrate()

        output = outfile.getvalue()
        self.assertIn("HTTP 404", output)

    def test_error_flow_objects_api_groups_inconsistent_catalogues_used(self):
        ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True,
            catalogue_domain="",
            catalogue_rsin="",
            iot_submission_report="",
            iot_submission_csv="",
            iot_attachment="",
            # catalogue TEST/000000000
            informatieobjecttype_submission_report=(
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "7a474713-0833-402a-8441-e467c08ac55b"
            ),
            informatieobjecttype_submission_csv="",
            # catalogue OTHER/000000000
            informatieobjecttype_attachment=(
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "cd6aeaf2-ca37-416f-b78c-1cc302f81a81"
            ),
        )
        ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True,
            catalogue_domain="TEST",
            catalogue_rsin="000000000",
            iot_submission_report="",
            iot_submission_csv="",
            iot_attachment="",
            # catalogue OTHER/000000000
            informatieobjecttype_submission_report=(
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "cd6aeaf2-ca37-416f-b78c-1cc302f81a81"
            ),
            informatieobjecttype_submission_csv="",
            informatieobjecttype_attachment="",
        )

        outfile = StringIO()
        migrator = Migrator(outfile=outfile)

        with self.assertRaisesMessage(
            MigrationProblem,
            "There are automatic migration problems, please analyze the output.",
        ):
            migrator.migrate()

        output = outfile.getvalue()
        self.assertIn(
            "resolving the document types didn't converge to a single catalogue", output
        )
        self.assertIn("OTHER", output)
        self.assertIn("TEST", output)
        self.assertIn("(000000000)", output)

    def test_error_flow_objects_api_groups_invalid_url_used(self):
        ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True,
            catalogue_domain="",
            catalogue_rsin="",
            iot_submission_report="",
            iot_submission_csv="",
            iot_attachment="",
            # Does not exist in fixture data
            informatieobjecttype_submission_report=(
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "a8fa5a01-41a2-48c0-aac8-807bad95b2bb"
            ),
            informatieobjecttype_submission_csv="",
            informatieobjecttype_attachment="",
        )

        outfile = StringIO()
        migrator = Migrator(outfile=outfile)

        with self.assertRaisesMessage(
            MigrationProblem,
            "There are automatic migration problems, please analyze the output.",
        ):
            migrator.migrate()

        output = outfile.getvalue()
        self.assertIn("HTTP 404", output)

    def test_error_flow_zgw_invalid_registration_options(self):
        FormRegistrationBackendFactory.create(
            name="Invalid registration options",
            backend="zgw-create-zaak",
            options={},
        )
        outfile = StringIO()
        migrator = Migrator(outfile=outfile)

        with self.assertRaisesMessage(
            MigrationProblem,
            "There are automatic migration problems, please analyze the output.",
        ):
            migrator.migrate()

        output = outfile.getvalue()
        self.assertIn("The registration options are not valid.", output)

    def test_error_flow_zgw_invalid_case_type_references(self):
        # set up a service for the local docker compose URLs
        api_group = ZGWApiGroupConfigFactory.create(
            for_test_docker_compose=True,
            catalogue_domain="",
            catalogue_rsin="",
        )
        form = FormFactory.create()
        # type ignore because the 4.0+ types require catalogue to be set
        zgw_options_1: ZGWRegistrationOptions = {  # pyright: ignore[reportAssignmentType]
            "zgw_api_group": api_group,
            "case_type_identification": "",
            "document_type_description": "",
            "product_url": "",
            # Simulates URLs to ACC on a PROD environment, which *does*
            # happen
            "zaaktype": (
                "http://bad.host.internal:80/catalogi/api/v1/zaaktypen/"
                "1f41885e-23fc-4462-bbc8-80be4ae484dc"
            ),
            "informatieobjecttype": (
                "http://bad.host.internal:80/catalogi/api/v1/"
                "informatieobjecttypen/f2908f6f-aa07-42ef-8760-74c5234f2d25"
            ),
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
            "objects_api_group": None,
            "summary_documents": [SummaryDocumentChoices.pdf],
        }
        FormRegistrationBackendFactory.create(
            form=form,
            name="ZGW with bad hostnames",
            backend="zgw-create-zaak",
            options=ZaakOptionsSerializer(
                instance=zgw_options_1, context={"in_migrator": True}
            ).data,
        )
        # type ignore because the 4.0+ types require catalogue to be set
        zgw_options_2: ZGWRegistrationOptions = {  # pyright: ignore[reportAssignmentType]
            "zgw_api_group": api_group,
            "case_type_identification": "",
            "document_type_description": "",
            "product_url": "",
            # valid URLs/hosts, but the UUID does not exist (404)
            "zaaktype": (
                "http://localhost:8003/catalogi/api/v1/zaaktypen/"
                "5b362092-3625-46db-ab37-c5eeb276c9ac"
            ),
            "informatieobjecttype": (
                "http://localhost:8003/catalogi/api/v1/"
                "informatieobjecttypen/183f2c86-8651-4ca2-afd8-81c40ede21a9"
            ),
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
            "objects_api_group": None,
            "summary_documents": [SummaryDocumentChoices.pdf],
        }
        FormRegistrationBackendFactory.create(
            form=form,
            name="ZGW 404 resource links",
            backend="zgw-create-zaak",
            options=ZaakOptionsSerializer(
                instance=zgw_options_2, context={"in_migrator": True}
            ).data,
        )

        outfile = StringIO()
        migrator = Migrator(outfile=outfile)

        with self.assertRaisesMessage(
            MigrationProblem,
            "There are automatic migration problems, please analyze the output.",
        ):
            migrator.migrate()

        output = outfile.getvalue()

        self.assertIn("No service configured", output)
        self.assertIn("HTTP 404", output)

    def test_error_flow_zgw_invalid_document_type_references(self):
        # set up a service for the local docker compose URLs
        api_group = ZGWApiGroupConfigFactory.create(
            for_test_docker_compose=True,
            catalogue_domain="",
            catalogue_rsin="",
        )
        form = FormFactory.create()
        # type ignore because the 4.0+ types require catalogue to be set
        zgw_options_1: ZGWRegistrationOptions = {  # pyright: ignore[reportAssignmentType]
            "zgw_api_group": api_group,
            "case_type_identification": "",
            "document_type_description": "",
            "product_url": "",
            "zaaktype": (
                "http://localhost:8003/catalogi/api/v1/zaaktypen/"
                "1f41885e-23fc-4462-bbc8-80be4ae484dc"
            ),
            # unknown/unresolvable host name
            "informatieobjecttype": (
                "http://bad.host.internal:80/catalogi/api/v1/informatieobjecttypen/"
                "531f6c1a-97f7-478c-85f0-67d2f23661c7"
            ),
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
            "objects_api_group": None,
            "summary_documents": [SummaryDocumentChoices.pdf],
        }
        FormRegistrationBackendFactory.create(
            form=form,
            name="ZGW with bad document type hostnames",
            backend="zgw-create-zaak",
            options=ZaakOptionsSerializer(
                instance=zgw_options_1, context={"in_migrator": True}
            ).data,
        )
        # type ignore because the 4.0+ types require catalogue to be set
        zgw_options_2: ZGWRegistrationOptions = {  # pyright: ignore[reportAssignmentType]
            "zgw_api_group": api_group,
            "case_type_identification": "",
            "document_type_description": "",
            "product_url": "",
            "zaaktype": (
                "http://localhost:8003/catalogi/api/v1/zaaktypen/"
                "1f41885e-23fc-4462-bbc8-80be4ae484dc"
            ),
            # UUID points to nothing
            "informatieobjecttype": (
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "5b362092-3625-46db-ab37-c5eeb276c9ac"
            ),
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
            "objects_api_group": None,
            "summary_documents": [SummaryDocumentChoices.pdf],
        }
        FormRegistrationBackendFactory.create(
            form=form,
            name="ZGW 404 document type resource links",
            backend="zgw-create-zaak",
            options=ZaakOptionsSerializer(
                instance=zgw_options_2, context={"in_migrator": True}
            ).data,
        )

        outfile = StringIO()
        migrator = Migrator(outfile=outfile)

        with self.assertRaisesMessage(
            MigrationProblem,
            "There are automatic migration problems, please analyze the output.",
        ):
            migrator.migrate()

        output = outfile.getvalue()

        self.assertIn("No service configured", output)
        self.assertIn("HTTP 404", output)

    def test_error_flow_zgw_case_type_document_type_have_different_catalogues(self):
        # set up a service for the local docker compose URLs
        api_group = ZGWApiGroupConfigFactory.create(
            for_test_docker_compose=True,
            catalogue_domain="",
            catalogue_rsin="",
        )
        form = FormFactory.create()
        # type ignore because the 4.0+ types require catalogue to be set
        zgw_options_1: ZGWRegistrationOptions = {  # pyright: ignore[reportAssignmentType]
            "zgw_api_group": api_group,
            "case_type_identification": "",
            "document_type_description": "",
            "product_url": "",
            # in the TEST/000000000 catalogue
            "zaaktype": (
                "http://localhost:8003/catalogi/api/v1/zaaktypen/"
                "1f41885e-23fc-4462-bbc8-80be4ae484dc"
            ),
            # in the OTHER/000000000 catalogue
            "informatieobjecttype": (
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "cd6aeaf2-ca37-416f-b78c-1cc302f81a81"
            ),
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
            "objects_api_group": None,
            "summary_documents": [SummaryDocumentChoices.pdf],
        }
        FormRegistrationBackendFactory.create(
            form=form,
            name="ZGW with bad document type hostnames",
            backend="zgw-create-zaak",
            options=ZaakOptionsSerializer(
                instance=zgw_options_1, context={"in_migrator": True}
            ).data,
        )

        outfile = StringIO()
        migrator = Migrator(outfile=outfile)

        with self.assertRaisesMessage(
            MigrationProblem,
            "There are automatic migration problems, please analyze the output.",
        ):
            migrator.migrate()

        output = outfile.getvalue()

        self.assertIn(
            "Resolving the case/document types didn't converge to a single catalogue.",
            output,
        )

    def test_error_flow_zgw_case_type_document_type_options_different_catalogue(self):
        # set up a service for the local docker compose URLs
        api_group = ZGWApiGroupConfigFactory.create(
            for_test_docker_compose=True,
            catalogue_domain="",
            catalogue_rsin="",
        )
        form = FormFactory.create()
        zgw_options_1: ZGWRegistrationOptions = {  # type: ignore
            "zgw_api_group": api_group,
            "catalogue": {
                "domain": "OTHER",
                "rsin": "000000000",
            },
            "case_type_identification": "",
            "document_type_description": "",
            "product_url": "",
            # in the TEST/000000000 catalogue
            "zaaktype": (
                "http://localhost:8003/catalogi/api/v1/zaaktypen/"
                "1f41885e-23fc-4462-bbc8-80be4ae484dc"
            ),
            # in the TEST/000000000 catalogue
            "informatieobjecttype": (
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "531f6c1a-97f7-478c-85f0-67d2f23661c7"
            ),
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
            "objects_api_group": None,
            "summary_documents": [SummaryDocumentChoices.pdf],
        }
        FormRegistrationBackendFactory.create(
            form=form,
            name="ZGW with bad document type hostnames",
            backend="zgw-create-zaak",
            options=ZaakOptionsSerializer(
                instance=zgw_options_1, context={"in_migrator": True}
            ).data,
        )

        outfile = StringIO()
        migrator = Migrator(outfile=outfile)

        with self.assertRaisesMessage(
            MigrationProblem,
            "There are automatic migration problems, please analyze the output.",
        ):
            migrator.migrate()

        output = outfile.getvalue()

        self.assertIn(
            "Resolving the case/document types didn't converge to a single catalogue.",
            output,
        )

    def test_error_flow_zgw_document_type_does_not_belong_to_case_type(self):
        api_group = ZGWApiGroupConfigFactory.create(
            for_test_docker_compose=True,
            catalogue_domain="",
            catalogue_rsin="",
        )
        form = FormFactory.create()
        zgw_options_1: ZGWRegistrationOptions = {  # type: ignore
            "zgw_api_group": api_group,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "case_type_identification": "ZT-002",  # has no related document types
            "document_type_description": "",
            "product_url": "",
            "zaaktype": "",
            # in the TEST/000000000 catalogue
            "informatieobjecttype": (
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "531f6c1a-97f7-478c-85f0-67d2f23661c7"
            ),
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
            "objects_api_group": None,
            "summary_documents": [SummaryDocumentChoices.pdf],
        }
        FormRegistrationBackendFactory.create(
            form=form,
            name="ZGW with incorrect relations",
            backend="zgw-create-zaak",
            options=ZaakOptionsSerializer(
                instance=zgw_options_1, context={"in_migrator": True}
            ).data,
        )

        outfile = StringIO()
        migrator = Migrator(outfile=outfile)

        with self.assertRaisesMessage(
            MigrationProblem,
            "There are automatic migration problems, please analyze the output.",
        ):
            migrator.migrate()

        output = outfile.getvalue()

        self.assertIn(
            "The specified case types, document types and/or catalogue do not belong "
            "together.",
            output,
        )


class ManagementCommandTests(OFVCRMixin, TestCase):
    def test_transaction_does_not_commit_by_default(self):
        api_group = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True,
            identifier=str(uuid4()),
            catalogue_domain="",
            catalogue_rsin="",
            iot_submission_report="",
            iot_submission_csv="",
            iot_attachment="",
            informatieobjecttype_submission_report=(
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "7a474713-0833-402a-8441-e467c08ac55b"
            ),
            informatieobjecttype_submission_csv=(
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "b2d83b94-9b9b-4e80-a82f-73ff993c62f3"
            ),
            informatieobjecttype_attachment=(
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "531f6c1a-97f7-478c-85f0-67d2f23661c7"
            ),
        )
        stdout = StringIO()
        stderr = StringIO()

        # no error implies this was performed successfully
        call_command("migrate_catalogi_api_urls", stdout=stdout, stderr=stderr)

        api_group.refresh_from_db()
        # expect no changes to be committed
        self.assertEqual(api_group.iot_submission_report, "")
        self.assertEqual(api_group.iot_submission_csv, "")
        self.assertEqual(api_group.iot_attachment, "")

    def test_commits_when_flag_is_passed(self):
        api_group = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True,
            identifier=str(uuid4()),
            catalogue_domain="",
            catalogue_rsin="",
            iot_submission_report="",
            iot_submission_csv="",
            iot_attachment="",
            informatieobjecttype_submission_report=(
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "7a474713-0833-402a-8441-e467c08ac55b"
            ),
            informatieobjecttype_submission_csv=(
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "b2d83b94-9b9b-4e80-a82f-73ff993c62f3"
            ),
            informatieobjecttype_attachment=(
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "531f6c1a-97f7-478c-85f0-67d2f23661c7"
            ),
        )
        stdout = StringIO()
        stderr = StringIO()

        # no error implies this was performed successfully
        call_command(
            "migrate_catalogi_api_urls", "--no-dryrun", stdout=stdout, stderr=stderr
        )

        api_group.refresh_from_db()
        # expect changes to be committed
        self.assertEqual(api_group.iot_submission_report, "PDF Informatieobjecttype")
        self.assertEqual(api_group.iot_submission_csv, "CSV Informatieobjecttype")
        self.assertEqual(api_group.iot_attachment, "Attachment Informatieobjecttype")

    def test_reports_error_when_problems_are_encountered(self):
        api_group = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True,
            identifier=str(uuid4()),
            catalogue_domain="OTHER",
            catalogue_rsin="000000000",
            iot_submission_report="",
            iot_submission_csv="",
            iot_attachment="",
            # document types & group catalogue mismatch
            informatieobjecttype_submission_report=(
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "7a474713-0833-402a-8441-e467c08ac55b"
            ),
            informatieobjecttype_submission_csv=(
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "b2d83b94-9b9b-4e80-a82f-73ff993c62f3"
            ),
            informatieobjecttype_attachment=(
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "531f6c1a-97f7-478c-85f0-67d2f23661c7"
            ),
        )
        stdout = StringIO()
        stderr = StringIO()

        with self.assertRaisesMessage(
            CommandError,
            "There are automatic migration problems, please analyze the output.",
        ):
            call_command(
                "migrate_catalogi_api_urls", "--no-dryrun", stdout=stdout, stderr=stderr
            )

        api_group.refresh_from_db()
        # expect no changes to be committed
        self.assertEqual(api_group.iot_submission_report, "")
        self.assertEqual(api_group.iot_submission_csv, "")
        self.assertEqual(api_group.iot_attachment, "")
