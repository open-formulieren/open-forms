from typing import Any, Dict

from openforms.plugins.registry import BaseRegistry


class Registry(BaseRegistry):
    """
    A registry for the FormIO formatters.
    """

    def format(self, info: Dict, value: Any, multiple: bool = False):
        formatter = (
            register[info["type"]] if info["type"] in register else register["default"]
        )
        return formatter(info, value, multiple=multiple)


# Sentinel to provide the default registry. You an easily instantiate another
# :class:`Registry` object to use as dependency injection in tests.
register = Registry()
