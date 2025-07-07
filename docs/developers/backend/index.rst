.. _developers_backend_index:

=====================
Backend documentation
=====================

The Open Forms backend is developed using the Django_ framework (Python based).

Django has a concept of "apps" within a project which logically contain some
functionality. The codebase layout reflects this - but the documentation is structured
following the outlined :ref:`developers_architecture`.

General principles
==================

On top of all this, we apply some general principles to keep/make the codebase
maintainable.

**Keep Django apps contained**

Django apps should focus on a single responsibility with minimal dependencies on the
"outside world".

**Explicitly expose public API**

Usually we only consider the ``service.py`` module of a Django app to be public API.
Please think twice before introducing breaking changes in those modules.

**Refrain from importing private API**

Importing things from modules in core functionality is generally frowned upon (
``service.py`` is the exception here). Modules should be able to freely alter their
implementation details, including their data model!

**Document useful, generic functionality**

Documentation makes it easier to find out what exists and avoid re-implementing the
same thing twice.

Core
====

.. toctree::
    :maxdepth: 1

    core/index
    core/formio
    core/email-verification
    core/submissions
    core/submission-renderer
    core/variables
    file-uploads
    service-fetch

Modules
=======

.. toctree::
    :maxdepth: 1

    modules/index
    modules/authentication
    modules/dmn

General purpose functionality
=============================

.. toctree::
    :maxdepth: 1

    api-clients
    core/utils
    core/tokens
    core/testing-tools
    core/templating

    upgrade-checks

Development and debug tooling
=============================

.. toctree::
    :maxdepth: 1

    tests
    logging
    dev-rendering
    profiling
    file-uploads
    external-resources

.. _Django: https://www.djangoproject.com/
