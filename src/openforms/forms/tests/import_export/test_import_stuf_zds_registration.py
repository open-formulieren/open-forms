from django.test import TestCase

from openforms.registrations.contrib.stuf_zds.options import ZaakOptionsSerializer
from openforms.registrations.contrib.stuf_zds.typing import RegistrationOptions

from ...import_export.service import (
    Artifact,
    FormImportOptions,
    import_form_data,
)


class ImportConversionTests(TestCase):
    def test_import_form_with_legacy_file_registration_options(self):
        opts: RegistrationOptions = {
            "zds_zaaktype_code": "zt-code",
            "zds_zaaktype_omschrijving": "zt-omschrijving",
            "zds_zaaktype_status_code": "123",
            "zds_zaaktype_status_omschrijving": "aaabbc",
            "zds_documenttype_omschrijving_inzending": "dt-omschrijving",
            "zds_zaakdoc_vertrouwelijkheid": "ZAAKVERTROUWELIJK",
        }
        artifact = Artifact(
            forms=[
                {
                    "name": "Test form",
                    "slug": "my-slug",
                    "registration_backends": [
                        {
                            "key": "stuf-zds1",
                            "name": "stuf-zds1",
                            "backend": "stuf-zds-create-zaak",
                            "options": ZaakOptionsSerializer(instance=opts).data,
                        },
                        {
                            "key": "stuf-zds2",
                            "name": "stuf-zds2",
                            "backend": "stuf-zds-create-zaak",
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
                                "type": "file",
                                "key": "toplevel.file2",
                                "label": "Top level file 2",
                                "file": {"type": []},
                                "filePattern": "",
                                "registration": {
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
            backend_without_initial_files = options["stuf-zds1"]
            file_options = {
                opts["key"]: opts for opts in backend_without_initial_files["files"]
            }
            self.assertEqual(
                file_options,
                {
                    "toplevel.file1": {
                        "key": "toplevel.file1",
                        "title": "Custom title",
                    },
                    "editgridFile": {
                        "key": "editgridFile",
                        "title": "Another title",
                    },
                },
            )

        with self.subTest("backend with file options is untouched"):
            backend_with_initial_files = options["stuf-zds2"]
            self.assertEqual(len(backend_with_initial_files["files"]), 0)
