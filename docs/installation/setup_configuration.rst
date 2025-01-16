.. _installation_configuration_cli:

==============================
Open Forms configuration (CLI)
==============================

After deploying Open Forms, it needs to be configured to be fully functional. The
command line tool ``setup_configuration`` assists with this configuration by loading a
YAML file in which the configuration information is specified.

.. code-block:: bash

    src/manage.py setup_configuration --yaml-file /path/to/your/yaml

You can get the full command documentation with:

.. code-block:: bash

    src/manage.py setup_configuration --help

.. warning:: This command is declarative - if configuration is manually changed after
   running the command and you then run the exact same command again, the manual
   changes will be reverted.

Preparation
===========

The command executes the list of pluggable configuration steps, and each step
requires specific configuration information, that should be prepared.
Here is the description of all available configuration steps and the shape of the data,
used by each step.

All of the configuration must be part of a single YAML file that is passed to the command.

OpenID Connect configuration for admin authentication
-----------------------------------------------------

.. autoclass:: mozilla_django_oidc_db.setup_configuration.steps.AdminOIDCConfigurationStep
    :noindex:

.. setup-config-example:: mozilla_django_oidc_db.setup_configuration.steps.AdminOIDCConfigurationStep

Services configuration
----------------------

.. autoclass:: zgw_consumers.contrib.setup_configuration.steps.ServiceConfigurationStep
    :noindex:

.. setup-config-example:: zgw_consumers.contrib.setup_configuration.steps.ServiceConfigurationStep


Objects API registration configuration
--------------------------------------

.. autoclass:: openforms.contrib.objects_api.setup_configuration.steps.ObjectsAPIConfigurationStep
    :noindex:

.. setup-config-example:: openforms.contrib.objects_api.setup_configuration.steps.ObjectsAPIConfigurationStep

ZGW APIs registration configuration
-----------------------------------

.. autoclass:: openforms.registrations.contrib.zgw_apis.setup_configuration.steps.ZGWApiConfigurationStep
    :noindex:

.. setup-config-example:: openforms.registrations.contrib.zgw_apis.setup_configuration.steps.ZGWApiConfigurationStep

Execution
=========

Open Forms configuration
------------------------

With the full command invocation, all defined configuration steps are applied. Each step is idempotent,
so it's safe to run the command multiple times. The steps will overwrite any manual changes made in
the admin if you run the command after making these changes.
