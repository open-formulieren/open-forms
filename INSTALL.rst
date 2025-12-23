============
Installation
============

This installation is meant for developers of Open Forms. If you are looking to
install Open Forms to try it out, or to run it in production, please consult
the `documentation <https://open-forms.readthedocs.io/en/stable/installation/>`_ for
alternative installation methods.

.. note:: The `Developer documentation`_ on Read the Docs provides working internal
   links, in case you are reading this on Github or elsewhere.

The (backend) project is developed in `Python`_ using the `Django framework`_.

For the SDK (frontend), see the `Storybook <https://open-formulieren.github.io/open-forms-sdk/>`_
documentation. This covers *all* SDK related development and will include custom
application development documentation in the future.

Prerequisites
=============

You need the following libraries and/or programs:

* `Python`_ 3.12
* Python `Virtualenv`_ and `Pip`_
* `PostgreSQL`_ 12 or above
* `Redis`_ for `Celery`_ to work
* `Node.js`_, see ``.nvmrc`` for the exact version. Using nvm_ is recommended.
* `npm`_
* `gettext`_
* `gdal-bin`_ (should pull in ``libgeos``)
* `chromedriver`_

You will also need the following operating-system libraries:

* pkg-config
* libmagic1
* libxml2-dev
* libxmlsec1-dev
* libxmlsec1-openssl
* libpq-dev

.. _Python: https://www.python.org/
.. _Django framework: https://www.djangoproject.com/
.. _Virtualenv: https://virtualenv.pypa.io/en/stable/
.. _Pip: https://pip.pypa.io/en/stable/installation/
.. _PostgreSQL: https://www.postgresql.org
.. _Node.js: http://nodejs.org/
.. _nvm: https://github.com/nvm-sh/nvm
.. _npm: https://www.npmjs.com/
.. _Redis: https://redis.io/
.. _gettext: https://www.gnu.org/software/gettext/
.. _gdal-bin: https://docs.djangoproject.com/en/3.2/ref/contrib/gis/gdal/
.. _chromedriver: https://chromedriver.chromium.org/downloads


Getting started
===============

Developers can follow the following steps to set up the project on their local
development machine.

1. Navigate to the location where you want to place your project.

2. Get the code:

   .. code-block:: bash

       $ git clone git@github.com:open-formulieren/open-forms.git
       $ cd open-forms

3. Install all required libraries.

   .. code-block:: bash

       $ virtualenv env
       $ source env/bin/activate
       $ pip install -r requirements/dev.txt

4. Install and build the frontend libraries:

   .. code-block:: bash

       $ npm ci --legacy-peer-deps
       $ npm run build

5. Create a ``.env`` file with database settings. See dotenv.example for an example.

   .. code-block:: bash

        $ cp dotenv.example .env

6. Activate your virtual environment and create the statics and database:

   .. code-block:: bash

       $ python src/manage.py collectstatic --link
       $ python src/manage.py compilemessages
       $ python src/manage.py migrate

7. Create a superuser to access the management interface:

   .. code-block:: bash

       $ python src/manage.py createsuperuser

8. You can now run your installation and point your browser to the address
   given by this command:

   .. code-block:: bash

       $ python src/manage.py runserver


**Note:** If you are making local (machine specific) changes, add them to your local
``.env`` file or ``src/openforms/conf/local.py``. You can base this file on the
example file included in the same directory.

For functional testing, if you run into trouble submitting forms or saving forms in the admin,
ensure the following is valid:

* `Redis server is running <https://redis.io/docs/latest/operate/oss_and_stack/install/>`_
* `Celery worker is running <https://open-forms.readthedocs.io/en/latest/developers/installation.html#running-background-and-periodic-tasks>`_
* Uncomment the ``CORS_ALLOWED_ORIGINS`` variable in your local ``.env`` file and add the address from step 8 to this list.


Building and running the frontend code
--------------------------------------

