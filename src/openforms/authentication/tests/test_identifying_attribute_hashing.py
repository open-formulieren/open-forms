from unittest.mock import patch

from django.test import TestCase

from ..constants import ActingSubjectIdentifierType, LegalSubjectIdentifierType
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


class HashIdentifyingAttributesTests(TestCase):
    def test_hashing_extra_identifying_attributes(self):
        input_attributes = {
            "value": "123456789",
            "acting_subject_identifier_value": "some-opaque-identifier",
            "legal_subject_identifier_value": "12345678",
            "additional_claims": {"attribute_name": "some value"},
        }

        auth_info = AuthInfoFactory.create(
            acting_subject_identifier_type=ActingSubjectIdentifierType.opaque,
            legal_subject_identifier_type=LegalSubjectIdentifierType.kvk,
            mandate_context={},
            **input_attributes,
        )
        # sanity check
        for attr, value in input_attributes.items():
            assert getattr(auth_info, attr) == value

        auth_info.hash_identifying_attributes()

        auth_info.refresh_from_db()
        for attr, old_value in input_attributes.items():
            with self.subTest(attribute=attr):
                hashed_value = getattr(auth_info, attr)
                self.assertGreater(len(hashed_value), 0)
                self.assertNotEqual(hashed_value, old_value)

    def test_hashing_minimal_information(self):
        auth_info = AuthInfoFactory.create(value="123456789")
        assert not auth_info.acting_subject_identifier_value
        assert not auth_info.legal_subject_identifier_value

        auth_info.hash_identifying_attributes()

        auth_info.refresh_from_db()

        assert auth_info.value
        self.assertNotEqual(auth_info.value, "123456789")
