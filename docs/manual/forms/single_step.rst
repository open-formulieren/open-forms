.. _manual_single_step:

================
Single step form
================

Open Forms supports three different types of form since version 4.0 (``regular``, ``appointment``
and ``single step``). The last one can be used when only one step and an anonymous user
are necessary (*consider an embedded contact form as an example*). This type of form can
be configured in the admin page by selecting the ``single step`` type.

This type of form can make use of logic rules but only the following actions are available:

1. Set the registration backend to use for the submission
2. Change the value of a variable/component
3. Evaluate DMN

.. warning::  Logic evaluation for a single step form is performed after submission and
   only in the backend.

The first one is used in the already known way. The other two can only be used in combination
with **user defined variables**.

See :ref:`single step logic <example_single_step_form>` for a detailed form/example.