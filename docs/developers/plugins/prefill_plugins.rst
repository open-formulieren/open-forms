.. _developers_prefill_plugins:

===============
Prefill plugins
===============

Open Forms has a plugin system for the prefill module. The prefill module is invoked
when form step (or rather, submission steps) are retrieved from the API to obtain the
FormioJS configuration. In the form builder, it's possible to specify which plugin and
plugin-specific attribute to use to prefill the default value.

Each plugin is responsible for fetching the relevant data from the plugin-specific
backend, which could be StUF-BG, HaalCentraal BRP or Chamber of Commerce for example.

Developing plugins
==================

Every possible backend can be implemented as a plugin, and registered with Open Forms.

Registering the plugin makes it available for content-editors to select as possible
prefill option for a form field.

You can find an example implementation in :mod:`openforms.prefill.contrib.demo`.

Implementation
--------------

Plugins must implement the interface from :class:`openforms.prefill.base.BasePlugin`.
It's safe to use this as a base class.

There are two relevant public methods:

``get_available_attributes``
    provide an iterable of ``(identifier, label)`` tuples. This is used to pre-populate/
    display the list of attributes that can be selected by content-editors.
``get_prefill_values``
    the actual implementation of the prefill functionality. This is invoked inside the
    request-response cycle of certain API endpoints.

Public Python API
=================

**Plugin base class**

.. autoclass:: openforms.prefill.base.BasePlugin
   :members:

**Module documentation**

.. automodule:: openforms.prefill
   :members:
