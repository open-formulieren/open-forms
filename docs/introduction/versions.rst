.. _introduction_versions:

==================
Available versions
==================

The Open Forms release cycle is calendar-based and version numbers follow
`semantic versioning <https://semver.org/>`_.

We release a new feature version each quarter. In SemVer terminology, this is typically
a minor version. Occassionally a major version is released which contains breaking
changes that cannot be handled automatically. There is at most one major version per
calendar year - we do this to minimize the impact. Minor versions may deprecate
functionalities that are then usually removed in the first upcoming major version.

Next to that, we aim to publish a monthly patch release with bugfixes, for all supported
versions. Sometimes serious bugs are discovered and then we will publish a hotfix
release outside of the regular schedule. In the event that there will be a release
addressing :ref:`security <security_policy>` issues, a pre-notice will be sent out via
the mailing list, and the release will usually be a hotfix.

The :ref:`changelog` documents all releases.

Development cycle
=================

A development cycle is one quarter of the year (3 months), made up of 4-week sprints.

During this time, new features are development and bugfixes applied to older versions,
when applicable. After each sprint, and alpha or beta version is released as
pre-release. These releases are not suitable for production usage.

At the end of the quarter and/or at the start of the next quarter, each release is
finalized into a stable version, suitable for production usage..

Supported versions
==================

We provide bugfixes for the current and previous version of Open Forms. For example,
if the latest stable version is 3.6.0, this means:

.. table:: Supported versions example
   :widths: auto

   ======= ==============
   Version Status
   ======= ==============
   3.7.0   in development
   3.6.x   maintained
   2.5.x   maintained
   3.4.x   not supported
   3.3.x   not supported
   ...     not supported
   ======= ==============

.. versionchanged:: 2.7.0

    Before 2.7.0, we supported old versions for 6 months after the new version was
    released. Given the available resources, this was causing too much maintenance
    overhead and limits cleaning up of technical debt.

.. seealso::

   See the :ref:`developer documentation <developers_versioning>` on versioning for
   more technical details.
