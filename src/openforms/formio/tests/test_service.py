from django.test import RequestFactory, TestCase
from django.urls import reverse

from openforms.formio.service import update_configuration_for_request


class ServiceTestCase(TestCase):
    def test_update_configuration_for_request(self):
        request = RequestFactory().get("/")

        configuration = {
            "display": "form",
            "components": [
                {
                    "id": "e1a2cv9",
                    "key": "my_file",
                    "type": "file",
                    "url": "bad",
                },
            ],
        }
        update_configuration_for_request(configuration, request)

        url = request.build_absolute_uri(reverse("api:formio:temporary-file-upload"))
        self.assertEqual(configuration["components"][0]["url"], url)
