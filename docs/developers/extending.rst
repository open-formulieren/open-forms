.. _developers_extending:

=========
Extending
=========

Open Forms ("the backend") is implemented with a pluggable architecture.

Within Open Forms there are modules which focus on specific functionality. In these modules, there are plugins that
implement the required functionality using multiple vendors. At the time of writing, the following modules exist:

* registrations
* authentication
* prefill
* payments
* appointments
* formio formatters
* formio custom types
* validations

Modules and plugins are Python packages with some Django bindings. They are called
by the Open Forms core functionality (forms, submissions...).

We support two ways to add new plugins:

#. Adding new plugins directly in Open Forms. These are extensions that serve the greater community and can be
   contributed as a pull request to Open Forms (more information can be found in the `CONTRIBUTING.md`_.

#. Adding 'external' plugins. This are extensions that are extremely specific or can't be open-sourced. Instructions on how to implement such 'external plugins' are described below.

.. _CONTRIBUTING.md: https://github.com/open-formulieren/open-forms/blob/master/CONTRIBUTING.md

Creating an external plugin
===========================

The `demo extension <https://github.com/open-formulieren/demo-extension>`_ is an example of an extension plugin.

An extension must be implement as a Django package, which is a stricter form of a
regular Python package. Extension code is allowed to import from Open Forms' public API, as documented :ref:`here<developers_backend_core_index>`.

Extensions cannot require modifications to Django settings. Any run-time configuration options can be specified as:

* Deployment time environment variables, for which the ``openforms.conf.utils.config`` helper is available

* Dynamic options using ``django-solo``, with the advantage that configuration can be modified at runtime

If any initialization or module loading is needed, this should be done as part of the
extension's ``extension.apps.ExtensionConfig.ready`` hook, which is called when Django
bootstraps. This is the mechanism by which Open Forms plugins are registered
(refer to the :ref:`plugin section<plugins_index>` for further details).

Steps to implement an extension plugin
--------------------------------------

#. You can use the `default-app`_ as a template for an empty django package. Follow the instructions in the ``README.rst`` file to start a new Django project.

#. Implement the plugin in the ``<project_name>`` directory. This will require at least updating/adding the files below. Refer to the :ref:`plugin section<plugins_index>` for further details.

   * ``apps.py``. See for example `apps.py`_.

   * ``plugin.py``. See for example `plugin.py`_. This is where the functionality of the plugin will be implemented.

.. _plugin.py: https://github.com/open-formulieren/demo-extension/blob/main/demo_extension/plugin.py
.. _apps.py: https://github.com/open-formulieren/demo-extension/blob/main/demo_extension/apps.py
.. _default-app: https://github.com/maykinmedia/default-app

Configurable options
^^^^^^^^^^^^^^^^^^^^

Extensions cannot require modifications to the Django settings of Open Forms. Any run-time configuration option can
be specified as

#. Deployment time environment variables. See `plugin.py:35 <https://github.com/open-formulieren/demo-extension/blob/main/demo_extension/plugin.py#L35>`_.

#. Dynamic options using ``django-solo``, with the advantage that configuration can be
   modified at runtime through the Admin interface. See `models.py`_ and `admin.py`_ in the demo plugin.
   If you add a solo model, you will have to generate migrations. See the :ref:`section below<test_extension_plugin_locally>` for details.

#. For certain types of plugins, like for registration backends, it is also possible to add form-specific options.
   These can be specified with a serializer. See `config.py`_ for details.

.. _models.py: https://github.com/open-formulieren/demo-extension/blob/main/demo_extension/models.py
.. _admin.py: https://github.com/open-formulieren/demo-extension/blob/main/demo_extension/admin.py
.. _config.py: https://github.com/open-formulieren/demo-extension/blob/main/demo_extension/config.py

.. _test_extension_plugin_locally:

Testing locally
---------------

In order to test your external plugin locally, you can use symlinks. Inside the ``src/`` directory of Open Forms,
create a symlink to your package. For example, in the case of the demo extension package:

.. code-block:: bash

    ln -s /path/to/plugin/demo_extension .

Now add an environment variable ``OPEN_FORMS_EXTENSIONS`` with the name of your package. The variable is a
comma-separated list of valid python identifiers (i.e. the python package names). For example:

.. code-block:: bash

    export OPEN_FORMS_EXTENSIONS=demo_extension

The Open Forms ``base.py`` settings module will extract this configuration value and
append the list of packages to ``INSTALLED_APPS``, which causes them to be loaded by
Django.

If you need to generate migrations for your package, you can now do it as follows (from within the Open Forms directory):

.. code-block:: bash

    python src/manage.py makemigrations demo_extension
    python src/manage.py migrate

If you created a solo model, you can add the configuration page to the Admin. To do this, login into the Open Forms
Admin:

#. Go to the **Configuratie** > **Application groups**.

#. Click on **Configuratie**.

#. In the **Models** secion, look for the name of your configuration model in the left table (for the demo extension, this was  ``demo_extension.Demoextensionconfig``).
   Then double click on it to add it to the right table.

#. Save the configuration.

Now the configuration page for your package will be visible on the main Admin page under **Configuratie**.
