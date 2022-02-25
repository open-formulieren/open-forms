.. _developers_extending:

=========
Extending
=========

Open Forms ("the backend") is implemented with a :ref:`pluggable architecture<plugins_index>`.
Modules and plugins are Python packages with some Django bindings. They get called
by the Open Forms core functionality (forms, submissions...).

We support two ways to add new plugins:

#. Adding new plugins directly in Open Forms. These are extensions that serve the greater community and can be
   contributed as a pull request to Open Forms (more information can be found in the `CONTRIBUTING.md`_).

#. Adding 'external' plugins. These are extensions that are extremely specific or can't be open-sourced.
   Instructions on how to implement such 'external plugins' are described below.

.. _CONTRIBUTING.md: https://github.com/open-formulieren/open-forms/blob/master/CONTRIBUTING.md

Creating an external plugin
===========================

An extension must be implemented as a Django package, which is a stricter form of a
regular Python package. They can be developed independently from the open-formulieren Github organisation.

The extensions can be loaded at deployment time through the environment variable ``OPEN_FORMS_EXTENSIONS`` which
specifies the Python name of the extensions to load. Open Forms will extract this configuration value and
load the referenced extension packages. For an extension to be loaded, it needs to be present in the ``PYTHONPATH``.
This means that it needs to be either:

* In the ``src/`` directory of Open Forms. It is then automatically picked up.
* Anywhere on the file path, but the ``PYTHONPATH`` environment variable is modified to include the path to the extension.
* In the relevant site-packages directory, similarly to when an Open Forms dependency is installed with ``pip install``
   and ``virtualenv``.

Building and distributing the extended Open Forms
-------------------------------------------------
You can build a custom Docker image extending an Open Forms release with a custom `Dockerfile`, in which the
extension source code is added to the desired location. Another option is to mount the source code as a volume
in a custom ``docker-compose.yml`` file or as part of your Kubernetes manifests, depending on how you deploy your
instance(s).

The `demo extension <https://github.com/open-formulieren/demo-extension>`_ is an example of an extension plugin. It
implements a demo registration backend that prints the specified configuration variables to the console. It uses
a custom ``Dockerfile`` to extend the Open Forms latest version.

Steps to implement an extension plugin
--------------------------------------

#. The `default-app`_ can be used as a template for an empty django package.
   Follow the instructions in the ``README.rst`` file to start a new Django project.

#. Implement the plugin in the ``<project_name>`` directory. This will require at least updating/adding the files below.
   Refer to the :ref:`plugin section<plugins_index>` for further details.

   * ``apps.py``. See for example `apps.py`_.

   * ``plugin.py``. See for example `plugin.py`_. This is where the functionality of the plugin will be implemented.

Extension code is allowed to import from Open Forms' public API, as
documented :ref:`here<developers_backend_core_index>`.

Any additional initialisation that the extension module might need can be implemented in the
``extension.apps.ExtensionConfig.ready`` hook. This hook is called when Django bootstraps and it is the mechanism used
by Open Forms to register plugins (refer to the :ref:`plugin section<plugins_index>` for further details).


.. _plugin.py: https://github.com/open-formulieren/demo-extension/blob/main/demo_extension/plugin.py
.. _apps.py: https://github.com/open-formulieren/demo-extension/blob/main/demo_extension/apps.py
.. _default-app: https://github.com/maykinmedia/default-app

Configurable options
^^^^^^^^^^^^^^^^^^^^

Extensions cannot require modifications to the Django settings of Open Forms. Any run-time configuration option can
be specified as:

#. Deployment time environment variables. See `plugin.py:35 <https://github.com/open-formulieren/demo-extension/blob/main/demo_extension/plugin.py#L35>`_.

#. Dynamic options using ``django-solo``, with the advantage that configuration can be
   modified at runtime through the Admin interface. See `models.py`_ and `admin.py`_ in the demo plugin.
   If you add a solo model, you will have to generate migrations.
   See the :ref:`section below<test_extension_plugin_locally>` for details.

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

If you need to generate migrations for your package, you can now do it as follows (from within the Open Forms directory):

.. code-block:: bash

    python src/manage.py makemigrations demo_extension
    python src/manage.py migrate

If you created a solo model, you can add the configuration page to the Admin. To do this, log into the Open Forms
Admin:

#. Go to the **Configuratie** > **Application groups**.

#. Click on **Configuratie**.

#. In the **Models** section, look for the name of your configuration model in the left table (for the demo extension, this was  ``demo_extension.Demoextensionconfig``).
   Then double click on it to add it to the right table.

#. Save the configuration.

Now the configuration page for your package will be visible on the main Admin page under **Configuratie**.

Since the demo-extension plugin is a demo feature, the demo plugins need to be enabled in the admin.
Under **Configuratie** > **Algemene configuratie** scroll to the bottom of the page and click on **Tonen** next to
**Feature flags, test- en ontwikkelinstellingen**. Then, check the box **Demo plugins inschakelen** and save the changes.

Testing with Docker
-------------------

First, the image for the extension needs to be built. For example, for the demo-extension this can be done as follows.
From within the demo-extension directory (which contains the ``Dockerfile``), build the image:

.. code-block:: bash

    docker build -t demo-extension:tag-name .

This is a multi-stage build, where in the first stage (``demo-extension-build``) the image for the demo extension is build
from the python:3.8-slim-buster base.

In the second stage (``production-build``), the ``openformulieren/open-forms:tag`` is used as base.
The dependencies for the demo-extension are copied to the ``/usr/local/lib/python3.8`` (they should not overwrite the
dependencies already present from the Open Forms requirements) and the ``demo_extension`` source code is copied
to the ``src/`` directory.

Then, once this new 'extended' Open Forms image is built, it can be run with ``docker-compose``
(again from within the demo-extension directory, which contains the ``docker-compose.yml`` file).
It is important that the name used in the docker-compose for the image of the demo-extension corresponds to the one used
when building the image (``demo-extension:tag-name``).

.. code-block:: bash

    docker-compose up
