from typing import TypedDict

from .models import OFOpenIDConnectConfig
from ...base import BasePlugin
from ...registry import register


class Options(TypedDict):
    pass


class OFOIDCPlugin[OptionsT: Options](BasePlugin[OptionsT]):
    config_class: OFOpenIDConnectConfig
    pass


def get_config_to_plugin() -> dict[OFOpenIDConnectConfig, OFOIDCPlugin]:
    """
    Get the mapping of config class to plugin identifier from the registry.
    """
    return {
        plugin.config_class: plugin
        for plugin in register
        if isinstance(plugin, OFOIDCPlugin)
    }
