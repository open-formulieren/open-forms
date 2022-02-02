from django.db import models
from django.test import TestCase

from .models import Model


class WrapperFieldTests(TestCase):
    def test_meta_information_copied(self):
        field = Model._meta.get_field("wysiwyg")

        self.assertEqual(field.verbose_name, "some verbose name")
        self.assertTrue(field.blank)
        self.assertFalse(field.null)
        self.assertEqual(field.model, Model)
        self.assertEqual(field.base_field.model, Model)
        self.assertEqual(field.description, models.TextField.description)

    def test_value_write_and_read(self):

        instance = Model.objects.create(wysiwyg="testdata")

        self.assertEqual(instance.wysiwyg, "testdata")

        instance2 = Model.objects.get(pk=instance.pk)
        self.assertEqual(instance2.wysiwyg, "testdata")
