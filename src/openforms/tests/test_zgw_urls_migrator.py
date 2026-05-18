from io import StringIO
from uuid import UUID

from django.test import TestCase

from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory
from openforms.forms.tests.factories import FormFactory, FormRegistrationBackendFactory
from openforms.registrations.contrib.objects_api.config import (
    ObjectsAPIOptionsSerializer,
)
from openforms.registrations.contrib.objects_api.constants import (
    PLUGIN_IDENTIFIER as OBJECTS_PLUGIN_IDENTIFIER,
)
from openforms.registrations.contrib.objects_api.typing import (
    RegistrationOptionsV2 as ObjectsRegistrationOptionsV2,
)
from openforms.registrations.contrib.zgw_apis.tests.factories import (
    ZGWApiGroupConfigFactory,
)
from openforms.utils.tests.vcr import OFVCRMixin

from ..zgw_urls_migrator import Migrator


class MigratorTests(OFVCRMixin, TestCase):
    """
    Requires the VCR services, see ``docker/start_vcr_services.sh``.
    """

    maxDiff = None

    def test_doesnot_crash_without_any_data(self):
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
                        "components": [
                            {
                                "type": "file",
                                "key": "fileToUpdate",
                                "label": "File to update",
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
                                "registration": {"informatieobjecttype": ""},
                            },
                            {
                                "type": "file",
                                "key": "fileToIgnore3",
                                "label": "File to ignore",
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
            options=ObjectsAPIOptionsSerializer(instance=objects_options_1).data,
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
            name="Objects without catalogue in group or options",
            backend=OBJECTS_PLUGIN_IDENTIFIER,
            options=ObjectsAPIOptionsSerializer(instance=objects_options_2).data,
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
                    "registration": {"informatieobjecttype": ""},
                },
            )
            self.assertEqual(
                file_to_ignore3,
                {
                    "type": "file",
                    "key": "fileToIgnore3",
                    "label": "File to ignore",
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

        # with self.subTest("zgw backends"):
        #     breakpoint()
