.. _introduction_versions:

==================
Available versions
==================

The Open Forms release cycle is calendar-based. Periodically, a new version with new
features and improvements is released. Additionally, we publish monthly bugfix releases.
The :ref:`changelog` documents all releases.

Currently, the development cycle consists of 4-week sprints, followed by an *off-week*
to prepare releases and perform periodic maintenance. We aim to publish a new feature
release every three sprints, so roughly once every three months.

Bugfix releases
===============

We provide bugfixes for the current and previous versions of Open Forms. For example,
if the latest stable version is 2.6.0, this means:

.. table:: Supported versions example
   :widths: auto

   ======= ==============
   Version Status
   ======= ==============
   2.7.0   in development
   2.6.x   maintained
   2.5.x   maintained
   2.4.x   not supported
   2.3.x   not supported
   ...     not supported
   ======= ==============

.. versionchanged:: 2.7.0

    Before 2.7.0, we supported old versions for 6 months after the new version was
    released. Given the available resources, this is causing too much maintenance
    overhead and limits cleaning up of technical debt.

.. seealso::

   See the :ref:`developer documentation <developers_versioning>` on versioning for
   more technical details.
