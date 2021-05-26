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

Registration
------------

Plugins are implemented as Django apps / Python packages. The
``openforms.prefill.contrib.demo`` plugin acts as an example.

1. Create the python package in ``openforms.prefill.contrib.<vendor>``
2. Ensure you have an AppConfig_ defined in this package, e.g.:

   .. code-block:: python

       class MyPlugin(AppConfig):
           name = "openforms.prefill.contrib.<vendor>"
           verbose_name = "My <vendor> plugin"

           def ready(self):
               from . import plugin  # noqa

   It's important to import the plugin as part of the ``ready`` hook of the ``AppConfig``,
   as this ensures that the plugin is added to the registry.

3. Add the application to ``settings.INSTALLED_APPS``, this will cause the ``AppConfig``
   to be loaded.

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

Public python API
=================

**Plugin base class**

.. autoclass:: openforms.prefill.base.BasePlugin
   :members:

**Module documentation**

.. automodule:: openforms.prefill
   :members:

.. _AppConfig: https://docs.djangoproject.com/en/2.2/ref/applications/
