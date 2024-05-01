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

Data model
==========

The following is a simplified relationship diagram of the Django models that relates to forms:

.. mermaid:: _assets/forms-models.mmd

Each :class:`~openforms.forms.models.Form` can have multiple :class:`~openforms.forms.models.FormStep`'s
defined, which acts as a proxy model to a :class:`~openforms.forms.models.FormDefinition`
(as these can be reusable across forms). The :class:`~openforms.forms.models.FormDefinition` model
has a ``configuration`` JSON field, holding the form.io configuration.

The submissions data model mirrors this model in some way:

- A :class:`~openforms.submissions.models.Submission` is tied to a :class:`~openforms.forms.models.Form`.
- A :class:`~openforms.submissions.models.SubmissionStep` is tied to a :class:`~openforms.forms.models.FormStep`.
- A :class:`~openforms.submissions.models.SubmissionValueVariable` is tied to a :class:`~openforms.forms.models.FormVariable`.
