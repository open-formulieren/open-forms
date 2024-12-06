.. _configuration_index:

Configuration
=============

There are many configuration options in Open Forms. Some of these are included
in the core of Open Forms, and some are included by plugins. We cover various
configuration topics that come with Open Forms by default.

Initial configuration
---------------------

Open Forms supports the ``setup_configuration`` management command, which allows loading configuration via
YAML files. The shape of these files is described at :ref:`installation_configuration_cli`.

.. toctree::
   :maxdepth: 2

   general/index

.. toctree::
   :maxdepth: 2
   :caption: Plugins

   authentication/index
   payment/index
   prefill/index
   registration/index
   appointment/index
   validation/index
   dmn/index
