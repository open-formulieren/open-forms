from openforms.plugins.registry import BaseRegistry


class Registry(BaseRegistry):
    """
    A registry for registrations module plugins.
    """

    module = "registrations"

    def check_plugin(self, plugin):
        if not plugin.configuration_options:
            raise ValueError(
                "Please specify 'configuration_options' attribute for plugin class."
            )


# Sentinel to provide the default registry. You an easily instantiate another
# :class:`Registry` object to use as dependency injection in tests.
register = Registry()
