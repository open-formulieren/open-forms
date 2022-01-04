from djangorestframework_camel_case.render import CamelCaseJSONRenderer

from .drf_camel_case import FormCamelCaseMixin


class FormCamelCaseJSONRenderer(FormCamelCaseMixin, CamelCaseJSONRenderer):
    """
    Renderer for Form resource.

    A camelcase JSON renderer subclass to deal with registration-backend specific keys
    that should not be converted from camelCase to snake_case. Rather than using the
    "global" ``ignore_fields`` option, we defer to the registration backend plugin
    to re-instate the keys that should not have been converted, which allows for
    more context.
    """

    pass
