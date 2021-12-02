from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, List, Optional, Tuple, Type

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.utils.mixins import JsonSchemaSerializerMixin

if TYPE_CHECKING:
    from openforms.submissions.models import Submission

SerializerCls = Type[serializers.Serializer]


class EmptyOptions(JsonSchemaSerializerMixin, serializers.Serializer):
    pass


class BasePlugin(ABC):
    verbose_name = _("Set the 'verbose_name' attribute for a human-readable name")
    """
    Specify the human-readable label for the plugin.
    """
    configuration_options: SerializerCls = EmptyOptions
    """
    A serializer class describing the plugin-specific configuration options.

    A plugin instance is the combination of a plugin callback and a set of options that
    are plugin specific. Multiple forms can use the same plugin with different
    configuration options. Using a serializer allows us to serialize the options as JSON
    in the database, and de-serialize them into native Python/Django objects when the
    plugin is called.
    """

    is_demo_plugin = False

    def __init__(self, identifier: str):
        self.identifier = identifier

    @abstractmethod
    def register_submission(
        self, submission: "Submission", options: dict
    ) -> Optional[dict]:
        raise NotImplementedError()

    @abstractmethod
    def get_reference_from_result(self, result: Any) -> str:
        """
        Extract the public submission reference from the result data.

        This method must return a string to be saved on the submission model.

        :arg result: the raw underlying JSONField datastructure.
        """
        raise NotImplementedError()

    def update_payment_status(self, submission: "Submission", options: dict):
        raise NotImplementedError()

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
