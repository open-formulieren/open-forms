from django.utils.translation import gettext_lazy as _

from drf_spectacular.plumbing import build_basic_type, build_object_type

STR_TYPE = build_basic_type(str)
assert STR_TYPE is not None
BOOL_TYPE = build_basic_type(bool)
assert BOOL_TYPE is not None

STATEMENT_CHECKBOX_SCHEMA = build_object_type(
    title=_("Statement checkbox"),
    description=_(  # pyright: ignore[reportArgumentType]
        "A single Form.io checkbox component for the statements that a user may "
        "have to accept before submitting a form."
    ),
    properties={
        "type": {
            **STR_TYPE,
            "description": _("Component type (checkbox)"),
        },
        "key": {
            **STR_TYPE,
            "description": _("Key of the statement field"),
        },
        "label": {
            **STR_TYPE,
            "description": _("Text of the statement"),
        },
        "validate": build_object_type(
            properties={
                "required": {
                    **BOOL_TYPE,
                    "description": _(
                        "Whether accepting this statement is required or not."
                    ),
                }
            }
        ),
    },
)
