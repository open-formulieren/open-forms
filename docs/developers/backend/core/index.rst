.. _developers_backend_core_index:

==================
Core: introduction
==================

As stated in the :ref:`developers_architecture`:

    Core functionality is considered functionality that does not or very loosely tie in
    to particular modules. It is functionality that has meaning on its own without
    dependencies, but is enriched by modules.

The core really implements the "engine" of Open Forms and hides all the implementation
details. It should be fairly stable, but also continually allow for new feature
additions, which is a challenging task!

The following Django apps are considered core functionality:

* :mod:`openforms.accounts`: (staff) user account management
* :mod:`openforms.config`: application-wide configuration and defaults
* :mod:`openforms.forms`: designing and building of forms
* :mod:`openforms.formio`: integration with the `form.io`_ frontend library
* :mod:`openforms.submissions`: persisting and handling of submitted form data
* :mod:`openforms.variables`: persisting (intermediate) data into variables for further
  operations

.. _form.io: https://www.form.io/
