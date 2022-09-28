"""
Internal Open Forms upgrade mechanics.

We have a database model that records the currently deployed version based on the
``RELEASE`` setting. On the next deploy, a system check verifies that the new version
of the code can be upgraded from the currently registered version.

If upgrading is not possible, the system check emits an error, which blocks migrations.
Users running into this error are referred to the release notes.

See :module:`openforms.upgrades.upgrade_paths` for the ``UPGRADE_PATHS`` attribute,
which defines which conditions need to be met to upgrade to a particular version.

.. note:: Versions are semantic version ranges. This means that if you're upgrading to
   2.0.3, and only a condition for 2.0.0 is defined, those conditions will be applied,
   because they match the major.minor range.
"""
