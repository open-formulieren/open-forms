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
* Anywhere on the file path, but the ``PYTHONPATH`` environment variable is modified to
  include the path to the extension.
* In the relevant site-packages directory, similarly to when an Open Forms dependency
  is installed with ``pip install`` and ``virtualenv``.

Building and distributing the extended Open Forms
-------------------------------------------------

You can build a custom Docker image extending an Open Forms release with a custom
``Dockerfile``, in which the extension source code is added to the desired location.
See :ref:`developers_extending_docker` for more details.

Another option is to mount the source code as a volume in a custom ``docker-compose.yml``
file or as part of your Kubernetes manifests, depending on how you deploy your
instance(s).

The `demo extension`_ is an example
of an extension plugin. It implements a demo registration backend that prints the
specified configuration variables to the console. It uses a custom ``Dockerfile``
to extend the (latest) Open Forms version.

Steps to implement an extension plugin
--------------------------------------

#. The `default-app`_ can be used as a template for an empty django package.
   Follow the instructions in the ``README.rst`` file to start a new Django project.

#. Implement the plugin in the ``<project_name>`` directory. This will require at least
   updating/adding the files below. Refer to the :ref:`plugin section<plugins_index>` for
   further details.

   * ``apps.py``. See for example `apps.py`_.

   * ``plugin.py``. See for example `plugin.py`_. This is where the functionality of the plugin will be implemented.

Extension code is allowed to import from Open Forms' :ref:`public API<developers_backend_core_index>`.

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

    export OPEN_FORMS_EXTENSIONS=demo_extension,another_extension

If you need to generate migrations for your package, you can now do it as follows (from within the Open Forms directory):

.. code-block:: bash

    python src/manage.py makemigrations demo_extension
    python src/manage.py migrate

If you created a solo model, the configuration page should be available in the admin
interface automatically under the "miscellaneous" group. Currently it's not possible to
configure these groups from an extension as they are reset on every deploy.

.. note::

   If your demo-extension is a demo feature (``Plugin.is_demo_plugin = True``), you must
   ensure that demo plugins are enabled in the admin interface for them to be available.

   Under **Configuratie** > **Algemene configuratie** scroll to the bottom of the page and
   click on **Tonen** next to **Feature flags, test- en ontwikkelinstellingen**. Then,
   check the box **Demo plugins inschakelen** and save the changes.

.. _developers_extending_docker:

Testing and distributing with Docker
------------------------------------

The recommended way to create a container image is to extend the Open Forms base image,
and set up a ``docker-compose.yml`` locally to test with this custom image. You can
find examples of both in the `demo extension`_ repository.

**Dockerfile structure**

We recommend using a two-stage Dockerfile approach, where the first stage is used to
install any additional Python dependencies (if relevant). This stage should inherit
from the same Python base image of Open Forms to keep the Python version identical.
Open Forms itself also applies this principle, so you can look at the upstream
``Dockerfile`` for inspiration.

The second stage is meant for the production image and should extend from the Open Forms
version you are extending, e.g. ``open-formulieren/open-forms:1.0.0``. You can copy
the dependencies from your build stage and the extension source code into the final
image here.

**Building and tagging the image**

From within your extension repository, build the image and give it a name and tag of
your choice, for example:

.. code-block:: bash

    docker build -t myorg/open-forms:1.0.0 .

or use the relevant docker-compose command variants.

**Running all the services with docker-compose**

You can create your own ``docker-compose.yml`` inspired by the Open Forms docker-compose
configuration, or use the `docker-compose.override.yml <https://docs.docker.com/compose/extends/#understanding-multiple-compose-files>`_
approach. Typically you will want to modify the image names and any additional
environment variables your extensions require.


.. code-block:: bash

    docker-compose up


Testing in CI
-------------

The approach for testing in CI largely follows :ref:`developers_extending_docker`.

Open Forms also publishes an image to Docker Hub including the test dependencies to
facilitate unit testing in PYthon for your extension. The
``openformulieren/open-forms:test`` image is always based on the ``latest`` tag and
includes the upstream ``requirements/ci.txt``.

See also our :ref:`versioning policy<developers_versioning>` to see how and when we
make breaking changes.


.. _demo extension: https://github.com/open-formulieren/demo-extension
