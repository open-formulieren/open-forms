REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        # TODO: left this in here to not break stuff during hackathon
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "djangorestframework_camel_case.render.CamelCaseJSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "djangorestframework_camel_case.parser.CamelCaseJSONParser",
        "djangorestframework_camel_case.parser.CamelCaseFormParser",
        "djangorestframework_camel_case.parser.CamelCaseMultiPartParser",
    ],
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {"anon": "200/day", "user": "1000/day"},
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
    "DEFAULT_SCHEMA_CLASS": "openforms.api.schema.AutoSchema",
}

#
# SPECTACULAR - OpenAPI schema generation
#

_DESCRIPTION = """
Open Forms provides an API to manage multi-page or multi-step forms.

It supports listing and retrieving forms, which are made up of form steps. Each form
step has a form definition driven by [FormIO.js](https://github.com/formio/formio.js/)
definitions.

Submissions of forms are supported, where each form step can be submitted individually.
Complete submissions are sent to the configured backend, which is a pluggable system
to hook into [Open Zaak](https://openzaak.org), [Camunda](https://camunda.com/) or
other systems.

Open Forms fits in the [Common Ground](https://commonground.nl) vision and architecture,
and it plays nice with other available components.
"""

SPECTACULAR_SETTINGS = {
    "SCHEMA_PATH_PREFIX": r"/api/v1",
    "TITLE": "Open Forms API",
    "DESCRIPTION": _DESCRIPTION,
    "POSTPROCESSING_HOOKS": [
        "drf_spectacular.hooks.postprocess_schema_enums",
        "drf_spectacular.contrib.djangorestframework_camel_case.camelize_serializer_fields",
    ],
    "TOS": None,
    # Optional: MAY contain "name", "url", "email"
    "CONTACT": {
        "url": "https://github.com/maykinmedia/open-forms",
        "email": "support@maykinmedia.nl",
    },
    # Optional: MUST contain "name", MAY contain URL
    "LICENSE": {
        "name": "UNLICENSED",
    },
    "VERSION": "1.0.0-alpha",
    # Tags defined in the global scope
    "TAGS": [],
    # Optional: MUST contain 'url', may contain "description"
    "EXTERNAL_DOCS": {
        "description": "Functional and technical documentation",
        "url": "https://open-forms.readthedocs.io/",
    },
}
