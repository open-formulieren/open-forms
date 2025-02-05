from django.test import TestCase

from openforms.appointments.contrib.qmatic.tests.factories import ServiceFactory

from ..config import JSONDumpOptions, JSONDumpOptionsSerializer


class JSONDumpConfigTests(TestCase):
    def test_serializer_raises_validation_error_on_path_traversal(self):
        service = ServiceFactory.create(api_root="https://example.com/api/v2")

        data: JSONDumpOptions = {
            "service": service.pk,
            "path": "",
            "variables": ["now"],
            "fixed_metadata_variables": [],
            "additional_metadata_variables": [],
        }

        # Ensuring that the options are valid in the first place
        serializer = JSONDumpOptionsSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        for path in ("..", "../foo", "foo/..", "foo/../bar"):
            with self.subTest(path):
                data["path"] = path
                serializer = JSONDumpOptionsSerializer(data=data)
                self.assertFalse(serializer.is_valid())
