from django.test import SimpleTestCase, tag

from openforms.typing import JSONObject

from ...typing import RadioComponent
from .helpers import validate_formio_data


class RadioValidationTests(SimpleTestCase):

    @tag("gh-4096")
    def test_radio_hidden_required(self):
        component: RadioComponent = {
            "type": "radio",
            "key": "radio",
            "label": "Radio",
            "values": [
                {"label": "Opt1", "value": "opt1"},
                {"label": "Opt2", "value": "opt2"},
            ],
            "hidden": True,
            "validate": {
                "required": True,
            },
        }

        # This happens when `clearOnHide` is `False`:
        data: JSONObject = {"radio": ""}

        is_valid, _ = validate_formio_data(component, data)
        self.assertTrue(is_valid)
