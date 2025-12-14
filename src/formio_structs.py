"""
Collection of struct definitions that describe the properties of supported formio
component types.
"""

from __future__ import annotations

from collections.abc import Sequence
from pprint import pprint

import msgspec

from formio_types import AnyComponent

if __name__ == "__main__":
    comp_def = {
        "id": "so-random",
        "type": "textfield",
        "key": "text.key",
        "label": "A text field!",
        "multiple": True,
        "defaultValue": ["first", "second"],
        "errors": {
            "required": "Custom message!",
        },
    }
    content_def = {
        "type": "content",
        "key": "content",
        "label": "",
        "html": "<p>Hello world</p>",
    }

    converted = msgspec.convert([comp_def, content_def], type=Sequence[AnyComponent])

    pprint(converted)
