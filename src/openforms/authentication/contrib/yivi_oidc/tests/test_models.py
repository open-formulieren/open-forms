from django.test import SimpleTestCase

from ..models import AttributeGroup


class AttributeGroupTests(SimpleTestCase):
    def test_model_str_for_unsaved_instance(self):
        instance = AttributeGroup()

        result = str(instance)

        self.assertIsInstance(result, str)
