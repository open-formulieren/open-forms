from uuid import UUID

from django.test import TestCase, tag

from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory
from openforms.registrations.contrib.objects_api.config import (
    ObjectsAPIOptionsSerializer,
)
from openforms.registrations.contrib.objects_api.typing import RegistrationOptionsV2
from openforms.utils.tests.vcr import OFVCRMixin

from ...import_export.service import (
    Artifact,
    FormImportOptions,
    import_form_data,
)


class ImportConversionTests(OFVCRMixin, TestCase):
    def test_v1_v2_conversion_adds_missing_variable_mapping(self):
        api_group = ObjectsAPIGroupConfigFactory.create(for_test_docker_compose=True)
        artifact = Artifact(
            forms=[
                {
                    "name": "Test form",
                    "slug": "my-slug",
                    "registration_backends": [
                        # explicit legacy v1 - do not touch
                        {
                            "key": "legacy-v1",
                            "name": "legacy-v1",
                            "backend": "objects_api",
                            "options": {
                                "objects_api_group": api_group.identifier,
                                "version": 1,
                                "objecttype": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                                "objecttype_version": 1,
                            },
                        },
                        # implicit no version -> convert to v2 and add variable mapping
                        {
                            "key": "implicit-v2",
                            "name": "implicit-v2",
                            "backend": "objects_api",
                            "options": {
                                "objects_api_group": api_group.identifier,
                                "objecttype": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                                "objecttype_version": 1,
                            },
                        },
                        # explicit v2 but missing variables mapping
                        {
                            "key": "explicit-v2",
                            "name": "explicit-v2",
                            "backend": "objects_api",
                            "options": {
                                "objects_api_group": api_group.identifier,
                                "version": 2,
                                "objecttype": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                                "objecttype_version": 1,
                            },
                        },
                        # existing variables mapping
                        {
                            "key": "existing-mapping",
                            "name": "existing-mapping",
                            "backend": "objects_api",
                            "options": {
                                "objects_api_group": api_group.identifier,
                                "version": 2,
                                "objecttype": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                                "objecttype_version": 1,
                                "variables_mapping": [
                                    {"variable_key": "data", "options": {}}
                                ],
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
        options = {
            str(backend.key): backend.options
            for backend in form.registration_backends.all()
        }
        assert len(options) == 4

        with self.subTest("explicit v1 untouched"):
            self.assertEqual(
                options["legacy-v1"]["objects_api_group"], api_group.identifier
            )
            self.assertEqual(options["legacy-v1"]["version"], 1)
            self.assertEqual(
                options["legacy-v1"]["objecttype"],
                "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
            )
            self.assertEqual(options["legacy-v1"]["objecttype_version"], 1)

        with self.subTest("implicit v2 made explicit"):
            self.assertEqual(
                options["implicit-v2"]["objects_api_group"], api_group.identifier
            )
            self.assertEqual(options["implicit-v2"]["version"], 2)
            self.assertEqual(
                options["implicit-v2"]["objecttype"],
                "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
            )
            self.assertEqual(options["implicit-v2"]["objecttype_version"], 1)
            self.assertEqual(options["implicit-v2"]["variables_mapping"], [])

        with self.subTest("explicit v2 updated"):
            self.assertEqual(
                options["explicit-v2"]["objects_api_group"], api_group.identifier
            )
            self.assertEqual(options["explicit-v2"]["version"], 2)
            self.assertEqual(
                options["explicit-v2"]["objecttype"],
                "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
            )
            self.assertEqual(options["explicit-v2"]["objecttype_version"], 1)
            self.assertEqual(options["explicit-v2"]["variables_mapping"], [])

        with self.subTest("existing mapping untouched"):
            self.assertEqual(
                options["existing-mapping"]["objects_api_group"], api_group.identifier
            )
            self.assertEqual(options["existing-mapping"]["version"], 2)
            self.assertEqual(
                options["existing-mapping"]["objecttype"],
                "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
            )
            self.assertEqual(options["existing-mapping"]["objecttype_version"], 1)
            self.assertEqual(
                options["existing-mapping"]["variables_mapping"],
                [{"variable_key": "data", "options": {}}],
            )

    @tag("gh-5384")
    def test_object_api_group_pk_references_converted_to_uuid(self):
        api_group = ObjectsAPIGroupConfigFactory.create(for_test_docker_compose=True)
        artifact = Artifact(
            forms=[
                {
                    "name": "Test form",
                    "slug": "my-slug",
                    "registration_backends": [
                        {
                            "key": "test",
                            "name": "test",
                            "backend": "objects_api",
                            "options": {
                                "objects_api_group": api_group.pk,
                                "version": 2,
                                "objecttype": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                                "objecttype_version": 1,
                                "variables_mapping": [],
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
        backend = form.registration_backends.get()
        self.assertEqual(
            backend.options["objects_api_group"], str(api_group.identifier)
        )

    def test_import_form_with_legacy_file_registration_options(self):
        api_group = ObjectsAPIGroupConfigFactory.create(for_test_docker_compose=True)
        opts: RegistrationOptionsV2 = {
            "version": 2,
            "objects_api_group": api_group,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            # See the docker compose fixtures for more info on these values:
            "objecttype": UUID("8faed0fa-7864-4409-aa6d-533a37616a9e"),
            "objecttype_version": 1,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "iot_submission_report": "",
            "iot_submission_csv": "",
            "iot_attachment": "Attachment Informatieobjecttype",
            "variables_mapping": [],
            "transform_to_list": [],
            "use_empty_string_for_empty_datelike_variables": False,
        }
        artifact = Artifact(
            forms=[
                {
                    "name": "Test form",
                    "slug": "my-slug",
                    "registration_backends": [
                        {
                            "key": "objects1",
                            "name": "objects1",
                            "backend": "objects_api",
                            "options": ObjectsAPIOptionsSerializer(instance=opts).data,
                        },
                        {
                            "key": "objects2",
                            "name": "objects2",
                            "backend": "objects_api",
                            "options": {
                                **ObjectsAPIOptionsSerializer(instance=opts).data,
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
                                "type": "file",
                                "key": "toplevel.file2",
                                "label": "Top level file 2",
                                "file": {"type": []},
                                "filePattern": "",
                            },
                            {
                                "type": "file",
                                "key": "toplevel.file3",
                                "label": "Top level file 3",
                                "file": {"type": []},
                                "filePattern": "",
                                "registration": {"titel": ""},
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
            backend_without_initial_files = options["objects1"]
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
            backend_with_initial_files = options["objects2"]
            self.assertEqual(len(backend_with_initial_files["files"]), 0)
