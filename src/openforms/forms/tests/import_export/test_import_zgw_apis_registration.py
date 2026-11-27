from django.test import TestCase

from rest_framework.exceptions import ErrorDetail, ValidationError

from openforms.contrib.objects_api.models import ObjectsAPIGroupConfig
from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory
from openforms.registrations.contrib.zgw_apis.options import ZaakOptionsSerializer
from openforms.registrations.contrib.zgw_apis.tests.factories import (
    ZGWApiGroupConfigFactory,
)
from openforms.registrations.contrib.zgw_apis.typing import RegistrationOptions
from openforms.utils.tests.vcr import OFVCRMixin

from ...import_export.service import (
    Artifact,
    FormImportOptions,
    import_form_data,
)


class ImportConversionTests(OFVCRMixin, TestCase):
    """
    This test case requires the Open Zaak Docker Compose to be running.

    See the relevant Docker compose in the ``docker/`` folder.
    """

    def test_missing_objects_api_group_is_backfilled(self):
        # In legacy imports, `options.objects_api_group` was not required, because the
        # plugin always used the ObjectsAPIGroup with the lowest primary key at runtime.
        # Because `options.objects_api_group` has been made required, this should be
        # injected into the import data to make sure the import still works
        api_group = ZGWApiGroupConfigFactory.create(for_test_docker_compose=True)
        objects_api_group, objects_api_group_2 = (
            ObjectsAPIGroupConfigFactory.create_batch(2, for_test_docker_compose=True)
        )
        artifact = Artifact(
            forms=[
                {
                    "name": "Test form",
                    "slug": "my-slug",
                    "registration_backends": [
                        {
                            "key": "test",
                            "name": "test",
                            "backend": "zgw-create-zaak",
                            "options": {
                                "zgw_api_group": api_group.pk,
                                "catalogue": {"domain": "TEST", "rsin": "000000000"},
                                "case_type_identification": "ZT-001",
                                "document_type_description": (
                                    "Attachment Informatieobjecttype"
                                ),
                                "objecttype": (
                                    "http://localhost:8001/api/v2/objecttypes/"
                                    "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48"
                                ),
                                "objecttype_version": 1,
                            },
                        },
                        {
                            "key": "test2",
                            "name": "test2",
                            "backend": "zgw-create-zaak",
                            "options": {
                                "zgw_api_group": api_group.pk,
                                "catalogue": {"domain": "TEST", "rsin": "000000000"},
                                "case_type_identification": "ZT-001",
                                "document_type_description": (
                                    "Attachment Informatieobjecttype"
                                ),
                                "objects_api_group": objects_api_group_2.identifier,
                                "objecttype": (
                                    "http://localhost:8001/api/v2/objecttypes/"
                                    "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48"
                                ),
                                "objecttype_version": 1,
                            },
                        },
                    ],
                }
            ],
            form_definitions=[],
            form_steps=[],
            form_variables=[],
            form_logic=[],
        )

        form = import_form_data(artifact, import_options=FormImportOptions())

        assert form is not None

        with self.subTest("resolves default api group"):
            backend = form.registration_backends.get(key="test")
            self.assertEqual(
                backend.options["objects_api_group"], objects_api_group.identifier
            )

        with self.subTest("does not touch explicitly set api group"):
            backend = form.registration_backends.get(key="test2")
            self.assertEqual(
                backend.options["objects_api_group"], objects_api_group_2.identifier
            )

        with (
            self.subTest("raises validation error when no group exists"),
            self.assertRaises(ValidationError) as exc_context,
        ):
            ObjectsAPIGroupConfig.objects.all().delete()

            import_form_data(artifact, import_options=FormImportOptions())

            objects_error = exc_context.exception.detail["registration_backends"][0][  # pyright: ignore
                "options"
            ]["objects_api_group"][0]
            assert isinstance(objects_error, ErrorDetail)
            self.assertEqual(objects_error.code, "required")

    def test_import_form_with_legacy_file_registration_options(self):
        group = ZGWApiGroupConfigFactory.create(for_test_docker_compose=True)
        opts: RegistrationOptions = {
            "zgw_api_group": group,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "case_type_identification": "ZT-001",
            "document_type_description": "PDF Informatieobjecttype",
            "organisatie_rsin": "000000000",
            "objects_api_group": None,
            "product_url": "",
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
            "summary_documents": [],
        }
        artifact = Artifact(
            forms=[
                {
                    "name": "Test form",
                    "slug": "my-slug",
                    "registration_backends": [
                        {
                            "key": "zgw1",
                            "name": "zgw1",
                            "backend": "zgw-create-zaak",
                            "options": ZaakOptionsSerializer(instance=opts).data,
                        },
                        {
                            "key": "zgw2",
                            "name": "zgw2",
                            "backend": "zgw-create-zaak",
                            "options": {
                                **ZaakOptionsSerializer(instance=opts).data,
                                "files": [],
                            },
                        },
                    ],
                }
            ],
            form_definitions=[
                {
                    "uuid": "63067a59-ace8-42ca-b04a-4f0c14c583c3",
                    "name": "Test",
                    "slug": "fd-1",
                    "configuration": {
                        "components": [
                            {
                                "type": "file",
                                "key": "toplevel.file1",
                                "label": "Top level file",
                                "file": {"type": []},
                                "filePattern": "",
                                "registration": {
                                    "bronorganisatie": "100000009",
                                    "docVertrouwelijkheidaanduiding": "geheim",
                                    "titel": "Custom title",
                                    "documentType": {
                                        "catalogue": {
                                            "domain": "TEST",
                                            "rsin": "000000000",
                                        },
                                        "description": "PDF Informatieobjecttype",
                                    },
                                },
                            },
                            {
                                "type": "editgrid",
                                "key": "editgrid",
                                "label": "Repeating group",
                                "groupLabel": "Item",
                                "components": [
                                    {
                                        "type": "file",
                                        "key": "editgridFile",
                                        "label": "Editgrid file",
                                        "file": {"type": []},
                                        "filePattern": "",
                                        "registration": {
                                            "bronorganisatie": "100000009",
                                            "titel": "Another title",
                                        },
                                    }
                                ],
                            },
                        ]
                    },
                }
            ],
            form_steps=[
                {
                    "uuid": "1e9ee006-cc5e-45e1-ab65-17f7fac5ce10",
                    "index": 0,
                    "slug": "step-1",
                    "form_definition": (
                        "http://testserver/api/v2/form-definitions/"
                        "63067a59-ace8-42ca-b04a-4f0c14c583c3"
                    ),
                }
            ],
            form_variables=[],
            form_logic=[],
        )

        form = import_form_data(artifact, import_options=FormImportOptions())

        assert form is not None
        options = {
            str(backend.key): backend.options
            for backend in form.registration_backends.all()
        }
        assert len(options) == 2
        with self.subTest("backend without file options gets them added"):
            backend_without_initial_files = options["zgw1"]
            file_options = {
                opts["key"]: opts for opts in backend_without_initial_files["files"]
            }
            self.assertEqual(
                file_options,
                {
                    "toplevel.file1": {
                        "key": "toplevel.file1",
                        "document_type_description": "PDF Informatieobjecttype",
                        "organization_rsin": "100000009",
                        "confidentiality_level": "geheim",
                        "title": "Custom title",
                    },
                    "editgridFile": {
                        "key": "editgridFile",
                        "organization_rsin": "100000009",
                        "title": "Another title",
                    },
                },
            )

        with self.subTest("backend with file options is untouched"):
            backend_with_initial_files = options["zgw2"]
            self.assertEqual(len(backend_with_initial_files["files"]), 0)
