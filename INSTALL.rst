============
Installation
============

This installation is meant for developers of Open Forms. If you are looking to 
install Open Forms to try it out, or to run it in production, please consult 
the documentation.

The project is developed in `Python`_ using the `Django framework`_.


Prerequisites
=============

You need the following libraries and/or programs:

* `Python`_ 3.8 or above
* Python `Virtualenv`_ and `Pip`_
* `PostgreSQL`_ 10 or above
* `Node.js`_
* `npm`_
* `yarn`_

.. _Python: https://www.python.org/
.. _Django framework: https://www.djangoproject.com/
.. _Virtualenv: https://virtualenv.pypa.io/en/stable/
.. _Pip: https://packaging.python.org/tutorials/installing-packages/#ensure-pip-setuptools-and-wheel-are-up-to-date
.. _PostgreSQL: https://www.postgresql.org
.. _Node.js: http://nodejs.org/
.. _npm: https://www.npmjs.com/
.. _yarn: https://yarnpkg.com/


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

       $ npm ci
       $ npm run build

5. Activate your virtual environment and create the statics and database:

   .. code-block:: bash

       $ python src/manage.py collectstatic --link
       $ python src/manage.py migrate

6. Create a superuser to access the management interface:

   .. code-block:: bash

       $ python src/manage.py createsuperuser

7. You can now run your installation and point your browser to the address
   given by this command:

   .. code-block:: bash

       $ python src/manage.py runserver

8. Create a .env file with database settings. See dotenv.example for an example.

        $ cp dotenv.example .env


**Note:** If you are making local, machine specific, changes, add them to
``src/openforms/conf/local.py``. You can base this file on the
example file included in the same directory.

**Note:** You can run watch-tasks to compile `Sass`_ to CSS and `ECMA`_ to JS
using ``npm run watch``.

.. _ECMA: https://ecma-international.org/
.. _Sass: https://sass-lang.com/


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
       $ npm install
       $ npm run build

3. Update the statics and database:

   .. code-block:: bash

       $ python src/manage.py collectstatic --link
       $ python src/manage.py migrate


Testsuite
=========

To run the test suite:

.. code-block:: bash

    $ python src/manage.py test openforms

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

All settings for the project can be found in
``src/openforms/conf``.
The file ``local.py`` overwrites settings from the base configuration.


Commands
========

Commands can be executed using:

.. code-block:: bash

    $ python src/manage.py <command>

There are no specific commands for the project. See
`Django framework commands`_ for all default commands, or type
``python src/manage.py --help``.

.. _Django framework commands: https://docs.djangoproject.com/en/dev/ref/django-admin/#available-commands
