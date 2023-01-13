.. _developers_backend_core_templating:

==========
Templating
==========

Open Forms provides templating solutions for form-designers
(see :ref:`manual_templates`), built on top of the Django Template Language.

Templating functionality is gradually becoming public API for other apps/packages.

Module: :mod:`openforms.template`

Reference
=========

Module functionality
--------------------

.. automodule:: openforms.template
   :members:

.. autoattribute:: openforms.template.sandbox_backend

.. autoattribute:: openforms.template.openforms_backend

Validators
----------

.. automodule:: openforms.template.validators
    :members:
    :exclude-members: deconstruct

Backends
--------

.. autoclass:: openforms.template.backends.sandboxed_django.SandboxedDjangoTemplates
   :members:
