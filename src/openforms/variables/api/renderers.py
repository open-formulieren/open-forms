from djangorestframework_camel_case.render import CamelCaseJSONRenderer


class ServiceFetchConfigurationRenderer(CamelCaseJSONRenderer):
    # The field body and query_params needs to be ignored, to prevent accidental snake_case to camelCase changes.
    # See github issue https://github.com/open-formulieren/open-forms/issues/5089
    json_underscoreize = {
        "ignore_fields": (
            "body",
            "query_params",
        )
    }
