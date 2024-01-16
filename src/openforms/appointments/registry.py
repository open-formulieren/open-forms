from typing import TYPE_CHECKING

from openforms.plugins.registry import BaseRegistry

if TYPE_CHECKING:
    from .base import BasePlugin  # noqa: F401


class Registry(BaseRegistry["BasePlugin"]):
    """
    A registry for appointments module plugins.
    """

    module = "appointments"


register = Registry()
