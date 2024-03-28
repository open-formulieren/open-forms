from django.test import SimpleTestCase

from ...typing import ContentComponent
from .helpers import validate_formio_data


class ContentValidationTests(SimpleTestCase):
    def test_content_ignored(self):
        component: ContentComponent = {
            "type": "content",
            "key": "Helaas-5.36",
            "label": "Nope",
            "validate": {"required": False},
            "html": "<p>Nope</p>",
        }

        is_valid, _ = validate_formio_data(component, {})

        self.assertTrue(is_valid)
