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

.. _CONTRIBUTING.md: https://github.com/open-formulieren/open-forms/blob/main/CONTRIBUTING.md

Creating an external plugin
===========================

An extension must be implemented as a Django package, which is a stricter form of a
regular Python package. They can be developed independently from the open-formulieren Github organization.

The extensions can be loaded at deployment time through the environment variable ``OPEN_FORMS_EXTENSIONS`` which
specifies the Python name of the extensions to load. Open Forms will extract this configuration value and
load the referenced extension packages. For an extension to be loaded, it needs to be present in the ``PYTHONPATH``.
This means that it needs to be either:

* In the ``src/`` directory of Open Forms. It is then automatically picked up.
* Anywhere on the file path, but the ``PYTHONPATH`` environment variable is modified to
  include the path to the extension.
* In the relevant site-packages directory, similarly to when an Open Forms dependency
  is installed with ``pip install`` and ``virtualenv``. In order for this to work, the extension should be published on
  PyPi and added to the ``requirements/extensions.in`` file.

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

#. Deployment time environment variables. See `plugin.py:35 <https://github.com/open-formulieren/demo-extension/blob/main/demo_extension/plugin.py>`_.

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

or use the relevant ``docker compose`` command variants.

**Running all the services with docker compose**

You can create your own ``docker-compose.yml`` inspired by the Open Forms docker-compose
configuration, or use the `docker-compose.override.yml <https://docs.docker.com/compose/multiple-compose-files/extends/>`_
approach. Typically you will want to modify the image names and any additional
environment variables your extensions require.


.. code-block:: bash

    docker compose up


Testing in CI
-------------

There are multiple approaches to testing in CI. These include:

* Using git submodules
* Using symlinks

**Git submodules**

You can include Open-Forms as a `git submodule`_ in the repository of the extension with:

.. code-block:: bash

   git submodule add https://github.com/open-formulieren/open-forms.git

Then, stage and commit the updated files.

In order for the extension to be able to import from ``openforms``, the path to the ``openforms`` package needs to be present in
the ``PYTHON_PATH``. If it is not present, it can be added with:

.. code-block:: bash

   export PYTHON_PATH=$PYTHON_PATH:<path to extension repo>/open-forms/src

Open-Forms (in the git submodule) should then be set up in the same way as when installing Open-Forms for development.
See :ref:`developers_installation` for more information.

With this set up, from within the extension repository it is possible to test the extension. This can be done
using the ``manage.py`` file from open-forms:

.. code-block:: bash

   open-forms/src/manage.py test extension_package

In Github Actions, one can then create an action to run the tests with a similar logic. This action requires a ``postgres``
and a ``redis`` service. It is possible to checkout the repository with the Open-Forms submodule using:

.. code-block:: yaml

   - uses: actions/checkout@v3
     with:
       submodules: true

Then, after setting up the Open-Forms backend with the ``maykinmedia/setup-django-backend@v1.1`` action, one can run the
tests as follows. Note that both the directory containing the Open-Forms ``manage.py`` and the working directory are
automatically added to the path (so there is no need to update the ``PYTHON_PATH``).

.. code-block:: yaml

   - name: Run tests
     run: |
       python open-forms/src/manage.py compilemessages
       coverage run --source=extension_package open-forms/src/manage.py test extension_package
       coverage xml -o coverage-extension.xml
     env:
       DJANGO_SETTINGS_MODULE: openforms.conf.ci
       OPEN_FORMS_EXTENSIONS: extension_package

For an example of how to set up github action with this method, look at the `demo extension`_.

The advantages of using this approach include:

* If you are not actively developing Open-Forms locally, then this approach keeps the extension nicely contained in one
  folder.
* Setting up CI with Github actions is more straightforward.

.. _demo extension: https://github.com/open-formulieren/demo-extension
.. _git submodule: https://git-scm.com/book/en/v2/Git-Tools-Submodules

**Symlinks**

This approach involves symlinking the extension package inside Open-Forms. The idea behind it is described in
:ref:`test_extension_plugin_locally`.

In order to create a Github Action to test with this approach, you need to checkout both the extension AND the
Open-Forms repositories:

.. code-block:: yaml

   - name: Checkout Open Forms
     uses: actions/checkout@v3
     with:
       repository: open-formulieren/open-forms
       path: open-forms

   - name: Checkout extension
     uses: actions/checkout@v3
     with:
       path: extension

Then, the Open-Forms backend needs to be set-up. You can use the ``maykinmedia/setup-django-backend@v1.1`` action,
specifying the ``working-directory: open-forms`` and the ``nvmrc-custom-dir: open-forms`` arguments in addition to
all the other arguments that are normally used to set up the Open-Forms backend.

Next, the extension package needs to be symlinked in the Open-Forms repository:

.. code-block:: yaml

   - name: Make symlink in OF to the extension
     run: |
       ln -s ${{ github.workspace }}/extension/extension_package ${{ github.workspace }}/open-forms/src

The tests can be run in the same way as for the previous approach, but the ``working-directory`` needs to be specified:

.. code-block:: yaml

   - name: Run tests
     run: |
       python open-forms/src/manage.py compilemessages
       coverage run --source=extension_package open-forms/src/manage.py test extension_package
       coverage xml -o coverage-extension.xml
     env:
       DJANGO_SETTINGS_MODULE: openforms.conf.ci
       OPEN_FORMS_EXTENSIONS: extension_package
     working-directory: ${{ github.workspace }}/open-forms

In order to get CodeCov working properly, the ``working-directory`` and the ``root_dir`` parameters both need to be
specified:

.. code-block:: yaml

   - name: Publish coverage report
     uses: codecov/codecov-action@v3.1.4
     with:
       root_dir: ${{ github.workspace }}/extension
       working-directory: ${{ github.workspace }}/open-forms
       files: ./coverage-extension.xml

For examples of how to set up Github Actions with this approach, look at `open-forms-ext-haalcentraal-hr`_ and
`open-forms-ext-token-exchange`_.

The advantages of using this approach are:

* If you are developing Open-Forms locally, you do not need to have an extra copy of the repository inside the extension
  repository.
* If you want to test multiple extensions at the same time, this can be easily achieved by adding more symlinks to
  Open-Forms.

.. _open-forms-ext-haalcentraal-hr: https://github.com/open-formulieren/open-forms-ext-haalcentraal-hr
.. _open-forms-ext-token-exchange: https://github.com/open-formulieren/open-forms-ext-token-exchange
