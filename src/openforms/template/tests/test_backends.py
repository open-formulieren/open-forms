from django.template import TemplateSyntaxError
from django.test import SimpleTestCase

from .. import render_from_string, sandbox_backend


def sandbox_render(tpl: str, context=None) -> str:
    return render_from_string(tpl, context=context or {}, backend=sandbox_backend)


class SandboxBackendTests(SimpleTestCase):
    def test_loading_template_libraries_forbidden(self):
        template = "{% load appointments %}"

        with self.assertRaises(TemplateSyntaxError):
            sandbox_render(template)

    def test_simple_template_ok(self):
        template = "{{ foo }} bar"

        result = sandbox_render(template, {"foo": "baz"})

        self.assertEqual(result, "baz bar")
