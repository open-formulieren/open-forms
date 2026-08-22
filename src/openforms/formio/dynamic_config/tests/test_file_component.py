from unittest.mock import patch

from django.test import TestCase, override_settings, tag

from rest_framework.test import APIRequestFactory

from formio_types import File
from openforms.config.models import GlobalConfiguration

from ...datastructures import FormioConfig
from ...service import rewrite_formio_components_for_request
from ...typing import FileComponent

request_factory = APIRequestFactory()


def _get_dynamic_config(component: FileComponent) -> FormioConfig:
    wrapper = FormioConfig(name="<test>", components=[component])
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
        component: FileComponent = {
            "type": "file",
            "key": "fileTest",
            "label": "fileTest",
            "url": "",
            "useConfigFiletypes": True,
            "filePattern": "*",
            "file": {"type": [], "allowedTypesLabels": []},
        }

        config = _get_dynamic_config(component)

        updated_component = config["fileTest"]
        assert isinstance(updated_component, File)
        self.assertEqual(updated_component.file_pattern, "image/png,application/pdf")
        self.assertEqual(updated_component.file.allowed_types_labels, [".png", ".pdf"])

    @patch(
        "openforms.formio.components.vanilla.GlobalConfiguration.get_solo",
        return_value=GlobalConfiguration(form_upload_default_file_types=["*"]),
    )
    @override_settings(LANGUAGE_CODE="en")
    def test_use_global_config_filetypes_all_allowed(self, m_get_solo):
        component: FileComponent = {
            "type": "file",
            "key": "fileTest",
            "label": "fileTest",
            "url": "",
            "useConfigFiletypes": True,
            "filePattern": "*",
            "file": {"type": [], "allowedTypesLabels": []},
        }

        config = _get_dynamic_config(component)

        updated_component = config["fileTest"]
        assert isinstance(updated_component, File)
        self.assertEqual(updated_component.file_pattern, "*")
        self.assertEqual(updated_component.file.allowed_types_labels, ["any filetype"])

    @tag("gh-6698")
    def test_allowed_types_labels_are_always_injected(self):
        component: FileComponent = {  # pyright: ignore[reportAssignmentType]
            "type": "file",
            "key": "fileTest",
            "label": "fileTest",
            "url": "",
            "useConfigFiletypes": False,
            "filePattern": "*",
            "file": {"type": ["image/png"]},
        }

        config = _get_dynamic_config(component)

        updated_component = config["fileTest"]
        assert isinstance(updated_component, File)
        self.assertEqual(updated_component.file.allowed_types_labels, [".png"])
