from unittest.mock import patch

from django.test import TestCase

from openforms.registrations.base import BasePlugin
from openforms.registrations.registry import Registry
from openforms.template import render_from_string
from openforms.template.backends.sandboxed_django import get_openforms_backend

register = Registry()


@register("Test")
class TestPlugin(BasePlugin):
    verbose_name = "Test"

    def register_submission(self, submission, options):
        pass

    def get_custom_templatetags_libraries(self) -> list[str]:
        return ["openforms.template.tests.templatetags.a_test_tag"]


class TestLibrariesOptionsBackend(TestCase):
    def test_libraries_contain_custom_libraries(self):
        with patch("openforms.registrations.registry.register", register):
            backend = get_openforms_backend()

        result = render_from_string(
            "{% a_test_tag %}",
            context={},
            backend=backend,
        )

        self.assertEqual("Hello I am a test", result)
