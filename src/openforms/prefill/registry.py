from openforms.plugins.registry import BaseRegistry


class Registry(BaseRegistry):
    """
    A registry for the prefill module plugins.
    """

    pass


# Sentinel to provide the default registry. You an easily instantiate another
# :class:`Registry` object to use as dependency injection in tests.
register = Registry()
