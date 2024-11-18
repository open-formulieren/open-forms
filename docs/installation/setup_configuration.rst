.. _installation_configuration_cli:

==============================
Open Forms configuration (CLI)
==============================

After deploying Open Forms, it needs to be configured to be fully functional. The
command line tool ``setup_configuration`` assist with this configuration:

* It uses environment variables for all configuration choices, therefore you can integrate this with your
  infrastructure tooling such as init containers and/or Kubernetes Jobs.
* The command can self-test the configuration to detect problems early on

You can get the full command documentation with:

.. code-block:: bash

    src/manage.py setup_configuration --help

.. warning:: This command is declarative - if configuration is manually changed after
   running the command and you then run the exact same command again, the manual
   changes will be reverted.

Preparation
===========

The command executes the list of pluggable configuration steps, and each step
has required specific environment variables, that should be prepared.
Here is the description of all available configuration steps and the environment variables,
used by each step.


Services configuration
----------------------

TODO: add generated documentation for ``zgw_consumers.ServiceConfigurationStep``

Objects API registration configuration
--------------------------------------

TODO: add generated documentation for ``ObjectsAPIConfigurationStep``

Execution
=========

Open Forms configuration
------------------------

With the full command invocation, everything is configured at once. Each configuration step
is idempotent, so any manual changes made via the admin interface will be updated if the command
is run afterwards.

.. code-block:: bash

    src/manage.py setup_configuration

.. note:: Due to a cache-bug in the underlying framework, you need to restart all
   replicas for part of this change to take effect everywhere.
