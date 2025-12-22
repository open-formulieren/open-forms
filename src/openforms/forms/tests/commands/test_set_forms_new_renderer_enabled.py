from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from ...models import Form
from ..factories import FormFactory


class CommandTests(TestCase):
    def test_command_enable(self):
        FormFactory.create(new_renderer_enabled=True)
        FormFactory.create_batch(2, new_renderer_enabled=False)

        stdout = StringIO()

        call_command("set_forms_new_renderer_enabled", state="enabled", stdout=stdout)

        self.assertFalse(Form.objects.filter(new_renderer_enabled=False).exists())

        output = stdout.getvalue().strip()
        self.assertEqual(output, "New renderer has been enabled for 2 form(s).")

    def test_command_disable(self):
        FormFactory.create(new_renderer_enabled=True)
        FormFactory.create(new_renderer_enabled=False)

        stdout = StringIO()

        call_command("set_forms_new_renderer_enabled", state="disabled", stdout=stdout)

        self.assertFalse(Form.objects.filter(new_renderer_enabled=True).exists())

        output = stdout.getvalue().strip()
        self.assertEqual(output, "New renderer has been disabled for 1 form(s).")
