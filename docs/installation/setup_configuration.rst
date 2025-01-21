.. _installation_configuration_cli:

==============================
Open Forms configuration (CLI)
==============================

After deploying Open Forms, it needs to be configured to be fully functional. The
command line tool ``setup_configuration`` assists with this configuration by loading a
YAML file in which the configuration information is specified.

For general information on how the command line tool works, refer to the
:external+django-setup-configuration:ref:`documentation <usage_docs>`.

Below are example configurations for all the configuration steps this application provides.
They can be used as a starting point and combined into a single YAML to use as input for the command.

.. warning::
    The values in the following YAML examples contain defaults and in some case dummy values, make sure to edit
    values of i.e. identifiers, secrets and other fields that have dummy values!

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
