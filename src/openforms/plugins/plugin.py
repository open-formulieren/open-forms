from typing import List, Tuple

from django.utils.translation import gettext_lazy as _


class AbstractBasePlugin:
    verbose_name = _("Set the 'verbose_name' attribute for a human-readable name")
    """
    Specify the human-readable label for the plugin.
    """

    is_demo_plugin = False

    def __init__(self, identifier: str):
        self.identifier = identifier

    def get_label(self):
        return self.verbose_name

    def check_config(self):
        """
        Validates if this plugin was properly configured. Typically you should
        avoid using any data altering actions.

        Implementations should essentially check 3 things (if applicable and
        possible):

        1. Check the settings (can be deployment variables or database values)
        2. Check connection to external system
        3. Check credentials to external system

        :raises InvalidPluginConfiguration: if plugin was not properly
            configured, this exception is raised.
        """
        raise NotImplementedError()

    def get_config_actions(self) -> List[Tuple[str, str]]:
        """
        Returns a list of tuples containing the label and URL of each action
        that is related to the configuration of this plugin. This can be to
        perform a data altering action that is similar to the plugin's
        behaviour, a configuration page, etc.
        """
        return []
