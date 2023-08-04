from openforms.plugins.registry import BaseRegistry

from .base import BaseStaticVariable


class Registry(BaseRegistry[BaseStaticVariable]):
    """
    A registry for static variables.
    """

    module = "variables"


# Sentinel to provide the default registry. You can easily instantiate another
# :class:`Registry` object to use as dependency injection in tests.
register_static_variable = Registry()
