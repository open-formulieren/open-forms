.. _installation_issues_upgrade:

Upgrade errors
==============

It may occur that you run into errors while upgrading from an earlier Open Forms
version.

Upgrading (directly) to '<versionY>' from '<VersionX>' is not supported.
------------------------------------------------------------------------

Open Forms :ref:`validates upgrade paths <developers_backend_upgrade_checks>` as a last
resort to prevent your database from ending up in a corrupted state. Some of the
upgrade checks perform additional output to help you resolve the state of your
installation, so please read these carefully.

We document any manual interventions or minimum required versions in the
:ref:`changelog` and expect system administrators/service providers/devops roles to
check these *before* performing the upgrade. You should be able to safely roll back to
the older version (that you were on before) to resolve the issues preventing the upgrade.

Note that we also adhere to :ref:`Semantic versioning <developers_versioning>`, so
please take extra care when upgrading the major version.
