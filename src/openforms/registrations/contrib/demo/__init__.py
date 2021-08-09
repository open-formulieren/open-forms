default_app_config = "openforms.registrations.contrib.demo.apps.DemoConfig"

# import the converters to register them
from . import converters  # noqa
from .config import to_jsonschema  # noqa
