from djangorestframework_camel_case.parser import CamelCaseJSONParser


class IgnoreConfigurationFieldCamelCaseJSONParser(CamelCaseJSONParser):
    # This is SUPER important - when using the API to manage forms, form steps and form
    # definitions, the `configuration` field we post back is a JSONField holding the
    # formio.js definitions, which are camelCase because it's raw JSON.
    # If you don't do this (see #449), you end up with both
    # `defaultValue` and `default_value` keys for a component, where the snake_case
    # variant can sometimes overwrite the camelCase variant, which breaks the pre-fill
    # functionality. This can happen because JSON objects DO NOT HAVE inherent ordering
    # and the spec is non-deterministic.
    json_underscoreize = {"ignore_fields": ("configuration",)}
