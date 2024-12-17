.. _configuration_index:

Configuration
=============

There are many configuration options in Open Forms. Some of these are included
in the core of Open Forms, and some are included by plugins. We cover various
configuration topics that come with Open Forms by default.

Open Forms supports the ``setup_configuration`` management command, which allows loading configuration via
YAML files. The shape of these files is described at :ref:`installation_configuration_cli`.

Initial configuration
---------------------

.. toctree::
   :maxdepth: 2

   general/index

Plugins
-------

Many of the plugins in Open Forms require some technical configuration before you can
use them in forms. The technical requirements are grouped by functionality module.

.. toctree::
   :maxdepth: 2

   authentication/index
   payment/index
   prefill/index
   registration/index
   appointment/index
   validation/index
   dmn/index
