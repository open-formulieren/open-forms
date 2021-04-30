import inspect
from dataclasses import dataclass
from typing import Dict, Optional, Type

from rest_framework import serializers

from .constants import UNIQUE_ID_MAX_LENGTH

SerializerCls = Type[serializers.Serializer]


@dataclass
class RegisteredPlugin:
    unique_identifier: str
    """
    The unique identifier to relate database mappings to callbacks.

    Using the Python path usually works, but requires special attention w/r to data
    migrations if code-refactors happen that affect the Python path, such as splitting
    a module into a package with sub-modules.
    """

    callback: callable
    """
    The actual callback that will be invoked from the public Python API.

    Plugins must implement the correct function signature.
    """

    name: str
    """
    A human readable name to easily distinguish between different plugins.
    """

    configuration_options: SerializerCls
    """
    A serializer class describing the plugin-specific configuration options.

    A plugin instance is the combination of a plugin callback and a set of options that
    are plugin specific. Multiple forms can use the same plugin with different
    configuration options. Using a serializer allows us to serialize the options as JSON
    in the database, and de-serialize them into native Python/Django objects when the
    plugin is called.
    """

    backend_feedback_serializer: Optional[SerializerCls] = None
    """
    A serializer class describing the plugin-specific backend feedback data.

    Plugins often interact with other backend systems that send response data. For
    debugging/troubleshooting purposes, this data can be stored as JSON using the
    specified serializer class.
    """


class Registry:
    """
    A registry for registrations module plugins.
    """

    def __init__(self):
        self._registry: Dict[str, RegisteredPlugin] = {}

    def __call__(
        self,
        unique_identifier: str,
        name: str,
        configuration_options: SerializerCls = serializers.Serializer,
        backend_feedback_serializer: Optional[SerializerCls] = None,
    ):
        """
        Provide the decorator syntax to register plugins.

        Note that registration applies some validation to enforce correct public API
        usage, causing code to crash early if you make mistakes as a plugin developer.
        """
        from openforms.submissions.models import Submission

        def decorator(callback: callable):
            sig = inspect.signature(callback)
            if len(sig.parameters) != 2:
                raise TypeError(
                    "A callback must take exactly two arguments - an instance of "
                    "'submissions.Submission' and the options object."
                )

            # check the expected type hint
            param = list(sig.parameters.values())[0]
            if param.annotation is not inspect._empty and not issubclass(
                param.annotation, Submission
            ):
                raise TypeError(
                    f"The '{param.name}' typehint does not appear to be a Submission."
                )

            if len(unique_identifier) > UNIQUE_ID_MAX_LENGTH:
                raise ValueError(
                    f"'unique_identifier' must be {UNIQUE_ID_MAX_LENGTH} or less characters."
                )

            if unique_identifier in self._registry:
                raise ValueError(
                    f"The unique identifier '{unique_identifier}' is already present "
                    "in the registry."
                )

            self._registry[unique_identifier] = RegisteredPlugin(
                unique_identifier=unique_identifier,
                callback=callback,
                name=name,
                configuration_options=configuration_options,
                backend_feedback_serializer=backend_feedback_serializer,
            )

            return callback

        return decorator

    def __iter__(self):
        return iter(self._registry.values())

    def __getitem__(self, key: str):
        return self._registry[key]


# Sentinel to provide the default registry. You an easily instantiate another
# :class:`Registry` object to use as dependency injection in tests.
register = Registry()