The backend project (``open-forms``, as opposed to ``open-forms-sdk``) comes with its
own SASS/Javascript build pipeline.

For a one-off build:

.. code-block:: bash

    npm run build

However, while developing on frontend code, it's recommended to start a watch process
that performs incremental builds:

.. code-block:: bash

    npm start


Using the SDK in the Open Forms backend
=======================================

The Docker image build copies the build artifacts of the SDK into the backend container.
This is not available during local development, but can be mimicked by symlinking or
fully copying a build of the SDK to Django's staticfiles. This enables you to use
this particular SDK build for local backend dev and testing.

.. note:: This only builds the SDK once so that you can use it from within the
   backend project. For actual SDK development, please review the appropriate
   `SDK documentation <https://open-formulieren.github.io/open-forms-sdk/>`_.

1. First, ensure you have checked out the SDK repository and made a production build:

   .. code-block:: bash

      cd /path/to/code/
      git clone git@github.com:open-formulieren/open-forms-sdk.git
      cd open-forms-sdk
      git submodule update --init
      npm install
      npm run build:design-tokens
      npm run build

   This produces the production build artifacts in the ``dist/bundles`` folder, it should
   contain ``open-forms-sdk.mjs`` and ``open-forms-sdk.css`` files.

2. Next, symlink this so it gets picked up by Django's staticfiles:

   .. code-block:: bash

      $ ln -s /path/to/code/open-forms-sdk/dist src/openforms/static/sdk

3. Finally, you *can* run collectstatic to verify it all works as expected.

   .. code-block:: bash

      $ python src/manage.py collectstatic

If you're using a tagged version with the SDK code in a subdirectory, you can set the
``SDK_RELEASE`` environment variable - it defaults to ``latest`` in dev settings.

Update installation
===================

When updating an existing installation:

1. Activate the virtual environment:

   .. code-block:: bash

       $ cd open-forms
       $ source env/bin/activate

2. Update the code and libraries:

   .. code-block:: bash

       $ git pull
       $ pip install -r requirements/dev.txt
       $ npm install --legacy-peer-deps
       $ npm run build

3. Update the statics and database:

   .. code-block:: bash

       $ python src/manage.py collectstatic --link
       $ python src/manage.py migrate


Documentation build
===================

The documentation lives in the ``docs`` folder.

The documentation build includes the SDK changelog, which requires you to set up a
symlink (or a dummy file). The preferred approach is using the real symlink.

1. Ensure you have a clone of the SDK repository, e.g. in ``/path/to/open-forms-sdk``.

2. Set up the symlink from the changelog file:

   .. code-block:: bash

       $ ln -s /path/to/open-forms-sdk/CHANGELOG.rst docs/changelog-sdk.rst

3. Build the docs to verify it's all correct:

   .. code-block:: bash

       $ cd docs
       $ make html

Alternatively, instead of symlinking you can also just create the file
``docs/changelog-sdk.rst`` with some dummy content.

Testsuite
=========

To run the test suite:

.. code-block:: bash

    playwright install
    python src/manage.py test src

See the detailed developer documentation for more information and different strategies.

Configuration via environment variables
=======================================

A number of common settings/configurations can be modified by setting
environment variables. You can persist these in your ``local.py`` settings
file or as part of the ``(post)activate`` of your virtualenv.

* ``SECRET_KEY``: the secret key to use. A default is set in ``dev.py``

* ``DB_NAME``: name of the database for the project. Defaults to ``openforms``.
* ``DB_USER``: username to connect to the database with. Defaults to ``openforms``.
* ``DB_PASSWORD``: password to use to connect to the database. Defaults to ``openforms``.
* ``DB_HOST``: database host. Defaults to ``localhost``
* ``DB_PORT``: database port. Defaults to ``5432``.

* ``SENTRY_DSN``: the DSN of the project in Sentry. If set, enabled Sentry SDK as
  logger and will send errors/logging to Sentry. If unset, Sentry SDK will be
  disabled.


