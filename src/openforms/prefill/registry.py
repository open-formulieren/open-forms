from openforms.plugins.registry import BaseRegistry

from .base import BasePlugin


class Registry(BaseRegistry[BasePlugin]):
    """
    A registry for the prefill module plugins.
    """

    module = "prefill"


# Sentinel to provide the default registry. You an easily instantiate another
# :class:`Registry` object to use as dependency injection in tests.
register = Registry()
