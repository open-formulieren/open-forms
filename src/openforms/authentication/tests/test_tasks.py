from unittest.mock import patch

from django.test import TestCase

from ..tasks import hash_identifying_attributes
from .factories import AuthInfoFactory


class HashIdentifyingAttributesTaskTests(TestCase):
    @patch("openforms.authentication.models.hash_identifying_attributes_task")
    def test_model_method_sync(self, mock_hash_task):
        auth_info = AuthInfoFactory.create()

        auth_info.hash_identifying_attributes()

        mock_hash_task.delay.assert_not_called()
        self.assertTrue(auth_info.attribute_hashed)

    @patch("openforms.authentication.models.hash_identifying_attributes_task")
    def test_model_method_async(self, mock_hash_task):
        auth_info = AuthInfoFactory.create()

        auth_info.hash_identifying_attributes(delay=True)

        mock_hash_task.delay.assert_called_once_with(auth_info.id)
        self.assertFalse(auth_info.attribute_hashed)

    def test_task_function(self):
        auth_info = AuthInfoFactory.create()

        hash_identifying_attributes(auth_info.id)

        auth_info.refresh_from_db()
        self.assertTrue(auth_info.attribute_hashed)
