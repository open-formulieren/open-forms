from ...registry import register
from ..digid_eherkenning_oidc.plugin import (
    get_config_to_plugin as digid_eherkenning_config_to_plugin,
)
from ..yivi_oidc.constants import PLUGIN_ID


def get_config_to_plugin() -> dict:
    """
    Get the mapping of config class to plugin identifier from the registry.
    """
    digid_eherkenning_plugin_map = digid_eherkenning_config_to_plugin()
    yivi_plugin = register[PLUGIN_ID]
    return {yivi_plugin.config_class: yivi_plugin} | digid_eherkenning_plugin_map
