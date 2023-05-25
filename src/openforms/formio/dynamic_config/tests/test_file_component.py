from unittest.mock import patch

from django.test import TestCase, override_settings

from rest_framework.test import APIRequestFactory

from openforms.config.models import GlobalConfiguration

from ...datastructures import FormioConfigurationWrapper
from ...service import rewrite_formio_components_for_request

request_factory = APIRequestFactory()


def _get_dynamic_config(component: dict) -> FormioConfigurationWrapper:
    wrapper = FormioConfigurationWrapper({"components": [component]})
    request = request_factory.get("/irrelevant")
    return rewrite_formio_components_for_request(wrapper, request)


class FileComponentTests(TestCase):
    @patch(
        "openforms.formio.components.vanilla.GlobalConfiguration.get_solo",
        return_value=GlobalConfiguration(
            form_upload_default_file_types=["image/png", "application/pdf"]
        ),
    )
    def test_use_global_config_filetypes(self, m_get_solo):
        component = {
            "type": "file",
            "key": "fileTest",
            "url": "",
            "useConfigFiletypes": True,
            "filePattern": "*",
            "file": {},
        }

        wrapper = _get_dynamic_config(component)

        updated_component = wrapper["fileTest"]
        self.assertEqual(updated_component["filePattern"], "image/png,application/pdf")
        self.assertNotEqual(updated_component["url"], "")
        self.assertEqual(
            updated_component["file"]["allowedTypesLabels"], [".png", ".pdf"]
        )

    @patch(
        "openforms.formio.components.vanilla.GlobalConfiguration.get_solo",
        return_value=GlobalConfiguration(form_upload_default_file_types=["*"]),
    )
    @override_settings(LANGUAGE_CODE="en")
    def test_use_global_config_filetypes_all_allowed(self, m_get_solo):
        component = {
            "type": "file",
            "key": "fileTest",
            "url": "",
            "useConfigFiletypes": True,
            "filePattern": "*",
            "file": {},
        }

        wrapper = _get_dynamic_config(component)

        updated_component = wrapper["fileTest"]
        self.assertEqual(updated_component["filePattern"], "*")
        self.assertEqual(
            updated_component["file"]["allowedTypesLabels"], ["any filetype"]
        )
