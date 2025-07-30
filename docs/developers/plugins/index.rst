.. _plugins_index:

=======
Plugins
=======

Open Forms has a plugin system for the several modules. Each module has a
specific goal and is invoked in different stages of the form process. Typically,
a plugin uses some backend to communicate with an external system to perform
some task.

Developing plugins
==================

Plugins for each component are developed in roughly the same way but uses a
different base class that belongs to that particular component.

Registering a plugin within a component makes it available for form editors to
use in their forms.

.. _adding_your_plugin:

Adding your plugin
------------------

Plugins are implemented as Django apps (which are essentially Python packages).
Typically you can look at a demo plugin for each component in
``openforms.<component>.contrib.demo`` which acts as an example.

1. Create the python package in ``openforms.<component>.contrib.<vendor>``
2. Ensure you have an AppConfig_ defined in this package, e.g.:

   .. code-block:: python

      # openforms.<component>.contrib.<vendor>.apps.py

       class MyPlugin(AppConfig):
           name = "openforms.<component>.contrib.<vendor>"
           verbose_name = "My <vendor> plugin"

           def ready(self):
               from . import plugin  # noqa

   It's important to import the plugin as part of the ``ready`` hook of the
   ``AppConfig``, as this ensures that the plugin is added to the registry.

3. Add the application to ``settings.INSTALLED_APPS``, this will cause the
   ``AppConfig`` to be loaded.

.. _AppConfig: https://docs.djangoproject.com/en/2.2/ref/applications/


Available plugin components
===========================

.. toctree::
   :maxdepth: 1

   registration_plugins
   prefill_plugins
   appointment_plugins
   payment/index
   authentication_plugins


