from io import StringIO
from uuid import uuid4

from django.test import TestCase

from upgrade_check import CommandCheck

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
from openforms.registrations.contrib.zgw_apis.options import ZaakOptionsSerializer
from openforms.registrations.contrib.zgw_apis.tests.factories import (
    ZGWApiGroupConfigFactory,
)
from openforms.registrations.contrib.zgw_apis.typing import (
    RegistrationOptions as ZGWRegistrationOptions,
)

check = CommandCheck(
    "check_legacy_catalogi_api_urls",
    options={
        "stdout": StringIO(),
        "stderr": StringIO(),
    },
)


class LegacyCatalogiUsageCheckTests(TestCase):
    def test_ok_when_no_data_in_environment(self):
        result = check.execute()

        self.assertTrue(result)

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

        result = check.execute()

        self.assertTrue(result)

    def test_ok_for_unused_form_definitions_with_legacy_config(self):
        # this doesn't impact runtime because the form definitions aren't used anywhere
        # and rely on form validation to catch these legacy configs if they do get added
        # eventually
        FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "type": "file",
                        "key": "file",
                        "label": "file",
                        "file": {"type": []},
                        "filePattern": "",
                        "registration": {
                            "informatieobjecttype": "https://example.com",
                        },
                    }
                ]
            }
        )

        result = check.execute()

        self.assertTrue(result)

    def test_ok_for_form_with_file_component_with_migrated_config(self):
        FormFactory.create(
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
                                "key": "file",
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
                                    "informatieobjecttype": "https://example.com",
                                },
                            }
                        ],
                    },
                ]
            },
        )

        result = check.execute()

        self.assertTrue(result)

    def test_not_ok_for_form_with_file_component_with_legacy_config(self):
        FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "editgrid",
                        "key": "editgrid",
                        "label": "editgrid",
                        "groupLabel": "Item",
                        "components": [
                            {
                                "type": "file",
                                "key": "file",
                                "label": "file",
                                "file": {"type": []},
                                "filePattern": "",
                                "registration": {
                                    "informatieobjecttype": "https://example.com",
                                },
                            }
                        ],
                    },
                ]
            },
        )

        result = check.execute()

        self.assertFalse(result)

    def test_ok_for_migrated_or_empty_objects_api_groups(self):
        ObjectsAPIGroupConfigFactory.create(
            catalogue_domain="TEST",
            catalogue_rsin="000000000",
            iot_submission_report="PDF",
            iot_submission_csv="CSV",
            iot_attachment="Attachment",
            informatieobjecttype_submission_report="https://example.com",
            informatieobjecttype_submission_csv="https://example.com",
            informatieobjecttype_attachment="https://example.com",
        )
        ObjectsAPIGroupConfigFactory.create(
            catalogue_domain="",
            catalogue_rsin="",
            iot_submission_report="",
            iot_submission_csv="",
            iot_attachment="",
            informatieobjecttype_submission_report="",
            informatieobjecttype_submission_csv="",
            informatieobjecttype_attachment="",
        )

        result = check.execute()

        self.assertTrue(result)

    def test_not_ok_for_unmigrated_objects_api_groups(self):
        ObjectsAPIGroupConfigFactory.create(
            catalogue_domain="",
            catalogue_rsin="",
            iot_submission_report="",
            iot_submission_csv="",
            iot_attachment="",
            informatieobjecttype_submission_report="https://example.com",
            informatieobjecttype_submission_csv="https://example.com",
            informatieobjecttype_attachment="https://example.com",
        )

        result = check.execute()

        self.assertFalse(result)

    def test_not_ok_for_partially_migrated_objects_api_groups(self):
        ObjectsAPIGroupConfigFactory.create(
            catalogue_domain="TEST",
            catalogue_rsin="000000000",
            iot_submission_report="PDF",
            iot_submission_csv="",
            iot_attachment="",
            informatieobjecttype_submission_report="https://example.com",
            informatieobjecttype_submission_csv="https://example.com",
            informatieobjecttype_attachment="https://example.com",
        )

        result = check.execute()

        self.assertFalse(result)

    def test_ok_for_empty_zgw_api_group_or_api_group_with_catalogue(self):
        ZGWApiGroupConfigFactory.create(
            catalogue_domain="",
            catalogue_rsin="",
        )
        ZGWApiGroupConfigFactory.create(
            catalogue_domain="TEST",
            catalogue_rsin="000000000",
        )

        result = check.execute()

        self.assertTrue(result)

    def test_ok_for_migrated_or_empty_objects_api_registration_backends(self):
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
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "iot_submission_report": "PDF",
            "iot_submission_csv": "CSV",
            "iot_attachment": "Attachment",
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
            backend=OBJECTS_PLUGIN_IDENTIFIER,
            options=ObjectsAPIOptionsSerializer(instance=objects_options_1).data,
        )
        objects_options_2: ObjectsRegistrationOptionsV2 = {
            "informatieobjecttype_submission_report": "",
            "informatieobjecttype_submission_csv": "",
            "informatieobjecttype_attachment": "",
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
            backend=OBJECTS_PLUGIN_IDENTIFIER,
            options=ObjectsAPIOptionsSerializer(instance=objects_options_2).data,
        )
        objects_options_3: ObjectsRegistrationOptionsV2 = {
            "informatieobjecttype_submission_report": (
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "7a474713-0833-402a-8441-e467c08ac55b"
            ),
            # may not trip up detection, because a catalogue is specified, you opt
            # into the new behaviour! This effectively means there's no document type
            # configured for CSV and the file will not be created.
            "informatieobjecttype_submission_csv": (
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "b2d83b94-9b9b-4e80-a82f-73ff993c62f3"
            ),
            "informatieobjecttype_attachment": (
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "531f6c1a-97f7-478c-85f0-67d2f23661c7"
            ),
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "iot_submission_report": "PDF",
            "iot_submission_csv": "",
            "iot_attachment": "Attachment",
            "version": 2,
            "objects_api_group": objects_api_group,
            "objecttype": uuid4(),
            "objecttype_version": 3,
            "upload_submission_csv": False,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "organisatie_rsin": "000000000",
            "transform_to_list": [],
            "variables_mapping": [],
        }
        FormRegistrationBackendFactory.create(
            backend=OBJECTS_PLUGIN_IDENTIFIER,
            options=ObjectsAPIOptionsSerializer(instance=objects_options_3).data,
        )

        result = check.execute()

        self.assertTrue(result)

    def test_not_ok_for_partially_or_unmigrated_objects_api_registration_backends(self):
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
            # note the absence of a catalogue here. The 3.5 migration tool will result
            # in it being set on the backend options.
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
            backend=OBJECTS_PLUGIN_IDENTIFIER,
            options=ObjectsAPIOptionsSerializer(instance=objects_options).data,
        )

        result = check.execute()

        self.assertFalse(result)

    def test_not_ok_for_partially_or_unmigrated_objects_api_registration_backends_2(
        self,
    ):
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
            "informatieobjecttype_submission_report": "",
            "informatieobjecttype_submission_csv": (
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "b2d83b94-9b9b-4e80-a82f-73ff993c62f3"
            ),
            "informatieobjecttype_attachment": (
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "531f6c1a-97f7-478c-85f0-67d2f23661c7"
            ),
            # note the absence of a catalogue here. The 3.5 migration tool will result
            # in it being set on the backend options.
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
            backend=OBJECTS_PLUGIN_IDENTIFIER,
            options=ObjectsAPIOptionsSerializer(instance=objects_options).data,
        )

        result = check.execute()

        self.assertFalse(result)

    def test_not_ok_for_partially_or_unmigrated_objects_api_registration_backends_3(
        self,
    ):
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
            "informatieobjecttype_submission_report": "",
            "informatieobjecttype_submission_csv": "",
            "informatieobjecttype_attachment": (
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "531f6c1a-97f7-478c-85f0-67d2f23661c7"
            ),
            # note the absence of a catalogue here. The 3.5 migration tool will result
            # in it being set on the backend options.
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
            backend=OBJECTS_PLUGIN_IDENTIFIER,
            options=ObjectsAPIOptionsSerializer(instance=objects_options).data,
        )

        result = check.execute()

        self.assertFalse(result)

    def test_ok_for_migrated_registration_backends(self):
        api_group = ZGWApiGroupConfigFactory.create(
            catalogue_domain="", catalogue_rsin=""
        )
        zgw_options_1: ZGWRegistrationOptions = {
            "zgw_api_group": api_group,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "case_type_identification": "ZT-001",
            "document_type_description": "Attachment",
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
        }
        FormRegistrationBackendFactory.create(
            backend="zgw-create-zaak",
            options=ZaakOptionsSerializer(instance=zgw_options_1).data,
        )

        result = check.execute()

        self.assertTrue(result)

    def test_not_ok_for_partially_or_unmigrated_zgw_registration_backends(self):
        api_group = ZGWApiGroupConfigFactory.create(
            catalogue_domain="", catalogue_rsin=""
        )
        zgw_options_1: ZGWRegistrationOptions = {
            "zgw_api_group": api_group,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "case_type_identification": "ZT-001",
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
        }
        FormRegistrationBackendFactory.create(
            backend="zgw-create-zaak",
            options=ZaakOptionsSerializer(instance=zgw_options_1).data,
        )

        result = check.execute()

        self.assertFalse(result)

    def test_not_ok_for_partially_or_unmigrated_zgw_registration_backends_2(self):
        api_group = ZGWApiGroupConfigFactory.create(
            catalogue_domain="", catalogue_rsin=""
        )
        zgw_options_1: ZGWRegistrationOptions = {
            "zgw_api_group": api_group,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
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
        }
        FormRegistrationBackendFactory.create(
            backend="zgw-create-zaak",
            options=ZaakOptionsSerializer(instance=zgw_options_1).data,
        )

        result = check.execute()

        self.assertFalse(result)
