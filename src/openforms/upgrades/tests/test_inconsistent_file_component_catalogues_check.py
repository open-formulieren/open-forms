from uuid import uuid4

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
from openforms.registrations.contrib.zgw_apis.options import ZaakOptionsSerializer
from openforms.registrations.contrib.zgw_apis.plugin import (
    PLUGIN_IDENTIFIER as ZGW_PLUGIN_IDENTIFIER,
)
from openforms.registrations.contrib.zgw_apis.tests.factories import (
    ZGWApiGroupConfigFactory,
)
from openforms.registrations.contrib.zgw_apis.typing import (
    RegistrationOptions as ZGWRegistrationOptions,
)

from ..script_checks import BinScriptCheck
from .utils import capture_output

check = BinScriptCheck("report_file_component_inconsistent_catalogues")


class InconsistentFileComponentCatalogueCheckTests(TestCase):
    def test_ok_when_no_data_in_environment(self):
        with capture_output() as outfile:
            result = check.execute()

        self.assertTrue(result)
        self.assertIn("No inconsistencies found.", outfile.getvalue())

    def test_ok_for_forms_defs_without_file_components(self):
        FormFactory.create(
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

        with capture_output() as outfile:
            result = check.execute()

        self.assertTrue(result)
        self.assertIn("No inconsistencies found.", outfile.getvalue())

    def test_reports_inconsistencies_for_zgw_and_objects_api(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "fieldset",
                        "key": "fieldset",
                        "label": "fieldset",
                        "components": [
                            {
                                "type": "file",
                                "key": "file1",
                                "label": "file",
                                "file": {"type": []},
                                "filePattern": "",
                                "registration": {
                                    "documentType": {
                                        # mismatch
                                        "catalogue": {
                                            "domain": "OTHER",
                                            "rsin": "000000000",
                                        },
                                        "description": "Attachment",
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
                                        "key": "file2",
                                        "label": "file",
                                        "file": {"type": []},
                                        "filePattern": "",
                                        "registration": {
                                            "documentType": {
                                                # mismatch
                                                "catalogue": {
                                                    "domain": "TEST",
                                                    "rsin": "100000009",
                                                },
                                                "description": "Attachment",
                                            },
                                        },
                                    },
                                    {
                                        "type": "file",
                                        "key": "file3",
                                        "label": "file",
                                        "file": {"type": []},
                                        "filePattern": "",
                                        "registration": {
                                            "documentType": {},
                                        },
                                    },
                                    {
                                        "type": "file",
                                        "key": "file4",
                                        "label": "file",
                                        "file": {"type": []},
                                        "filePattern": "",
                                        "registration": {"titel": "Custom title"},
                                    },
                                    {
                                        "type": "file",
                                        "key": "file5",
                                        "label": "file",
                                        "file": {"type": []},
                                        "filePattern": "",
                                    },
                                ],
                            },
                        ],
                    },
                    {
                        "type": "file",
                        "key": "file6",
                        "label": "file",
                        "file": {"type": []},
                        "filePattern": "",
                        "registration": {
                            "documentType": {
                                "catalogue": {
                                    "domain": "TEST",
                                    "rsin": "000000000",
                                },
                                "description": "Attachment",
                            },
                        },
                    },
                ]
            },
        )
        objects_api_group = ObjectsAPIGroupConfigFactory.create(
            catalogue_domain="",
            catalogue_rsin="",
            iot_submission_report="",
            iot_submission_csv="",
            iot_attachment="",
            informatieobjecttype_submission_report="",
            informatieobjecttype_submission_csv="",
            informatieobjecttype_attachment="",
        )
        objects_options: ObjectsRegistrationOptionsV2 = {
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "iot_submission_report": "",
            "iot_submission_csv": "",
            "iot_attachment": "",
            "version": 2,
            "objects_api_group": objects_api_group,
            "objecttype": uuid4(),
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
            backend=OBJECTS_PLUGIN_IDENTIFIER,
            options=ObjectsAPIOptionsSerializer(instance=objects_options).data,
        )
        zgw_api_group = ZGWApiGroupConfigFactory.create(
            catalogue_domain="", catalogue_rsin=""
        )
        zgw_options: ZGWRegistrationOptions = {
            "zgw_api_group": zgw_api_group,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "case_type_identification": "ZT-001",
            "document_type_description": "Attachment",
            "product_url": "",
            "partners_roltype": "",
            "partners_description": "",
            "children_roltype": "",
            "children_description": "",
            "objects_api_group": None,
            "summary_documents": [],
            "zaaktype": "",
            "informatieobjecttype": "",
        }
        FormRegistrationBackendFactory.create(
            form=form,
            backend=ZGW_PLUGIN_IDENTIFIER,
            options=ZaakOptionsSerializer(instance=zgw_options).data,
        )

        with capture_output() as outfile:
            result = check.execute()

        self.assertFalse(result)
        output = outfile.getvalue()
        self.assertIn("file1", output)
        self.assertIn("file2", output)
        self.assertNotIn("file3", output)
        self.assertNotIn("file4", output)
        self.assertNotIn("file5", output)
        self.assertNotIn("file6", output)

        self.assertIn(ZGW_PLUGIN_IDENTIFIER, output)
        self.assertIn(OBJECTS_PLUGIN_IDENTIFIER, output)
