from django.db import IntegrityError
from django.test import TestCase

from ..factories import FormVariableFactory


class FormVariableModelTests(TestCase):
    def test_prefill_plugin_empty_prefill_attribute_filled(self):
        with self.assertRaises(IntegrityError):
            FormVariableFactory.create(prefill_plugin="", prefill_attribute="demo")

    def test_prefill_plugin_filled_prefill_attribute_empty(self):
        with self.assertRaises(IntegrityError):
            FormVariableFactory.create(prefill_plugin="demo", prefill_attribute="")
