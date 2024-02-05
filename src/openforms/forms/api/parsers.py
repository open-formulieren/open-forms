from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer

from .drf_camel_case import FormCamelCaseMixin


class IgnoreConfigurationFieldCamelCaseJSONParser(CamelCaseJSONParser):
    # This is SUPER important - when using the API to manage forms, form steps and form
    # definitions, the `configuration` field we post back is a JSONField holding the
    # formio.js definitions, which are camelCase because it's raw JSON.
    # If you don't do this (see #449), you end up with both
    # `defaultValue` and `default_value` keys for a component, where the snake_case
    # variant can sometimes overwrite the camelCase variant, which breaks the pre-fill
    # functionality. This can happen because JSON objects DO NOT HAVE inherent ordering
    # and the spec is non-deterministic.
    json_underscoreize = {"ignore_fields": ("configuration", "component_translations")}


class FormVariableJSONParser(CamelCaseJSONParser):
    json_underscoreize = {
        "ignore_fields": (
            "body",
            "headers",
            "mapping_expression",
            "query_params",
        )
    }


class FormVariableJSONRenderer(CamelCaseJSONRenderer):
    json_underscoreize = {
        "ignore_fields": (
            "body",
            "headers",
            "mapping_expression",
            "query_params",
        )
    }


class IgnoreConfigurationFieldCamelCaseJSONRenderer(CamelCaseJSONRenderer):
    # This is needed for fields in the JSON configuration that have an underscore
    # For example: time_24hr in the date component. See github issue
    # https://github.com/open-formulieren/open-forms/issues/1255
    json_underscoreize = {"ignore_fields": ("configuration", "component_translations")}


class FormLogicRuleJSONParser(CamelCaseJSONParser):
    # In the config field of the DMN Evaluate logic action, the mapping of the form variables to the DMN variables should
    # not be changed by the parser
    json_underscoreize = {"ignore_fields": ("input_mapping", "output_mapping")}


class FormLogicRuleJSONRenderer(CamelCaseJSONRenderer):
    json_underscoreize = {"ignore_fields": ("input_mapping", "output_mapping")}


class FormCamelCaseJSONParser(FormCamelCaseMixin, CamelCaseJSONParser):
    """
    Parser for Form resource.

    A camelcase JSON parser subclass to deal with registration-backend specific keys
    that should not be converted from camelCase to snake_case. Rather than using the
    "global" ``ignore_fields`` option, we defer to the registration backend plugin
    to re-instate the keys that should not have been converted, which allows for
    more context.
    """

    pass
