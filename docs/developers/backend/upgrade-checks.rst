.. _developers_backend_upgrade_checks:

==============
Upgrade checks
==============

Open Forms has upgrade checks built-in to prevent inconsistent database states. This
consists of a couple of components, given that:

1. You are currently on version ``X`` and
2. you are trying to upgrade to version ``Y``

Then, the check will:

1. Validate that upgrading from version ``X`` to version ``Y`` is a supported upgrade
   path.
2. Run specified check management commands - if any command raises ``CommandError``, the
   upgrade is blocked
3. Run specified check scripts from the ``bin`` folder

Check configuration
-------------------

The upgrade paths are specified in :mod:`openforms.upgrades.upgrade_paths`, in the
``UPGRADE_PATHS`` constant.

For every target version (=version to upgrade *to*), you can specify:

* the supported version ranges to upgrade *from*
* management commands that need to pass (optional)
* custom scripts in the ``bin`` folder that need to pass (optional)

**Custom scripts**

Custom scripts must implement a ``main`` callable, taking the ``skip_setup`` boolean
(keyword) argument. If the function returns ``False`` or raises an exception, then the
upgrade is blocked.

How does it work?
-----------------

The version ranges are specified in semantic version format, and thus primarly target
official releases.

.. note:: Non-official releases are possible in the form of custom image builds, or even
   development/nightly builds that don't have an explicit version number.

1. When a release is created, it is assigned an explicit version number (see also:
   :ref:`developers_versioning`) in semantic version format, e.g.:

   ``1.0.0``, ``2.0.0-beta.1``...
2. The CI pipeline bakes this version number into the container image in the ``RELEASE``
   environment variable (and the VCS commit hash is baked into ``GIT_SHA``, accordingly)
3. The container start script (``bin/docker_start.sh``) runs migrations as part of the
   initialization, through the ``migrate`` management command.
4. Django runs the system checks *before* executing the migrations
5. Our custom system check is registered with the system checks and runs as part of the
   system checks
6. The custom check reads from the database which version was deployed earlier and
   compares this with the version from the container image (from the ``RELEASE``
   environment variable). The check then verifies if upgrading from old version (from
   the database) to the new version is possible.
7. If upgrading is not possible, an error is emitted and the ``migrate`` command does
   not execute - your database is thus left untouched. Because of the error exit code,
   the container will also not start. All information to correct this situation is
   available in the container logs.
8. If upgrading is possible, migrations are executed and add the end the version
   registered in the database is automatically updated with the value of ``RELEASE``
9. This cycle repeats for the next upgrade.

If your upgrade is blocked, you should be able to safely deploy the old version again,
make the necessary changes to resolve the problems preventing the upgrade, and then
try again.

Developers and people deploying ``latest`` (don't do this unless you're willing to
debug breaking changes!) usually receive warnings instead of errors, so their usual
flow is not broken.

