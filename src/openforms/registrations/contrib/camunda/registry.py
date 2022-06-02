"""
Camunda registry for custom plugins hooks.

This registry allows users of Open Forms with the Camunda registration backend to
supply their own implementations/handlers for obtaining a reference from the process
instance (and handling a payment update).

These handlers receive the submission instance and a Camunda client object so API
calls can be made to the Camunda instance, e.g. to send a message in the process,
or poll for the availability of a certain variable.
"""
from openforms.plugins.registry import BaseRegistry


class CamundaHandlerRegistry(BaseRegistry):
    module = "registrations:camunda"


# Sentinel to provide the default registry. You an easily instantiate another
# :class:`Registry` object to use as dependency injection in tests.
register = CamundaHandlerRegistry()
