from openforms.authentication.contrib.digid_eherkenning_oidc.plugin import (
    get_config_to_plugin as digid_eherkenning_config_to_plugin,
)
from openforms.authentication.contrib.yivi_oidc.plugin import YiviOIDCAuthentication
from openforms.authentication.registry import register


def get_config_to_plugin() -> dict:
    """
    Get the mapping of config class to plugin identifier from the registry.
    """
    digid_eherkenning_plugin_map = digid_eherkenning_config_to_plugin()
    return {
        plugin.config_class: plugin
        for plugin in register
        if isinstance(plugin, YiviOIDCAuthentication)
    } | digid_eherkenning_plugin_map
