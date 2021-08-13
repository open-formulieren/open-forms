from typing import TYPE_CHECKING

from openforms.plugins.registry import BaseRegistry

if TYPE_CHECKING:
    from openforms.submissions.models import Submission


class Registry(BaseRegistry):
    """
    A registry for registrations module plugins.
    """

    def check_plugin(self, plugin):
        if not plugin.configuration_options:
            raise ValueError(
                f"Please specify 'configuration_options' attribute for plugin class."
            )

    def update_payment_status(self, submission: "Submission"):
        # submission.payments.
        pass


# Sentinel to provide the default registry. You an easily instantiate another
# :class:`Registry` object to use as dependency injection in tests.
register = Registry()
