from ..formatters.custom import MapFormatter
from ..registry import BasePlugin, register


@register("map")
class Map(BasePlugin):
    formatter = MapFormatter
