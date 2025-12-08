"""
Collection of struct definitions that describe the properties of supported formio
component types.
"""

from __future__ import annotations

from collections.abc import Sequence

import msgspec

from formio_types import AnyComponent
from formio_types._base import BaseOpenFormsExtensions
from formio_types.textfield import TextField

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

    print(converted)

    some_textfield = TextField(
        key="typeCheckerGoesBrr",
        label="Type checker validates things!",
        open_forms=BaseOpenFormsExtensions(
            translations={"nl": {"label": "De datatypecontrole valideert dingen!"}}
        ),
        translated_errors={"nl": {"required": "Dit veld is verplicht."}},
    )
