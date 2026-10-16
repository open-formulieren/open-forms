.. _developers_index:

=======================
Developer documentation
=======================

Integrating (parts of) Open Forms
=================================

Open Forms provides some functionalities for external parties to integrate with it.
See the table of contents below for articles documenting use cases.

.. toctree::
   :maxdepth: 1

   embedding
   analytics
   public-api

.. tip::

    If you're developing a client for Open Forms, please take a look at the OpenAPI 3
    specification in the root of the project or spin up an instance and visit the
    interactive documentation at ``http://localhost:8000/api/docs/``.

Modifying Open Forms itself
===========================

This documentation is intended for developer contributing to Open Forms itself, not for
people integrating with Open Forms.

In :ref:`developers_architecture` we describe the high level architecture of Open Forms
and some core principles that impact the codebase structure. Please take a look to
familiarize yourself with the design principles.

.. toctree::
   :maxdepth: 2

   architecture
   installation
   backend/index
   frontend/index
   sdk
   extensions
   i18n
   ui-components
   csp
   npm
   releases
   versioning
   ci-workflow
