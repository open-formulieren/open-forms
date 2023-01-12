from openforms.plugins.registry import BaseRegistry


class Registry(BaseRegistry):
    """
    A registry for appointments module plugins.
    """

    module = "appointments"


register = Registry()