Settings
========

All settings for the project can be found in ``src/openforms/conf``.

The file ``local.py`` overwrites settings from the base configuration.

Running background and periodic tasks
=====================================

We use `Celery`_ as background task queue.

You can run celery beat and worker(s) in a shell to activate the asynchronous task
queue processing:

To start beat which triggers periodic tasks:

.. code-block:: bash

   $ ./bin/celery_beat.sh

To start the background workers executing tasks:

.. code-block:: bash

   $ CELERY_WORKER_CONCURRENCY=4 ./bin/celery_worker.sh

.. note:: You can tweak ``CELERY_WORKER_CONCURRENCY`` to your liking, the default is 1.

To start flower for task monitoring:

.. code-block:: bash

   $ ./bin/celery_flower.sh

Commands
========

Commands can be executed using:

.. code-block:: bash

    $ python src/manage.py <command>

You can always get a full list of available commands by running:

.. code-block:: bash

    $ python src/manage.py help

There are a number of developer management commands available in this project.

``appointment``
---------------

Performs various appointment plugin calls.

``dmn_evaluate``
----------------

Evaluate a particular decision definition.

``dmn_list_definitions``
------------------------

List the available decision definitions for a given engine.

``check_duplicate_component_keys``
----------------------------------

Check all forms and report duplicated component keys.

``export``
----------

Export a form.

``import``
----------

Import a form.

``msgraph_list_files``
----------------------

List the files in MS Sharepoint.

``list_prefill_plugins``
------------------------

List the registered prefill plugins and the attributes they expose.

``register_submission``
-----------------------

Execute the registration machinery for a given submission.

``render_confirmation_pdf``
---------------------------

Render the summary/confirmation into a PDF for a given submission.

``render_report``
-----------------

Render a summary for a given submission in a particular render mode.

``test_submission_completion``
------------------------------

Generate a submission and test the completion process flow.

Utility scripts
===============

The ``bin`` folder contains some utility scripts sporadically used.

``bin/bumpversion.sh``
----------------------

Wrapper around ``bumpversion`` which takes care of ``package-lock.json`` too.

This allows bumping the version according to semver, e.g.:

.. code-block:: bash

   ./bin/bumpversion.sh minor

``bin/compile_dependencies.sh``
-------------------------------

Wrapper script around ``pip-compile``. New dependencies should be added to the
relevant ``.in`` file in ``requirements``, and then you run the compile script:

.. code-block:: bash

   ./bin/compile_dependencies.sh

You should also use this to *upgrade* existing dependencies to a newer version, for
example:

.. code-block:: bash

   ./bin/compile_dependencies.sh -P django

Any additional argument passed to the script are passed down to the underlying
``pip-compile`` call.

``bin/find_untranslated_js.py``
-------------------------------

A utility that checks the JavaScript translation catalogs and detects strings that
may still need translation.

``bin/generate_admin_index_fixture.sh``
---------------------------------------

After configuring the application groups in the admin through point-and-click, you
call this script to dump the configuration into a fixture which will be loaded on
all other installations.

``bin/generate_default_groups_fixture.sh``
------------------------------------------

After configuring the user groups with the appropriate permissions in the admin,
you call this script to dump the configuration into a fixture which will be loaded on
all other installations.

``bin/generate_default_map_tile_layers_fixture.sh``
-----------------------------------------------------------

After configuring the map tile layers in the admin,
you call this script to dump the configuration into a fixture which will be loaded on
all other installations.

``bin/generate_oas.sh``
-----------------------

This script generates the OpenAPI specification from the API endpoint implementations.

You must call this after making changes to the (public) API.

``bin/makemessages.sh``
-----------------------

Script to extract the backend and frontend translation messages into their catalogs
for translation.


.. _Celery: https://docs.celeryq.dev/en/stable/
.. _Developer documentation: https://open-forms.readthedocs.io/en/latest/developers/
