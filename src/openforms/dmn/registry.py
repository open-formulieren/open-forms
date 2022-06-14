from openforms.plugins.registry import BaseRegistry


class Registry(BaseRegistry):
    """
    A registry for decision modelling/evaluation module plugins.
    """

    module = "dmn"


# Sentinel to provide the default registry. You an easily instantiate another
# :class:`Registry` object to use as dependency injection in tests.
register = Registry()
