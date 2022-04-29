.. _developers_backend_core_index:

==================
Core functionality
==================

Reference documentation for the Open Forms core.

General principles
==================

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


.. toctree::
   :caption: Contents
   :maxdepth: 2

   submissions
   submission-renderer
   utils
   tokens
   testing-tools
