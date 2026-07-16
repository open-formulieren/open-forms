.. _developers_backend_plugins_index:

=========================
Module system and plugins
=========================

Open Forms has a plugin system for the several *modules*. Each module has a
specific goal providing some high-level functionality. Each module is invoked in
different stages of the form (submission) process.

Within each module, one or more plugins are available that implement the low-level
functionality that a module delivers. Often there are plugins for different standards
or they implement necessary vendor-specific details.

Typically, a plugin uses some backend to communicate with an external system to perform
some task.

.. toctree::
    :caption: Modules
    :maxdepth: 1

    authentication
    prefill
    dmn
    payment
    appointment
    registration

.. todo:: Document other modules: ``formio``, ``forms.validation``,
   ``pre_requests``, ``validations`` and ``variables``.

Developing plugins
==================

Plugins for each module are developed in roughly the same way, but they tend to use a
different base class that belongs to that particular module.

Registering a plugin within a module makes it available for form editors to
use in their forms.

.. _adding_your_plugin:

Adding your plugin
------------------

Plugins are implemented as Django apps (which are essentially Python packages).
Typically you can look at a demo plugin for each module in
``openforms.<module>.contrib.demo`` which acts as an example.

1. Create the python package in ``openforms.<module>.contrib.<vendor>``
2. Ensure you have an AppConfig_ defined in this package, e.g.:

   .. code-block:: python

      # openforms.<module>.contrib.<vendor>.apps.py

       class MyPlugin(AppConfig):
           name = "openforms.<module>.contrib.<vendor>"
           verbose_name = "My <vendor> plugin"
           label = "<module>_<vendor>"

           def ready(self):
               from . import plugin  # noqa

   It's important to import the plugin as part of the ``ready`` hook of the
   ``AppConfig``, as this ensures that the plugin is added to the registry.

3. Add the application to ``settings.INSTALLED_APPS``, this will cause the
   ``AppConfig`` to be loaded.

.. _AppConfig: https://docs.djangoproject.com/en/5.2/ref/applications/
