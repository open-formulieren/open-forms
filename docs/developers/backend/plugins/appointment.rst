.. _developers_backend_plugins_appointment:

===========
Appointment
===========

One of the available form types in Open Forms is the *appointment* form type. These
forms have a fixed flow through the form and require an integration with an appointment
service provider.

The appointments module provides the available product lookups and creation or
cancellation of appointments.

.. contents::
   :local:
   :depth: 2
   :backlinks: none

Python API
==========

Module interface
----------------

The module-level API serves as an abstraction over the various plugins.

.. automodule:: openforms.appointments.service
   :members:

Plugin interface
----------------

.. autoclass:: openforms.appointments.base.BasePlugin
   :members:
