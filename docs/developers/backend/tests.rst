.. _developers_backend_tests:

=============
Running tests
=============

The Open Forms backend comes with an extensive test suite to prevent regressions and
also describe intended behaviour.

Running the backend tests
=========================

The testsuite uses Django's standard test mechanism:

.. code-block:: bash

    python src/manage.py test src --exclude=e2e

will run all the tests discovered in the ``src`` directory, excluding
:ref:`developers_backend_tests_e2e`.

You can also limit the tests to run by python path:

.. code-block:: bash

    python src/manage.py test openforms.registrations.contrib.demo

or even by certain tags:


.. code-block:: bash

    python src/manage.py test src --tag=gh-2418

For all options, see ``src/manage.py test --help``.

Cheatsheet for speeding up tests
--------------------------------

* ``--keepdb`` to skip running all migrations every time
* ``--parallel <number>`` to break the testsuite into ``<number>`` parts and run them
  in parallel.
* ``--reverse`` to scan for test isolation problems
* ``coverage run src/manage.py test src <options> && coverage html`` to measure code coverage

Frontend tests
==============

There is (a limited) set of tests for the frontend code used in the backend. Tests are
run with Jest.

.. code-block:: bash

    npm run test

You can also run jest in watch mode or pass any other flags:

.. code-block:: bash

    npm run test -- --watch

.. _developers_backend_tests_e2e:

End-to-end tests
================

We have some end-to-end and Javascript smoke tests with Playwright for the custom JS
used in the admin.

These tend to be slower and harder to debug/maintain.

**Installation**

After installing the dependencies, install the browsers locally:

.. code-block:: bash

    playwright install

**Running only the E2E tests**

.. code-block:: bash

    TWO_FACTOR_PATCH_ADMIN=no python src/manage.py test src --tag=e2e

.. note:: When the admin is monkeypatched to enable 2FA behaviour, it's been observed
   that the end to end tests fail to run/complete properly. Disabling this via your
   local settings or the environment variable ``TWO_FACTOR_PATCH_ADMIN=no`` mitigates
   this.

**Configuration**

Configuration is done through environment variables:

* ``NO_E2E_HEADLESS=1``: will open an actual browser window so you can see what's
  happening. By default, tests are run in headless mode.

* ``E2E_DRIVER=chromium``: specifies which browser is used for the selenium tests,
  defaults to Chromium. Available options: ``chromium``, ``firefox`` and ``webkit``.

Example custom command:

.. code-block:: bash

    export NO_E2E_HEADLESS=1 E2E_DRIVER=firefox
    python src/manage.py test src --tag=e2e
