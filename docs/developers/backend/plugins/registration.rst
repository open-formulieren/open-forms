.. _developers_backend_plugins_registration:

============
Registration
============

The registrations module is invoked when a form submission is completed, and is
responsible for persisting the form data to a configured backend. It's arguably the
most important step in the process, as this is where Open Forms does the handover to
another system to process the customer request.

.. contents::
   :local:
   :depth: 2
   :backlinks: none

Python API
==========

Module interface
----------------

The module-level API serves as an abstraction over the various plugins.

.. automodule:: openforms.registrations.service
   :members:

Plugin interface
----------------

Registrations plugins must inherit from the base plugin.

**Plugin base API**

.. automodule:: openforms.registrations.base
   :members:

Registration failure
--------------------

If the registration fails for whatever reason, then your plugin should raise
:class:`openforms.registrations.exceptions.RegistrationFailed`. This will mark the
submission with a failed state, making it possible to handle these failures.

The submission handler extracts the traceback, so you should ideally raise this exception
from the root exception to include the full traceback:

.. code-block:: python

    try:
        ...  # do plugin stuff
    except Exception as exc:
        raise RegistrationFailed from exc
