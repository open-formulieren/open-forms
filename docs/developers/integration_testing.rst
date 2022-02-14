.. _developers_integration_testing:

===================
Integration testing
===================

We use Cypress to test the integration between the Open Forms backend and frontend SDK.
In these tests, the entire docker-compose stack is brought up and the forms are tested end-to-end.

Running Cypress tests
=====================

In order to run the tests locally, ensure Cypress is installed:

.. code-block::

    $ npm install

The fixtures for the tests can be generated using:

.. code-block::

    $ python src/manage.py generate_cypress_fixtures

After that, the docker-compose stack must be started:

.. code-block::

    $ docker-compose up -d

Once the stack is up and running, we can load the generated fixtures:

.. code-block::

    $ bin/load_cypress_fixtures.sh

Now the Cypress tests can be run in headless mode:

.. code-block::

    $ node_modules/.bin/cypress run

Or with a GUI:

.. code-block::

    $ node_modules/.bin/cypress open
