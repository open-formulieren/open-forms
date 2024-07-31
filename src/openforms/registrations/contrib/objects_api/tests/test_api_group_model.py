from django.db import IntegrityError, transaction
from django.test import TestCase

from .factories import ObjectsAPIGroupConfigFactory


class ObjectsAPIGroupTests(TestCase):

    def test_can_save_without_catalogue_information(self):
        # checks that the check constraints are defined correctly
        instance = ObjectsAPIGroupConfigFactory.create(
            catalogue_domain="",
            catalogue_rsin="",
        )

        self.assertIsNotNone(instance.pk)

    def test_can_save_with_catalogue_information(self):
        # checks that the check constraints are defined correctly
        instance = ObjectsAPIGroupConfigFactory.create(
            catalogue_domain="Test",
            catalogue_rsin="123456782",
        )

        self.assertIsNotNone(instance.pk)

    def test_cannot_save_with_partial_information(self):
        # checks that the check constraints are defined correctly
        with self.assertRaises(IntegrityError), transaction.atomic():
            ObjectsAPIGroupConfigFactory.create(
                catalogue_domain="Test", catalogue_rsin=""
            )

        with self.assertRaises(IntegrityError), transaction.atomic():
            ObjectsAPIGroupConfigFactory.create(
                catalogue_domain="", catalogue_rsin="123456782"
            )
