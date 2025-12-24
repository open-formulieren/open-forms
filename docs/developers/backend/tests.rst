.. _developers_backend_tests:

=============
Running tests
=============

The Open Forms backend comes with an extensive test suite to prevent regressions and
also describe intended behaviour.

.. tip:: See the :ref:`developers_backend_core_testing_tools` for a collection of
   utilities that you can use when writing tests.

Running the backend tests
=========================

The testsuite uses Django's standard test mechanism:

.. code-block:: bash

    python src/manage.py test src --exclude-tag=e2e --exclude-tag=migration_test

will run all the tests discovered in the ``src`` directory, excluding slow tests like
:ref:`end-to-end <developers_backend_tests_e2e>` and migration tests.

You can also limit the tests to run by python path:

.. code-block:: bash

    python src/manage.py test openforms.registrations.contrib.demo

or even by certain tags:


.. code-block:: bash

    python src/manage.py test src --tag=gh-2418

There's a tag ``dangerous`` for tests that point out breaking behaviour.

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

    python src/manage.py test src --tag=e2e

**Configuration**

Configuration is done through environment variables:

* ``NO_E2E_HEADLESS=<anything>``: will open an actual browser window so you can see what's
  happening. By default, tests are run in headless mode.

* ``E2E_DRIVER=chromium``: specifies which browser is used for the selenium tests,
  defaults to Chromium. Available options: ``chromium``, ``firefox`` and ``webkit``.

Example custom command:

.. code-block:: bash

    NO_E2E_HEADLESS=1 E2E_DRIVER=firefox python src/manage.py test src --tag=e2e

.. note:: Only the presence of the ``NO_E2E_HEADLESS`` is checked, not the value

Known issues
============

**AssertionError: Database queries to 'default' are not allowed in SimpleTestCase subclasses.**

These are often caused by django-solo ``SingletonModel`` sucblasses that are being
called somewhere, e.g. ``GlobalConfiguration.get_solo``. Sometimes they fetch from
cache, sometimes there is a cache miss and a database query is needed (e.g. when running
tests in reverse).

This is typically a test-isolation smell and the root cause should be fixed. This may
also be caused indirectly if you have ``LOG_OUTGOING_REQUESTS`` set to ``True`` in your
local ``.env``, as it also results in a django-solo lookup.

The preferred approach to mitigate these kind of issues is to mock the ``get_solo`` call
to prevent cache or DB hits:

.. code-block:: python

    @unittest.mock.patch(
        "path.to.module.using_the_model.GlobalConfiguration.get_solo",
        return_value=GlobalConfiguration(...),
    )
    def test_something(self, mock_get_solo):
        ...
