"""
Define some (basic) OpenAPI schema for Form.io components.
"""

from django.utils.translation import gettext_lazy as _

from drf_spectacular.plumbing import build_basic_type, build_object_type

STR_TYPE = build_basic_type(str)
assert STR_TYPE is not None


FORMIO_COMPONENT_SCHEMA = build_object_type(
    title=_("Form.io component"),
    description=_(
        "A single Form.io component. The `type`, `key` and `label` properties "
        "are guaranteed to be present and non-empty."
    ),
    properties={
        "type": {
            **STR_TYPE,
            "description": _("Component type"),
        },
        "key": {
            **STR_TYPE,
            "description": _("Form field name"),
        },
        "label": {
            **STR_TYPE,
            "description": _("Form field label"),
        },
    },
    additionalProperties={},
)
