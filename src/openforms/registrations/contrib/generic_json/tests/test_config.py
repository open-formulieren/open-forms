from django.test import TestCase

from openforms.appointments.contrib.qmatic.tests.factories import ServiceFactory

from ..config import GenericJSONOptionsSerializer
from ..typing import GenericJSONOptions


class GenericJSONConfig(TestCase):
    def test_serializer_raises_validation_error_on_path_traversal(self):
        service = ServiceFactory.create(api_root="https://example.com/api/v2")

        data: GenericJSONOptions = {
            "service": service.pk,
            "path": "",
            "variables": ["now"],
            "fixed_metadata_variables": [],
            "additional_metadata_variables": [],
            "transform_to_list": [],
        }

        # Ensuring that the options are valid in the first place
        serializer = GenericJSONOptionsSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        for path in ("..", "../foo", "foo/..", "foo/../bar"):
            with self.subTest(path):
                data["path"] = path
                serializer = GenericJSONOptionsSerializer(data=data)
                self.assertFalse(serializer.is_valid())
