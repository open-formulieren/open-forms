.. _developers_backend_plugins_dmn:

===========================
Decision Modelling Notation
===========================

Decision Modelling Notation (DMN) is an
`international standard <https://www.omg.org/dmn/>`_ for modelling *rules* resulting
in certain outputs given certain input values. DMN is a machine-readable XML-based
format which typically defines one or more decision tables that can be evaluated.

Open Forms supports DMN evaluation in its DMN module. Engine-specific details are
implemented in the plugins.

.. contents::
   :local:
   :depth: 2
   :backlinks: none

Python API
==========

Management commands
-------------------

Open Forms provides two management commands for introspection and (local) testing.
Please see the ``--help`` for each command for detailed information.

* ``dmn_list_definitions``: retrieve the available decision definitions and their versions
* ``dmn_evaluate``: evaluate a particular decision table with provided input variables

Module interface
----------------

The public API serves as an abstraction over the various engines.

.. automodule:: openforms.dmn.service
   :members:

Plugin interface
----------------

.. automodule:: openforms.dmn.base
   :members:

Available implementations
=========================

The following plugins are available in Open Forms core.

Camunda DMN
-----------

Configuration is done in the admin via **Configuratie** > **Camunda configuration**.

.. automodule:: openforms.dmn.contrib.camunda
   :members:
